import os
import openai

effort = "low"

api_key = os.environ.get("OPENAI_API_KEY")
client = openai.OpenAI(api_key = api_key)

# Define file and directory names
input_instructions_file = "instructions-without-transcripts.txt"

try:
    with open(input_instructions_file, "r", encoding="utf-8") as input_file:
        instructions_questions_exceptions = input_file.read()
except FileNotFoundError:
    raise FileNotFoundError(f"The input file '{input_instructions_file}' was not found. Please make sure it exists.")

# Build the messages list: instructions + individual file messages + questions message
messages = [
    {"role": "developer", "content": instructions_questions_exceptions}
]

completion = client.chat.completions.create(
    model="o3-mini",
    reasoning_effort=effort,
    messages=messages
)

output_directory = "questions"
# Create the output directory if it doesn't exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)
    print(f"Created output directory: {output_directory}")

output_file_path = os.path.join(output_directory, "input_questions2.txt")

with open(output_file_path, "w", encoding="utf-8") as output_file:
    output_file.write(completion.choices[0].message.content)
print("Output saved to {output_file_path}")
print(completion.choices[0].message.content)
