import sys
sys.path.append("./ImageBind")
import os
import json
import argparse
from model.avrag import AVRAG
from imagebind.models.imagebind_model import ModalityType

def main(args):

    with open(args.annotations, "r") as f:
        sources = json.load(f)

    rag = AVRAG(model_path = args.model_path, bsz = args.bsz)

    if args.cache:
        video_paths = os.path.join(os.path.dirname(args.video_vocabs), "video_embeddings.pt")
        audio_paths = os.path.join(os.path.dirname(args.audio_vocabs), "audio_embeddings.pt")
    else:
        video_paths = [os.path.join(args.video_vocabs, video) for video in os.listdir(args.video_vocabs) if video.endswith(".mp4")]
        audio_paths = [os.path.join(args.audio_vocabs, audio) for audio in os.listdir(args.audio_vocabs) if audio.endswith(".m4a") or audio.endswith(".wav")]
    
    v_embed = rag.encode(video_paths, ModalityType.VISION, cache = args.cache)
    a_embed = rag.encode(audio_paths, ModalityType.AUDIO, cache = args.cache)

    targets = []
    for source in sources:
        query = source["question"]
        t_embed = rag.encode(query, ModalityType.TEXT)
        res = rag.joint_rag(t_embed, v_embed, a_embed, k = args.topk, alpha_v = args.alpha_v, mode = args.mode)
        res = res[0]
        source["retrieved_file"] = res[query]
        targets.append(source)

    with open(args.output, 'w') as f:
        json.dump(targets, f, indent=2)

if __name__ == "__main__":
    
    args = argparse.ArgumentParser(description="AV-RAG")
    args.add_argument("--model_path", type=str, default="./checkpoints/imagebind_huge.pth", help="Path to the model.")
    args.add_argument("--annotations", type=str, default="./data/test.json", help="Path to the annotations.")
    args.add_argument("--output", type=str, default="./output/test_retrieved.json", help="Path to the output.")
    args.add_argument("--video_vocabs", type=str, default="./data/test/original-videos", help="Path to the video vocab.")
    args.add_argument("--audio_vocabs", type=str, default="./data/test/original-audio", help="Path to the audio vocab.")
    args.add_argument("--bsz", type=int, default=1, help="Batch size.")
    args.add_argument("--cache", action="store_true", help="Use cache.")
    args.add_argument("--mode", type=str, default="0", help="Mode.")
    args.add_argument("--topk", type=int, default=1, help="Number of top results to return.")
    args.add_argument("--alpha_v", type=float, default=0.5, help="The importance of vision compared to audio.")
    args = args.parse_args()

    main(args)