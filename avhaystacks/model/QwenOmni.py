# code base: https://github.com/QwenLM/Qwen2.5-Omni
import json
import torch
from .base import BaseModel
from qwen_omni_utils import process_mm_info
from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor

MODALITIES = {"text", "image", "video", "audio"}

class Qwen2_5OMNI(BaseModel):
    
    def __init__(self, model_name = "Qwen/Qwen2.5-Omni-7B", prompt = None, enable_flashattn = True, use_audio_in_video = True, return_audio = False):
        
        self.prompt = prompt
        self.return_audio = return_audio
        self.use_audio_in_video = use_audio_in_video

        self.processor = Qwen2_5OmniProcessor.from_pretrained(model_name)
        if enable_flashattn:
            self.model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype="auto",
                device_map="auto",
                attn_implementation="flash_attention_2",
            )
        else:
            self.model = Qwen2_5OmniForConditionalGeneration.from_pretrained(model_name, torch_dtype="auto", device_map="auto")
        self.model.eval()

        self.device = self.model.device
        self.dtype = self.model.dtype

    def prepare_input(self, inputs):
        """
        Args:
            inputs: list of dict
                [
                    {
                        image: str
                        video: str
                        audio: str
                        text: str
                    }
                ]
        """

        conversation = []
        for input in inputs:
            conversation.append([
                {
                    "role": "system",
                    "content": "You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, capable of perceiving auditory and visual inputs, as well as generating text and speech.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": key, key: self.prompt.format(Question=value) if key == "text" and self.prompt is not None else value}
                        for key, value in input.items() if key in MODALITIES
                    ],
                }
            ])

        if len(conversation) == 1:
            conversation = conversation[0]

        text = self.processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
        audios, images, videos = process_mm_info(conversation, use_audio_in_video=self.use_audio_in_video)
        inputs = self.processor(text=text, audio=audios, images=images, videos=videos, return_tensors="pt", padding=True, use_audio_in_video=self.use_audio_in_video)
        inputs = inputs.to(self.device).to(self.dtype)

        return inputs

    @torch.no_grad()
    def generate(self, inputs):
        
        if self.return_audio:
            text_ids, audio = self.model.generate(**inputs, use_audio_in_video=self.use_audio_in_video)
            text = self.processor.batch_decode(text_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            audio = audio.reshape(-1).detach().cpu().numpy() # need to change
        else:
            text_ids = self.model.generate(**inputs, use_audio_in_video=self.use_audio_in_video, return_audio=False)
            text = self.processor.batch_decode(text_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            audio = None
        text = [t.split("assistant")[-1].strip() for t in text]
        return text, audio
    
if __name__ == "__main__":
    
    # prompt = "Localize the start and end timestamp for event to answer the question '{Question}' in the video, and answer the question with sentences."
    # prompt = "Give the query: '{Question}', when does the described content occur in the video?"
    prompt = None

    with open('data/Cooking-tutorials.json', 'r') as f:
        sources = json.load(f)
    
    source = sources[0]
    question = source["question"]
    answer = source["answer"]
    timestamps = source["timestamps"]
    
    inputs = []
    for timestamp in timestamps:
        filename = timestamp.replace(".txt", '')
        inputs.append({
            "text": question,
            "audio": f"data/Cooking-tutorials/original-audio/{filename}.m4a",
            "video": f"data/Cooking-tutorials/original-videos/{filename}.mp4",
        })
        break
    model = Qwen2_5OMNI(model_name="Qwen/Qwen2.5-Omni-7B", prompt=prompt)
    inputs = model.prepare_input(inputs)
    text, audio = model.generate(inputs)

    print(text)