# import sys
# sys.path.append("/ibex/user/feij0a/phd_project/av-haystack/ImageBind")
import os
import math
import torch
import argparse
from imagebind import data
from imagebind.models import imagebind_model
from imagebind.models.imagebind_model import ModalityType
# from ImageBind.imagebind import data
# from ImageBind.imagebind.models import imagebind_model
# from ImageBind.imagebind.models.imagebind_model import ModalityType


class AVRAG:
    
    def __init__(self, model_path = None, bsz = 128):
        
        self.bsz = bsz
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"

        # Instantiate model
        if model_path:
            self.model = imagebind_model.imagebind_huge(pretrained = False)
            self.model.load_state_dict(torch.load(model_path))
        else: # download pretrained model automatically
            self.model = imagebind_model.imagebind_huge(pretrained = True)
        self.model.eval()
        self.model.to(self.device)

        self.load_and_transform_func = {
            ModalityType.TEXT: data.load_and_transform_text,
            ModalityType.AUDIO: data.load_and_transform_audio_data,
            ModalityType.VISION: [data.load_and_transform_vision_data, data.load_and_transform_video_data]
        }

    @torch.no_grad()
    def encode(self, input_paths, data_type, cache = False) -> dict:
        """
        Args:
            input_paths (str or list): Paths to the input data.
            cache (bool): If True, loads the embeddings from a cache file.
        Returns:
            Dict: {
                filename: list,
                embeddings: torch.Tensor,
            }
        """

        if cache:
            assert input_paths.endswith(".pt"), "Cache file must be a pt file, but got {}".format(input_paths)
            embeddings = torch.load(input_paths)
            return embeddings
        
        if type(input_paths) == str:
            if os.path.isdir(input_paths):
                input_paths = [os.path.join(input_paths, f) for f in os.listdir(input_paths)]
            else:
                input_paths = [input_paths]

        embeddings = None
        epochs = len(input_paths) // self.bsz - 1 if len(input_paths) % self.bsz == 0 else len(input_paths) // self.bsz

        for i in range(epochs + 1):
            start = i * self.bsz
            end = (i + 1) * self.bsz
            input_batch = input_paths[start:end]

            if data_type == ModalityType.VISION:
                indice = 1 if input_paths[0].endswith(".mp4") else 0
                inputs = {
                    data_type: self.load_and_transform_func[data_type][indice](input_batch, self.device),
                }
            else:
                inputs = {
                    data_type: self.load_and_transform_func[data_type](input_batch, self.device),
                }
            
            embedding_batch = self.model(inputs)[data_type].cpu()

            if embeddings is None:
                embeddings = embedding_batch
            else:
                embeddings = torch.cat((embeddings, embedding_batch), dim = 0)

        if data_type != ModalityType.TEXT:
            filenames = ['.'.join(os.path.basename(path).split('.')[:-1]) for path in input_paths]
        else:
            filenames = input_paths
            
        embeddings = {
            "filename": filenames,
            "embeddings": embeddings,
        }
        if data_type == ModalityType.VISION:
            data_type = "video" if indice == 1 else "image"

        if data_type != ModalityType.TEXT:
            torch.save(embeddings, os.path.join(os.path.dirname(os.path.dirname(input_paths[0])), f"{data_type}_embeddings.pt"))

        return embeddings
    
    def topk(self, queries, vocabs, k = 1):
        """
        Args:
            queries (torch.Tensor, (n, d)): Query embeddings.
            vocabs (torch.Tensor, (m, d)): Vocabulary embeddings.
            k (int): Number of top results to return.
        Returns:
            List (n, k): Top k results.
        """
        scores = torch.softmax(queries @ vocabs.T, dim = -1)
        topk_indices = torch.topk(scores, k = k, dim = -1).indices

        return topk_indices

    
    def pair_rag(self, query = None, vocab = None, k = 1):

        topk_indices = self.topk(query["embeddings"], vocab["embeddings"], k = k)
        topk_files = []
        for indice, topi_indices in enumerate(topk_indices):
            topk_files.append(
                {
                    query["filename"][indice]: [vocab["filename"][i] for i in topi_indices]
                }
            )

        return topk_files
    
    def joint_rag(self, query = None, vocab_vision = None, vocab_audio = None, k = 1, alpha_v = 0.5, mode = '0'):
        """
        Args:
            mode (str):
            0 -> text as query, return topk filename via joint embedding
            1 -> text as query, return both topk vision and topk audios
        """
        if mode == '0':

            embeddings = alpha_v * vocab_vision["embeddings"] + (1 - alpha_v) * vocab_audio["embeddings"]
            topk_indices = self.topk(query["embeddings"], embeddings, k = k)
            topk_files = []
            for indice, topi_indices in enumerate(topk_indices):
                topk_files.append(
                    {
                        query["filename"][indice]: [vocab_vision["filename"][i] for i in topi_indices]
                    }
                )
            
        elif mode == '1':
            topk_indices_vision = self.topk(query["embeddings"], vocab_vision["embeddings"], k = k)
            topk_indices_audio = self.topk(query["embeddings"], vocab_audio["embeddings"], k = k)
            topk_files = []
            for indice, (topi_indices_vision, topi_indices_audio) in enumerate(zip(topk_indices_vision, topk_indices_audio)):
            
                # topk_files.append(
                #     {
                #         query["filename"][indice]: ([vocab_vision["filename"][i] for i in topi_indices_vision], [vocab_audio["filename"][i] for i in topi_indices_audio])
                #     }
                # )
                topk_files.append(
                    {
                        query["filename"][indice]: list(set([vocab_vision["filename"][i] for i in topi_indices_vision] + [vocab_audio["filename"][i] for i in topi_indices_audio]))
                    }
                )

        else:
            raise NotImplementedError("Only mode 0 is implemented.")
        
        return topk_files

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="AV-RAG")
    parser.add_argument("--model_path", type=str, default="./checkpoints/imagebind_huge.pth", help="Path to the model.")
    parser.add_argument("--bsz", type=int, default=128, help="Batch size.")
    parser.add_argument("--cache", action="store_true", help="Use cache.")
    parser.add_argument("--mode", type=str, default="0", help="Mode.")
    parser.add_argument("--topk", type=int, default=1, help="Number of top results to return.")
    parser.add_argument("--alpha_v", type=float, default=0.5, help="The importance of vision compared to audio.")
    args = parser.parse_args()

    rag = AVRAG(model_path = args.model_path, bsz = args.bsz)

    text_list=["A dog", "A car", "A bird"]

    image_paths=["./assets/test/images/dog.jpg", "./assets/test/images/car.jpg", "./assets/test/images/bird.jpg"]
    video_paths=["./assets/test/videos/dog.mp4", "./assets/test/videos/car.mp4", "./assets/test/videos/bird.mp4"]
    audio_paths=["./assets/test/audios/dog.wav", "./assets/test/audios/car.wav", "./assets/test/audios/bird.wav"]
    if args.cache:
        image_paths = "./assets/image_embeddings.pt"
        video_paths = "./assets/video_embeddings.pt"
        audio_paths = "./assets/audio_embeddings.pt"
    
    
    t_embed = rag.encode(text_list, ModalityType.TEXT)
    v_embed = rag.encode(video_paths, ModalityType.VISION, cache = args.cache)
    a_embed = rag.encode(audio_paths, ModalityType.AUDIO, cache = args.cache)
    
    v_res = rag.pair_rag(t_embed, v_embed, k = args.topk)
    a_res = rag.pair_rag(t_embed, a_embed, k = args.topk)
    j_res = rag.joint_rag(t_embed, v_embed, a_embed, k = args.topk, alpha_v = args.alpha_v, mode = args.mode)

    print("=========================Text-Vision RAG============================")
    print(v_res)
    print("\n=========================Text-Audio RAG============================")
    print(a_res)
    print("\n==================Text-(Audio, Vision) joint RAG=====================")
    print(j_res)
    
    