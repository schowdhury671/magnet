#!/bin/bash
source params.sh

DOWN_FOLDER="original-subtitles"
mkdir -p $DOWN_FOLDER

# Loop over the array indices
for i in "${!links[@]}"; do
    echo "#########################"
    echo "#########################"
    echo "Processing file number $i"
    link="${links[$i]}"
    output="${TOPIC_NAME}-${i}"
    
    yt-dlp --skip-download \
           --write-subs \
           --write-auto-subs \
           --sub-lang en \
           --sub-format ttml \
           --convert-subs srt \
           --output "tmp" \
           "https://www.youtube.com/watch?v=${link}" && \
                   
    # Check if the file was created
    if [ -f "tmp.en.srt" ]; then
        # Remove XML tags, empty lines, and truncate the timestamps after seconds
        awk '
            {
                gsub(/<[^>]*>/, "")
                print
            }
        ' tmp.en.srt | sed '/^[[:space:]]*$/d' | sed '/^[0-9]\+$/d' | sed -E 's/([0-9]{2}:[0-9]{2}:[0-9]{2}),[0-9]{3}/\1/g' > "${DOWN_FOLDER}/${output}.txt"
        rm tmp.en.srt
    else
        # If no subtitles were found, create an empty file
        > "${DOWN_FOLDER}/${output}-empty.txt"
    fi
done
