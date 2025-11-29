python infer.py --model_name /ibex/tmp/c2090/junjie/ckpts/Qwen/Qwen2.5-Omni-7B \
                --retrieve_pth ./output/Cooking-tutorials_retrieved_use_gt_video.json \
                --video_vocabs  ./data/Cooking-tutorials/segment-video/ \
                --audio_vocabs  ./data/Cooking-tutorials/segment-audio/ \
                --output ./output/Cooking-tutorials_response.json \