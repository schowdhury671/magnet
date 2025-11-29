python rag.py --model_path ./checkpoints/imagebind_huge.pth \
              --annotations ./data/test.json \
              --output ./output/test_retrieved.json \
              --video_vocabs  ./data/test/original-videos \
              --audio_vocabs  ./data/test/original-audio \
              --topk 1 \

python infer.py --model_name ./checkpoints/Qwen2.5-Omni-7B \
                --retrieve_pth ./output/test_retrieved.json \
                --output ./output/test_response.json \