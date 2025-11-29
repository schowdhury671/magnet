#!/bin/bash
source params.sh

DOWN_FOLDER="original-videos"
mkdir -p $DOWN_FOLDER

for i in "${!links[@]}"; do
    echo "#########################"
    echo "#########################"
    echo "Processing file number $i"
    link="${links[$i]}"
    output="${i}"

    if ! yt-dlp -f "bestvideo[width=854][height=480]+bestaudio/best[width=854][height=480]" "https://www.youtube.com/watch?v=${link}" -o "${DOWN_FOLDER}/${output}"; then
        echo "Primary download failed. Attempting fallback format..."
        # Fallback format
        yt-dlp -f "bestvideo[width=1280][height=720]+bestaudio/best[width=1280][height=720]" "https://www.youtube.com/watch?v=${link}" -o "${DOWN_FOLDER}/${output}"
    fi

done
