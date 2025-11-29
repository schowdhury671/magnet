import os
import openai

# IMPORTANT NOTE: This folder depends on this folder "processed-subtitles" which has to be within the same directory
effort = "low"

api_key = os.environ.get("OPENAI_API_KEY")
client = openai.OpenAI(api_key = api_key)

# Define file and directory names
input_instructions_file = "input_instructions_segmentation.txt"

try:
    with open(input_instructions_file, "r", encoding="utf-8") as input_file:
        instructions_segmentation = input_file.read()
except FileNotFoundError:
    raise FileNotFoundError(f"The input file '{input_instructions_file}' was not found. Please make sure it exists.")

files = [
        "0.txt",
        "1.txt",
        "2.txt",
        "3.txt",
        "4.txt",
        "5.txt",
        "6.txt",
        "7.txt",
        "8.txt",
        "9.txt",
        "10.txt",
        "11.txt",
        "12.txt",
        "13.txt",
        "14.txt",
        "15.txt",
        "16.txt",
        "17.txt",
        "18.txt",
        "19.txt"
         ]

input_directory = "processed-subtitles"
for filename in files:
    # Read transcript from input file
    input_file_path = os.path.join(input_directory, filename)
    print("input_file_path")
    print(input_file_path)
    try:
        with open(input_file_path, "r", encoding="utf-8") as input_file:
            input_transcript = input_file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"The input file '{filename}' was not found. Please make sure it exists.")

    completion = client.chat.completions.create(
        model="o3-mini",
        reasoning_effort = effort,
        messages=[
            {
                "role": "developer",
                "content": instructions_segmentation
            },
            {
                "role": "user",
                "content": input_transcript
            }
        ]
    )
    
    output_directory = "segmented-subtitles"
    
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print(f"Created output directory: {output_directory}")
    
    output_file_path = os.path.join(output_directory, filename)

    with open(output_file_path, "w", encoding="utf-8") as output_file:
        output_file.write(completion.choices[0].message.content)
    print("Output saved to {output_file_path}")
    print(completion.choices[0].message.content)
