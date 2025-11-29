python rag.py --model_path ./checkpoints/imagebind_huge.pth \
              --annotations ./data/Cooking-tutorials.json \
              --output ./output/Cooking-tutorials_retrieved.json \
              --video_vocabs  ./data/Cooking-tutorials/process-video/ \
              --audio_vocabs  ./data/Cooking-tutorials/process-audio/ \
              --topk 1 \
