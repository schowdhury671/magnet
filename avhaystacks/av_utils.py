import os
import sys
import cv2
import time
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Union

import torch
import decord
from decord import VideoReader, cpu
from tqdm import tqdm
from transformers import AutoModel, AutoProcessor

# -------------------------------
# Utility conversions
# -------------------------------

def time_to_seconds(t: str) -> int:
    """Convert HH:MM:SS into integer seconds."""
    hh, mm, ss = map(int, t.split(":"))
    return hh * 3600 + mm * 60 + ss


def normalize_time_segment(seg: Union[Tuple[str, str], Dict[str, str]]) -> Tuple[int, int]:
    """Normalize a tuple or dict into (start_sec, end_sec)."""
    if isinstance(seg, tuple):
        s, e = seg
    else:
        s, e = seg["start"], seg["end"]
    return time_to_seconds(s), time_to_seconds(e)


# ============================================================
#            SAMPLING MANAGER (fps / fixed / sfs)
# ============================================================

class SamplingController:
    def __init__(self, clip_model_name: str = "openai/clip-vit-base-patch32"):
        self.sampler = VideoFrameSampler(clip_model_name=clip_model_name)

    def convert_indices_to_segments(
        self,
        phase1_result: str,
        max_duration: int = 60,
        frame_indices: List[int] = None,
        fps: float = None,
        min_side_length: int = 30
    ) -> List[Dict[str, str]]:
        """
        Convert a textual index list (e.g., '[1,2,3]' or '1, 2, 3') into
        a set of time segments. Supports both index-based and frame-based modes.
        """
        # Use frame-index segmentation if possible
        if frame_indices is not None and fps is not None:
            if len(frame_indices) < 2:
                return [{"start": "00:00:00", "end": "00:01:00"}]

            frame_ts = [idx / fps for idx in frame_indices]
            midpoint_list = [(frame_ts[i] + frame_ts[i+1]) / 2 for i in range(len(frame_ts) - 1)]
            midpoint_list = [0] + midpoint_list + [frame_ts[-1] + (frame_ts[-1] - midpoint_list[-1])]

            segments_all = []
            for i in range(len(frame_ts)):
                st = max(0, min(midpoint_list[i], frame_ts[i] - min_side_length))
                et = min(midpoint_list[-1], max(frame_ts[i] + min_side_length, midpoint_list[i + 1]))

                segments_all.append({
                    "start": time.strftime("%H:%M:%S", time.gmtime(st)),
                    "end": time.strftime("%H:%M:%S", time.gmtime(et)),
                    "duration": et - st,
                    "start_seconds": st,
                    "end_seconds": et,
                    "index": i
                })

            # Parse indices from text
            import re
            try:
                cleaned = phase1_result.replace("image", "").replace("Image", "")
                match_list = re.findall(r"\[(.*?)\]", cleaned)
                if match_list:
                    nums = match_list[0]
                else:
                    nums = re.findall(r"\d+(?:\s*,\s*\d+)*", cleaned)[0]

                chosen = sorted([int(x.strip()) - 1 for x in nums.split(",") if x.strip()])
                if not chosen:
                    return [segments_all[0]]
            except:
                return [segments_all[0]]

            # Select segments respecting max duration
            picked, accumulated = [], 0
            for idx in chosen:
                if idx >= len(segments_all):
                    continue
                seg = segments_all[idx]
                if accumulated + seg["duration"] > max_duration * 60:
                    break
                picked.append(seg.copy())
                accumulated += seg["duration"]

            if not picked:
                return [{"start": segments_all[0]["start"], "end": segments_all[0]["end"]}]

            # Merge contiguous segments
            merged = []
            active = picked[0]
            for nxt in picked[1:]:
                if abs(nxt["index"] - active["index"]) == 1:
                    active["end"] = nxt["end"]
                    active["end_seconds"] = nxt["end_seconds"]
                    active["duration"] = active["end_seconds"] - active["start_seconds"]
                    active["index"] = nxt["index"]
                else:
                    merged.append({"start": active["start"], "end": active["end"]})
                    active = nxt

            merged.append({"start": active["start"], "end": active["end"]})
            return merged


    def sample_frames(self, vr, cfg: Dict, time_segments: Optional[List] = None) -> List[int]:
        """
        Dispatch sampler based on strategy: fps / fixed / sfs.
        """
        strategy = cfg.get("sampling_strategy", "fixed")
        print(f"strategy: {strategy}")

        if strategy == "fps":
            return self._sample_fps(vr, cfg["fps_config"], time_segments)
        elif strategy == "fixed":
            return self._sample_fixed(vr, cfg["fixed_config"], time_segments)
        elif strategy == "sfs":
            return self._sample_sfs(vr, cfg["sfs_config"], time_segments)
        else:
            raise ValueError(f"Unknown sampling strategy {strategy}")

    # ----------------------------------------------
    # Actual sampling methods
    # ----------------------------------------------

    def _sample_fps(self, vr, config: Dict, segs: Optional[List]) -> List[int]:
        tgt_fps = config.get("fps", 1.0)

        # If there are no segments, sample entire video
        if not segs:
            return self.sampler.fps_sampling(vr, tgt_fps)

        # Collect frames inside target segments
        all_idxs = []
        native_fps = vr.get_avg_fps()
        for s in segs:
            f1 = int(time_to_seconds(s["start"]) * native_fps)
            f2 = int(time_to_seconds(s["end"]) * native_fps)
            all_idxs.extend(range(f1, f2))

        interval = int(native_fps / tgt_fps)
        samples = all_idxs[::interval]
        print("fps, interval:", tgt_fps, interval)
        return sorted(samples)

    def _sample_fixed(self, vr, config: Dict, segs: Optional[List]) -> List[int]:
        n = config.get("num_frames", 8)

        if not segs:
            return self.sampler.fixed_sampling(vr, n)

        # build a combined list of frames
        frame_list = []
        video_fps = vr.get_avg_fps()
        for s in segs:
            st = int(time_to_seconds(s["start"]) * video_fps)
            et = int(time_to_seconds(s["end"]) * video_fps)
            frame_list.extend(range(st, et))

        if len(frame_list) < n:
            print("len(all_segment_indices) < num_frames:", len(frame_list), n)
            return sorted(frame_list)

        idxs = np.linspace(0, len(frame_list) - 1, n, dtype=int)
        print("num_frames:", n)
        return sorted([frame_list[i] for i in idxs])

    def _sample_sfs(self, vr, config: Dict, segs: Optional[List]) -> List[int]:
        """
        sfs wrapper – segmentation-aware sfs not implemented.
        """
        n = config.get("num_frames")
        kr = config.get("keep_ratio")
        init_n = config.get("initial_frames")
        init_fps = config.get("initial_fps")
        lp = config.get("length_penalty", 0.0)
        lp_exp = config.get("length_penalty_exponent", 1.0)

        print(
            f"num_frames={n}, keep_ratio={kr}, initial_frames={init_n}, "
            f"initial_fps={init_fps}, length_penalty={lp}, exp={lp_exp}"
        )

        if not segs:
            return self.sampler.sfs_sampling(
                vr,
                num_samples=n,
                keep_ratio=kr,
                initial_frames=init_n,
                initial_fps=init_fps,
                length_penalty=lp,
                length_penalty_exponent=lp_exp
            )

        # identical logic as your original
        assert False, "segmented sfs not yet implemented"


# ============================================================
#                    VIDEO FRAME SAMPLER
# ============================================================

class VideoFrameSampler:
    def __init__(
        self,
        clip_model_name: Optional[str] = "openai/clip-vit-base-patch32",
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.device = device
        self.logger = logging.getLogger(__name__)

        if clip_model_name is not None:
            self.model = AutoModel.from_pretrained(
                clip_model_name,
                attn_implementation="flash_attention_2",
                device_map="cuda",
                torch_dtype=torch.float16
            ).eval().to(device)

            if torch.__version__ >= "2.0.0":
                self.model = torch.compile(self.model)

            self.processor = AutoProcessor.from_pretrained(clip_model_name)
            self.model.eval()

    # --------------  image encoding  --------------
    def encode_images(self, imgs, max_batch: int = 64):
        try:
            if not isinstance(imgs, list):
                imgs = [imgs]

            chunks = []
            for i in range(0, len(imgs), max_batch):
                batch = imgs[i:i + max_batch]
                with torch.inference_mode():
                    inp = self.processor(images=batch, return_tensors="pt", padding=True).to(self.model.device)
                    feats = self.model.get_image_features(**inp)
                    chunks.append(feats)

            return torch.cat(chunks, dim=0) if len(chunks) > 1 else chunks[0]

        except Exception as e:
            self.logger.error(f"Encoding failure: {e}")
            raise

    # --------------  helper --------------
    def _get_reader(self, v):
        if isinstance(v, str):
            return VideoReader(v, ctx=cpu(), num_threads=0)
        if isinstance(v, VideoReader):
            return v
        raise ValueError("video_input must be path or VideoReader")

    # ======================================================
    #                       SFS SAMPLING
    # ======================================================

    def sfs_sampling(
        self,
        video,
        num_samples=None,
        keep_ratio=None,
        initial_frames=None,
        initial_fps=None,
        length_penalty=0.0,
        length_penalty_exponent=1.0,
    ):
        try:
            t0 = time.time()
            vr = self._get_reader(video)
            total_frames = len(vr)
            fps = vr.get_avg_fps()

            # Decide initial sampling technique
            if initial_fps is not None:
                steps = round(fps / initial_fps)
                init_idx = np.arange(0, total_frames, steps, dtype=int)
            else:
                if initial_frames is None:
                    initial_frames = min(total_frames, num_samples * 2 if num_samples else int(total_frames * 0.5))
                init_idx = np.linspace(0, total_frames - 1, initial_frames, dtype=int)

            frames_np = vr.get_batch(init_idx).asnumpy()
            print(f"Video load: {time.time() - t0:.2f}s")

            # Decide target count
            if num_samples is None and keep_ratio is None:
                raise ValueError("Need num_samples or keep_ratio")

            if keep_ratio is not None:
                num_samples = max(1, int(len(init_idx) * keep_ratio))
            else:
                num_samples = min(num_samples, len(init_idx))

            # Extract features
            t1 = time.time()
            with torch.inference_mode():
                feats = self.encode_images(frames_np)
                flat = feats.view(len(init_idx), -1)
                norm = torch.nn.functional.normalize(flat, p=2, dim=1).float()
                sim_mat = torch.mm(norm, norm.t()).cpu().numpy()

            print(f"Feature extraction: {time.time() - t1:.2f}s")

            M = np.zeros((len(init_idx) + 1, len(init_idx) + 1))
            M[1:, 1:] = sim_mat

            # Length penalty precompute
            penalties = np.array([
                ((1 / (torch.sin(1.5708 * abs(i - k) / len(init_idx)) + 1) - 1) * length_penalty)
                for i in range(len(init_idx))
                for k in range(len(init_idx))
            ]).reshape(len(init_idx), len(init_idx))

            P = np.zeros_like(M)
            P[1:, 1:] = penalties

            # DP selection
            t2 = time.time()
            dp = np.full((len(init_idx) + 1, num_samples + 1), np.inf)
            trace = np.full((len(init_idx) + 1, num_samples + 1), -1, dtype=int)
            dp[0, 0] = 0.0

            for j in range(1, num_samples + 1):
                for i in range(j, len(init_idx) + 1):
                    temp = dp[j - 1:i, j - 1] + M[j - 1:i, i] + P[j - 1:i, i]
                    best = np.argmin(temp)
                    dp[i, j] = temp[best]
                    trace[i, j] = j - 1 + best

            chosen = []
            idx = len(init_idx)
            while idx > 0 and len(chosen) < num_samples:
                chosen.append(init_idx[idx - 1])
                idx = trace[idx, num_samples - len(chosen) + 1]

            chosen = chosen[::-1]
            print(f"DP time: {time.time() - t2:.2f}s")

            if len(chosen) < num_samples:
                raise ValueError("Insufficient frames selected.")

            torch.cuda.empty_cache()
            return chosen

        except Exception as e:
            self.logger.error(f"sfs_sampling failed: {e}")
            raise

    # ======================================================
    #                FPS SAMPLING
    # ======================================================

    def fps_sampling(self, video, target_fps: float) -> List[int]:
        try:
            vr = self._get_reader(video)
            total = len(vr)
            native_fps = vr.get_avg_fps()

            step = int(native_fps / target_fps)
            if step < 1:
                raise ValueError("target_fps > video_fps")

            return np.arange(0, total, step, dtype=int).tolist()

        except Exception as e:
            self.logger.error(f"fps_sampling error: {e}")
            raise

    # ======================================================
    #                FIXED SAMPLING
    # ======================================================

    def fixed_sampling(self, video, num: int) -> List[int]:
        try:
            vr = self._get_reader(video)
            total = len(vr)
            if num > total:
                raise ValueError(f"Requested {num} > total frames {total}")
            return np.linspace(0, total - 1, num, dtype=int).tolist()
        except Exception as e:
            self.logger.error(f"fixed_sampling error: {e}")
            raise
