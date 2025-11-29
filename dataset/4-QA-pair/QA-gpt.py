import os
import openai

# IMPORTANT NOTE: this file depends on this folder segmented-subtitles
effort = "low"

api_key = os.environ.get("OPENAI_API_KEY")
client = openai.OpenAI(api_key = api_key)

# Define file and directory names
input_instructions_file = "input_QA_gen_instructions.txt"

try:
    with open(input_instructions_file, "r", encoding="utf-8") as input_file:
        instructions_QA = input_file.read()
except FileNotFoundError:
    raise FileNotFoundError(f"The input file '{input_instructions_file}' was not found. Please make sure it exists.")

input_questions_file = "input_questions.txt"
try:
    with open(input_questions_file, "r", encoding="utf-8") as input_file:
        user_QA= input_file.read()
except FileNotFoundError:
    raise FileNotFoundError(f"The input file '{input_questions_file}' was not found. Please make sure it exists.")


files = [
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19"
        ]

input_directory = "segmented-subtitles"
file_messages = []

# Read file contents and create a text message for each file
for file_id in files:
    file_name = file_id + '.txt'
    input_file_path = os.path.join(input_directory, file_name)
    print(f"Reading file: {input_file_path}")
    try:
        with open(input_file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"The input file '{input_file_path}' was not found. Please make sure it exists.")
    file_messages.append({
        "type": "text",
        "text": f"--- Content from file {file_name} ---\n{file_content}"
    })

# Build the messages list: instructions + individual file messages + questions message
messages = [
    {"role": "developer", "content": instructions_QA}
]
# Extend messages with each file's text message
for msg in file_messages:
    messages.append({"role": "user", "content": msg["text"]})

# Finally, add the questions message
messages.append({"role": "user", "content": user_QA})


completion = client.chat.completions.create(
    model="o3-mini",
    reasoning_effort=effort,
    messages=messages
)

output_directory = "QA-generated"

# Create the output directory if it doesn't exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)
    print(f"Created output directory: {output_directory}")

output_file_path = os.path.join(output_directory, "questions-answers-pair.txt")

with open(output_file_path, "w", encoding="utf-8") as output_file:
    output_file.write(completion.choices[0].message.content)
print("Output saved to {output_file_path}")
print(completion.choices[0].message.content)
