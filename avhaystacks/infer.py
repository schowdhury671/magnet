import os
import glob
import math
import json
import argparse
from model.QwenOmni import Qwen2_5OMNI

"""
Please analyze both video and audio content using this two-step process:  
1. Determine if the question is answerable based on the video and audio. If unrelated, respond ONLY with "Unanswerable".  
2. If answerable:  
   - Provide a concise answer using timestamps from the video  
   - Format timestamps as [HH:MM:SS-HH:MM:SS] in brackets  

# Video Context: [Insert key content/themes with timestamps]
User Question: [Insert specific query]
"""

PROMPT = "Please analyze both video and audio content using this two-step process:\n1. Determine if the question is answerable based on the video and audio. If unrelated, respond ONLY with 'Unanswerable'.\n2. If answerable:\n- Provide a concise answer using timestamps from the video\n- Format timestamps as [HH:MM:SS-HH:MM:SS] in brackets\nUser Question: {Question}"

def main(args):
    
    bsz = args.bsz
    model = Qwen2_5OMNI(model_name = args.model_name, prompt = PROMPT)

    with open(args.retrieve_pth, 'r') as f:
        sources = json.load(f)
    
    targets = []
    for source in sources:

        question = source["question"]
        retrieved_files = source["retrieved_file"]
        agent_answers = {}
        
        for retrieved_file in retrieved_files:

            filenames = [os.path.splitext(os.path.basename(filename))[0] for filename in glob.glob(os.path.join(args.video_vocabs, f"{retrieved_file}__*.mp4"))]
            filenames.sort()

            # inputs = [
            #     {
            #         "text": question,
            #         "audio": os.path.join(args.audio_vocabs, f"{filename}.wav"),
            #         "video": os.path.join(args.video_vocabs, f"{filename}.mp4")
            #     }
            #     for filename in filenames
            # ]

            # inputs = model.prepare_input(inputs)
            # text, _ = model.generate(inputs)
            
            # answers = {filaname: t for filaname, t in zip(filenames, text)}
            texts = []
            for i in range(math.ceil(len(filenames) / bsz)):
                
                batch_filenames = filenames[i * bsz:(i + 1) * bsz]
                inputs = [
                    {
                        "text": question,
                        "audio": os.path.join(args.audio_vocabs, f"{filename}.wav"),
                        "video": os.path.join(args.video_vocabs, f"{filename}.mp4")
                    }
                    for filename in batch_filenames
                ]
                inputs = model.prepare_input(inputs)
                text, _ = model.generate(inputs)
                texts.extend(text)
                
            answers = {filaname: t for filaname, t in zip(filenames, texts)}
            agent_answers[retrieved_file] = answers

        source["agent_answers"] = agent_answers
        targets.append(source)
    
    with open(args.output, 'w') as f:
        json.dump(targets, f, indent=2)



if __name__ == "__main__":
    
    args = argparse.ArgumentParser()
    args.add_argument("--model_name", type=str, default="Qwen/Qwen2.5-Omni-7B")
    args.add_argument("--retrieve_pth",type=str, default="./output/test_retrieved.json")
    args.add_argument("--video_vocabs", type=str, default="./data/test/original-videos")
    args.add_argument("--audio_vocabs", type=str, default="./data/test/original-audio")
    args.add_argument("--output", type=str, default="./output/test_response.json")
    args.add_argument("--bsz", type=int, default=4)
    args = args.parse_args()

    main(args)