## Data Creation Pipeline
### 1) Config setup
Modify the `params.sh` file to include video IDs from youtube and include the number of videos to be downloaded using MAX_NUM, 19 here means 20 as it starts from zero!
```
#links=("Video-ID1" "VIDEO-ID2" ...etc)
#TOPIC_NAME="travel-egypt"
#MAX_NUM=19
```
```
cd dataset-creation-pipeline/1-download-subtitles-audio-video
vim params.sh
# modify params.sh according to above instructions
```
### 2) Download transcripts
This part depends on setting up `params.sh`
Use download-subtitles script to download the transcripts
```
source download-subtitles-1.sh
```
Now, `original-subtitles` directory will be created with transcripts from 0.txt to 19.txt

### 3) Processing the subtitles for zero-shot successful GPT understanding
- a) There were mismatches in the seconds
- b) Merge text together for similar starting or ending timestamps
- c) Merge text together if there is >= 2 seconds difference between the shared timestep
- d) If difference between starting & ending is 1 second, make first one less by 1 second
- e) Merge with the prior if there is only one word and the time difference is one second
- f) Merge with the next block if there is only one word and the time difference is one second

This part depends on setting up `params.sh` & `download-subtitles`
Use subtitles-processing-2 script to convert the transcripts based on the following
```
source subtitles-processing-2.sh
```
Results in `processed-subtitles` directory generated

### 4) Download Audio
This part depends on setting up `params.sh`
```
source download-audios.sh
```
Results in `original-audio` directory generated

### 5) Download Video
This part depends on setting up `params.sh`
```
source download-videos.sh
```
Results in `original-videos` directory generated

### 6) Transcripts Segmentation
In order to be able to create a meaningful question answer pair, we tasked GPT to segment the transcripts into sub-topics and segment them together

This depends on `input_instructions_segmentation.txt` & `processed-subtitles`
```
cd 2-subtitles-segmentation
cp ../1-download-subtitles-audio-video/processed-subtitles . -r
python3 segmentation-gpt.py
```

`input_instructions_segmentation.txt`:
```
Using the full video transcript as input with timestamps in seconds, automatically segment the video into distinct sections based on topic changes and instructional content. For each segment, follow these steps:

1. Segment Identification:
        - Detect natural breaks in the transcript that indicate a change in topic, exercise, or technique.
        - Assign appropriate start and end times in the seconds-only format. Do not convert into minute:seconds.
        - If a segment is overly long or covers multiple topics, subdivide it into smaller, more manageable segments.

2. Topic and Title Assignment:
        - Determine a concise topic and title for each segment that accurately reflects the core content or exercise discussed.
3. Enhanced Instructional Details:
        - Create a 'Details' sub-section enriched with technical, procedural, and descriptive information extracted directly from the transcript.
        - Include all relevant details about the content covered, such as specific techniques, step-by-step procedures, key motions, and critical nuances.
        - If related audio sound follows the text for that segment, integrate a description of it (e.g., background music cues, sound effects, or any other auditory elements) to further contextualize the instructional material.

4. Content Filtering:
        - Remove any content not directly related to the instructional material, including:
        - Mentions of the presenter’s name or personal commentary.
        - Introduction segments (greetings or general overviews).
        - Advertisement segments or any promotional content.
        - The final summary or closing remarks.
The output should present each segment in the following format:
Segment [Segment Number]
Time: [Start Seconds] --> [End Seconds]
Title: [Concise Title]
Details:
   - Instructional Focus: [Brief description of the instructional focus]
   - Key Steps and details:
      - [Step / Detail 1]
      - [Step / Detail 2]
      - [Step / Detail 3]
      - [Step / Detail 4]
      - [Step / Detail 5]
   - Audio Cues: [Description of any audio elements, or ""None beyond the spoken instruction.""]

Each segment must use the original seconds-only timestamp format, and the 'Details' sub-section should focus solely on the instructional content derived directly from the transcript.
```
### 7) Questions generation without seeing transcripts
To generate meaningful questions without having the GPT look at the transcripts

```
cd 3-questions-generation
python3 questions-generation-without-transcripts.py
```
This depends on `instructions-without-transcripts.txt`
```
I am collecting data about how to <TOPIC>
- What are different 50 questions that must be answer by a video and cant be answered by text.
- Questions that can not be answered by google search and require to watch a multiple videos to reach the best steps and answers.
- Questions rely on auditory or physical cues, things that can be observed, but without using common terms related to seeing or hearing.
- Questions should not include keywords like video, images, visually, presenter, or instructor.
- Avoid directly referencing the media content itself.
```
### 8) Questions generation while looking at the transcripts
To generate meaningful questions by looking at the transcripts
```
cd 3-questions-generation
cp ../2-subtitles-segmentation/segmented-subtitles . -r
python3 questions-generation-with-transcripts.py
```
This depends on `segmented-subtitles` & `instructions-with-transcripts.txt`

`instructions-with-transcripts.txt`:
```
You are tasked with generation of questions based on attached files.
Go over each file one by one and create a question for each Instructional Focus.

Example:
You will find an Instructional Focus: Teach the standard phrases for saying goodbye in Chinese.
A question for this instructional focus would be how to say goodbye in chinese?

mention the file name, followed by the segment number followed by the instruction focus point followed by the questions and then the next segment and so on.
let's start with file 0 then 1, then 2 ...etc till 19.
```
### 9) Question-Answer pair generation
To generate the QA-pair, there is a dependency on `segmented-subtitles` & `input_QA_gen_instructions.txt` & `input_questions.txt`

```
cd 4-QA-pair
cp ../3-questions-generation/questions.txt input_questions.txt
cp ../2-subtitles-segmentation/segmented-subtitles . -r
source QA-gpt.py
```

`input_questions.txt`:
```
Question 1
Question 2
etc...
```

`input_QA_gen_instructions.txt`:
```
You are provided with multiple video transcripts and a separate list of unanswered questions.
Your task is to generate precise, instructional, and comprehensive answers for each question by meticulously extracting and synthesizing information solely from the provided transcripts.

Follow these guidelines:

1. Answer Requirements:
        - Specific and Instructional: Provide clear, step-by-step instructions exactly as described in the transcripts. Detail every step necessary, making no assumptions and avoiding generalizations.
        - Transcript-Based Only: Use only the information found in the transcripts. Do not incorporate any external or general knowledge.
        - Comprehensive Coverage: Analyze every transcript segment. Include every detail from the transcripts that pertains to the question. Do not omit any relevant piece of information.
        - Unified Integration: Merge overlapping or complementary information into one coherent, highly detailed, and unified answer..
        - Elaborative Detail: Expand on the basic instructions with additional context and clarifications directly from the transcripts. Provide enriched details to enhance clarity.
        - Step-by-Step Reasoning: Present the answer in a sequential, logical order with numbered or clearly defined steps.
        - Numbered steps.
2. Referencing Format:
   - Complete References: List all transcript segments used to derive the answer. Even if multiple segments come from the same file, each relevant segment must be referenced.
   - Single Bracketed Section: List all references at the end of the answer within one set of brackets.
   - Reference Format:
        At end of the answer, write the references from all files (file number.txt (start_time s–end_time s), file number.txt (start_time s–end_time s), file number.txt (start_time s–end_time s))

3. Final Checks:
        - Transcript Exclusivity: Confirm that the answer is derived exclusively from the provided transcripts.
        - Full Reference Inclusion
        - Unified Integration: Seamlessly integrate all pieces of transcript evidence into a detailed, and instructional response.
        - Analysis: Reflect deep analysis and synthesis of every detail provided in the transcripts.

4. Final output format:
        Each question, answer and references are in one line separated by separator ###
        Question: Question 1?### 1) step 1 2) step 3) step 3 4) step 4 5) step 5###All References: (1.txt (0017s–0074s), 8.txt (0045s–0270s), 2.txt (0050s–0100s), 3.txt (0110s–0110s))
```
