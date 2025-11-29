To run the av-rag part code, download ImageBind and install dependencies.
```
conda create --name av-rag python=3.10 -y
conda activate av-rag

git clone git@github.com:facebookresearch/ImageBind.git
cd ImageBind
pip install .
pip install --upgrade numpy==1.26.4  # ImageBind is based on Numpy 1.x
```

Download the checkpoints
```
mkdir checkpoints
cd checkpoints
wget https://dl.fbaipublicfiles.com/imagebind/imagebind_huge.pth
```

Firstly, You need  to run `sh scripts/coding_conv.sh` as the coding in the collected video and '.m4a' are not supported in ImageBind.

Run `sh scripts/clipping.sh` to clip the video and audio into chunks, the default length for each clip is 60s.

Run the following command to get the rag results
```
sh scripts/avrag.sh
``` 

The `--annotation` should be format as follow (see example `./data/test.json`):
```
[{
    "id": "1",
    "question": "A barking dog",
    "answer": "filename: 2",
    "timestamps": {
        "2.txt": [
        0,
        17
        ]
    }
    },
    {
    "id": "2",
    "question": "A car",
    "answer": "filename: 1",
    "timestamps": {
        "1.txt": [
        0,
        12
        ]
    }
    }
]
``` 
I write a `data_convert.py` script to convert the xlsx (collected data) to such format. Be careful that this excel has some inconsistent about the defination of `Metadata` and `Answers`. You need to change the key if necessary.

The `--video_vocabs` and `--audio_vocabs` specify the root path of video and audio can be retrieved (Note: the video and audio should correspond one to one and share the same filename (in addition to the suffix)). Change `--topk` to return the top k retrieved filenames (without suffix).

To run the av-qa part code, You need to create a new environment as the dependencies of ImageBind and Qwen2.5-Omni are conflicts. Install the dependencies based on the instruction of Qwen2.5-Omni offcial repo.

Specify the retrieved file path obtain in av-rag and run the following repo to get the results of avqa.
```
sh scripts/infer.sh
```
The query here is the question in retrieved file. Change `PROMPT` in line 6 of `infer.py` to add prompt for the question. The prompt should be like:
```
prompt = "Give the query: '{Question}', when does the described content occur in the video?"
```
