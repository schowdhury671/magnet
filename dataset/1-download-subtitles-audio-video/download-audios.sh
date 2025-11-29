#!/bin/bash
source params.sh

DOWN_FOLDER="original-audio"
mkdir -p $DOWN_FOLDER

for i in "${!links[@]}"; do
    echo "#########################"
    echo "#########################"
    echo "Processing file number $i"
    link="${links[$i]}"
    output="${i}"

    yt-dlp -x https://www.youtube.com/watch?v=${link} -o $DOWN_FOLDER/$output
done
