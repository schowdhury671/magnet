source params.sh
LINK="RKJXqZpPXsQ"
SERIAL="10"
FOLDER="original-subtitles"
OUTPUT="$FOLDER/$TOPIC_NAME-$SERIAL"
yt-dlp --skip-download \
       --write-subs \
       --write-auto-subs \
       --sub-lang en \
       --sub-format ttml \
       --convert-subs srt \
       --output "$FOLDER/tmp" \
       'https://www.youtube.com/watch?v='$LINK && \
awk '
    # Remove everything inside <...> but keep text outside
    {
        gsub(/<[^>]*>/, "")
        print
    }
' $FOLDER/tmp.en.srt | sed '/^[[:space:]]*$/d' | sed '/^[0-9]\+$/d' | sed -E 's/([0-9]{2}:[0-9]{2}:[0-9]{2}),[0-9]{3}/\1/g' > $OUTPUT.txt
rm $FOLDER/tmp.en.srt
