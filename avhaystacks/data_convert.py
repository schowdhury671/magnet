import re
import os
import json
import argparse
import pandas as pd

def parse_timestamps(timestamps):

    pattern = r'(\d+\.txt) \((\d{4})s–(\d{4})s\)'
    matches = re.findall(pattern, timestamps)
    result = {filename: [int(start), int(end)] for filename, start, end in matches}
    
    return result

def main(args):

    files = pd.ExcelFile(args.file)
    sub_file = files.parse(args.sheet)
    
    targets = []
    for indices, row in sub_file.iterrows():

        if pd.isna(row["Questions Serial"]):
            continue
        
        id = str(int(row["Questions Serial"]))
        question = row["Questions"]
        # answer = row["Metadata"]
        # timestamps = parse_timestamps(row["Answers"])
        answer = row["Answers"]
        timestamps = parse_timestamps(row["Metadata"])

        targets.append({
            "id": id,
            "question": question,
            "answer": answer,
            "timestamps": timestamps
        })
    
    with open(args.output, 'w') as f:
        json.dump(targets, f, indent = 2)

if __name__ == "__main__":

    args = argparse.ArgumentParser()
    args.add_argument("--file", type=str, default="./data/sources.xlsx")
    args.add_argument("--sheet", type=str, default="Cooking tutorials")
    args.add_argument("--output", type=str, default="./data/Cooking-tutorials.json")
    args = args.parse_args()

    main(args)