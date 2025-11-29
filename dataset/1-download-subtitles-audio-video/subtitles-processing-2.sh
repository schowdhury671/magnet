#!/bin/bash
source params.sh
DEBUG=0

ORIGINAL_FOLDER="original-subtitles"
FOLDER="processed-subtitles"
mkdir $FOLDER -p

for FILE_NUM in $(seq 0 $MAX_NUM); do
  echo "Processing file number $FILE_NUM"

  # Step 1: Convert time to seconds only
  STEP="step1"
  INPUT_FILE="$ORIGINAL_FOLDER/$TOPIC_NAME-$FILE_NUM.txt"
  MID_OUTPUT_FILE="$FOLDER/$TOPIC_NAME-$FILE_NUM-seconds-$STEP.txt"

  # Skip if the input file doesn't exist.
  if [ ! -f "$INPUT_FILE" ]; then
    echo "File $INPUT_FILE not found. Skipping..."
    continue
  fi

  # HH:MM:SS --> HH:MM:SS
  regex='^[0-9]{2}:([0-9]{2}):([0-9]{2}) --> [0-9]{2}:([0-9]{2}):([0-9]{2})$'
  
  while IFS= read -r line; do
    if [[ "$line" =~ $regex ]]; then
      start_min="${BASH_REMATCH[1]}"
      start_sec="${BASH_REMATCH[2]}"
      end_min="${BASH_REMATCH[3]}"
      end_sec="${BASH_REMATCH[4]}"
      
      # Conversion.
      start_total=$((10#$start_min * 60 + 10#$start_sec))
      end_total=$((10#$end_min * 60 + 10#$end_sec))
      
      # Write the conversion.
      printf "%04d --> %04d\n" "$start_total" "$end_total"
    else
      # Write lines without timestamp.
      echo "$line"
    fi
  done < "$INPUT_FILE" > "$MID_OUTPUT_FILE"
  
  
  # Step 2: Merge text together for similar starting or ending timestamps
  MID_INPUT_FILE="$FOLDER/$TOPIC_NAME-$FILE_NUM-seconds-$STEP.txt"
  STEP="step2"
  MID_OUTPUT_FILE="$FOLDER/$TOPIC_NAME-$FILE_NUM-seconds-$STEP.txt"
  
  awk '
    function min(a, b) { return (a+0 < b+0 ? a : b) }
    function max(a, b) { return (a+0 > b+0 ? a : b) }
    BEGIN { block = 0 }
    /-->/ {
        split($0, parts, /-->/)
        start = parts[1]
        end = parts[2]
        gsub(/^[ \t]+|[ \t]+$/, "", start)
        gsub(/^[ \t]+|[ \t]+$/, "", end)
        text = ""
        if (getline nextline > 0) {
            if (index(nextline, "-->") == 0) {
                text = nextline
                gsub(/^[ \t]+|[ \t]+$/, "", text)
            }
        }
        if (block == 0) {
            curr_start = start
            curr_end   = end
            curr_text  = text
            block = 1
        } else {
            if (curr_start == start || curr_end == end) {
                curr_start = min(curr_start, start)
                curr_end   = max(curr_end, end)
                if (curr_text != "" && text != "")
                    curr_text = curr_text " " text
                else
                    curr_text = curr_text text
            } else {
                print curr_start " --> " curr_end
                print curr_text
                curr_start = start
                curr_end   = end
                curr_text  = text
            }
        }
    }
    END {
        if (block == 1) {
            print curr_start " --> " curr_end
            print curr_text
        }
    }
  ' "$MID_INPUT_FILE" > "$MID_OUTPUT_FILE"
  
  # Step 3: Merge text together if there is >= 2 seconds difference between the shared timestep
  MID_INPUT_FILE="$FOLDER/$TOPIC_NAME-$FILE_NUM-seconds-$STEP.txt"
  STEP="step3"
  MID_OUTPUT_FILE="$FOLDER/$TOPIC_NAME-$FILE_NUM-seconds-$STEP.txt"
  
  awk '
    function trim(s) {
        gsub(/^[ \t]+|[ \t]+$/, "", s)
        return s
    }
    BEGIN { block = 0 }
    /-->/ {
        split($0, parts, /-->/)
        start_str = trim(parts[1])
        end_str   = trim(parts[2])
        start_num = start_str + 0
        end_num   = end_str + 0
        text_line = ""
        if (getline nextline > 0) {
            if (index(nextline, "-->") == 0) {
                text_line = trim(nextline)
            }
        }
        if (block == 0) {
            curr_start_num = start_num
            curr_end_num   = end_num
            curr_start_str = start_str
            curr_end_str   = end_str
            curr_text      = text_line
            block = 1
        } else {
            if (curr_end_num - start_num > 1) {
                curr_end_num = end_num
                curr_end_str = end_str
                if (curr_text != "" && text_line != "")
                    curr_text = curr_text " " text_line
                else
                    curr_text = curr_text text_line
            } else {
                print curr_start_str " --> " curr_end_str
                print curr_text
                curr_start_num = start_num
                curr_end_num   = end_num
                curr_start_str = start_str
                curr_end_str   = end_str
                curr_text      = text_line
            }
        }
    }
    END {
        if (block == 1) {
            print curr_start_str " --> " curr_end_str
            print curr_text
        }
    }
  ' "$MID_INPUT_FILE" > "$MID_OUTPUT_FILE"
  
  # Step 4: If difference between starting & ending is 1 second, make first one less by 1 second
  MID_INPUT_FILE="$FOLDER/$TOPIC_NAME-$FILE_NUM-seconds-$STEP.txt"
  STEP="step4"
  MID_OUTPUT_FILE="$FOLDER/$TOPIC_NAME-$FILE_NUM-seconds-$STEP.txt"
  
  awk '
    function pad(num, width) { return sprintf("%0*d", width, num) }
    /-->/ {
      block++
      split($0, parts, /-->/)
      start = parts[1]
      end   = parts[2]
      gsub(/^[ \t]+|[ \t]+$/, "", start)
      gsub(/^[ \t]+|[ \t]+$/, "", end)
      block_start[block] = start
      block_end[block]   = end
      pad_width = length(start)
      block_pad[block]   = pad_width
      getline text_line
      block_text[block] = text_line
    }
    END {
      for (i = 1; i < block; i++) {
        end_i = block_end[i] + 0
        start_next = block_start[i + 1] + 0
        if ((end_i - start_next) == 1) {
          new_end = end_i - 1
          block_end[i] = pad(new_end, block_pad[i])
        }
      }
      for (i = 1; i <= block; i++) {
        print block_start[i] " --> " block_end[i]
        print block_text[i]
      }
    }
  ' "$MID_INPUT_FILE" > "$MID_OUTPUT_FILE"
  
  # Step 5: Merge with the prior if there is only one word and the time difference is one second
  MID_INPUT_FILE="$FOLDER/$TOPIC_NAME-$FILE_NUM-seconds-$STEP.txt"
  STEP="step5"
  MID_OUTPUT_FILE="$FOLDER/$TOPIC_NAME-$FILE_NUM-seconds-$STEP.txt"
  
  awk '
    function word_count(s,    n, arr) {
      n = split(s, arr, /[ \t]+/)
      return n
    }
    /-->/ {
      block++
      split($0, parts, /-->/)
      start[block] = parts[1]
      end[block] = parts[2]
      gsub(/^[ \t]+|[ \t]+$/, "", start[block])
      gsub(/^[ \t]+|[ \t]+$/, "", end[block])
      start_num[block] = start[block] + 0
      end_num[block] = end[block] + 0
      getline text_line
      text[block] = text_line
    }
    END {
      i = 1
      while (i <= block) {
        merged_start = start[i]
        merged_end = end[i]
        merged_text = text[i]
        while (i < block && word_count(text[i+1]) == 1 && ((end_num[i+1] - start_num[i+1]) == 1)) {
            merged_end = end[i+1]
            merged_text = merged_text " " text[i+1]
            i++
        }
        print merged_start " --> " merged_end
        print merged_text
        i++
      }
    }
  ' "$MID_INPUT_FILE" > "$MID_OUTPUT_FILE"
  
  # Step 6: Merge with the next block if there is only one word and the time difference is one second
  MID_INPUT_FILE="$FOLDER/$TOPIC_NAME-$FILE_NUM-seconds-$STEP.txt"
  STEP="step6"
  OUTPUT_FILE="$FOLDER/$FILE_NUM.txt"
  
  awk '
    function word_count(s,   n, arr) {
      n = split(s, arr, /[ \t]+/)
      return n
    }
    /-->/ {
      block++
      split($0, parts, /-->/)
      start[block] = parts[1]
      end[block]   = parts[2]
      gsub(/^[ \t]+|[ \t]+$/, "", start[block])
      gsub(/^[ \t]+|[ \t]+$/, "", end[block])
      start_num[block] = start[block] + 0
      getline text_line
      text[block] = text_line
    }
    END {
      i = 1
      while (i <= block) {
        merged_start = start[i]
        merged_end   = end[i]
        merged_text  = text[i]
        while (i < block && ((start_num[i+1] - start_num[i]) == 1) && (word_count(text[i+1]) > 1)) {
            merged_end  = end[i+1]
            merged_text = merged_text " " text[i+1]
            i++
        }
        print merged_start " --> " merged_end
        print merged_text
        i++
      }
    }
  ' "$MID_INPUT_FILE" > "$OUTPUT_FILE"
  
  # If DEBUG is enabled, remove intermediate files.
  if [ "$DEBUG" -eq 0 ]; then
      rm "$FOLDER/$TOPIC_NAME-$FILE_NUM-seconds-"*.txt
  fi

done

