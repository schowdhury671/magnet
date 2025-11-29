import os
import argparse
import subprocess

def process_video(video_dir):

    video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
    output_dir = os.path.join(os.path.dirname(video_dir), "process-video")
    os.makedirs(output_dir, exist_ok=True)
    
    for filename in os.listdir(video_dir):
        
        if filename.lower().endswith(video_extensions):
            
            input_path = os.path.join(video_dir, filename)
            output_path = os.path.join(output_dir, filename)
            print(f"Processing: {filename}")
            
            command = [
                "ffmpeg",
                "-i", input_path,
                "-map", "0",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "192k",
                output_path
            ]
            
            subprocess.run(command, check=True)

def process_audio(audio_dir):
    
    output_dir = os.path.join(os.path.dirname(audio_dir), "process-audio")
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(audio_dir):
        
        if filename.lower().endswith('.m4a'):
            
            input_path = os.path.join(audio_dir, filename)
            output_filename = os.path.splitext(filename)[0] + '.wav'
            output_path = os.path.join(output_dir, output_filename)
            print(f"Converting: {filename} -> {output_filename}")

            command = [
                "ffmpeg",
                "-i", input_path,
                "-acodec", "pcm_s16le",
                output_path
            ]

            subprocess.run(command, check=True)



if __name__ == "__main__":
    
    args = argparse.ArgumentParser()
    args.add_argument("--video_dir", type=str, default=None, help="Path to the video directory.")
    args.add_argument("--audio_dir", type=str, default=None, help="Path to the video directory.")
    args = args.parse_args()
    
    if args.video_dir is not None:
        process_video(args.video_dir)
        
    if args.audio_dir is not None:
        process_audio(args.audio_dir)