import os
import math
import argparse
import subprocess

def get_duration(file_path):
    
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries',
         'format=duration', '-of',
         'default=noprint_wrappers=1:nokey=1', file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    
    return float(result.stdout)

def split_precisely(input_file, output_dir, prefix, ext, segment_length):
    
    total_duration = get_duration(input_file)
    num_segments = math.ceil(total_duration / segment_length)

    for i in range(num_segments):
        start = i * segment_length
        duration = min(segment_length, total_duration - start)
        output_path = os.path.join(output_dir, f"{prefix}__{i:03d}.{ext}")
        cmd = [
            'ffmpeg',
            '-ss', str(start),
            '-t', str(duration),
            '-i', input_file,
            '-c', 'copy',
            output_path
        ]
        subprocess.run(cmd)

def split_video(video_dir, segment_length):
    
    output_dir = os.path.join(os.path.dirname(video_dir), 'segment-video')
    os.makedirs(output_dir, exist_ok=True)
    
    for filename in os.listdir(video_dir):
        
        base_name = os.path.splitext(filename)[0]
        split_precisely(os.path.join(video_dir, filename), output_dir, base_name, 'mp4', segment_length)
    
    

def split_audio(audio_dir, segment_length):
    
    output_dir = os.path.join(os.path.dirname(audio_dir), 'segment-audio')
    os.makedirs(output_dir, exist_ok=True)
    
    for filename in os.listdir(audio_dir):
        
        base_name = os.path.splitext(filename)[0]
        input_file = os.path.join(audio_dir, filename)
        output_path = os.path.join(output_dir, f"{base_name}__%03d.wav")
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-f', 'segment',
            '-segment_time', str(segment_length),
            '-c', 'copy',
            output_path
        ]
        subprocess.run(cmd)
    
    
if __name__ == "__main__":
    
    args = argparse.ArgumentParser()
    args.add_argument("--video_dir", type=str, default=None, help="Path to the video file")
    args.add_argument("--audio_dir", type=str, default=None, help="Path to the audio file")
    args.add_argument("--length", type=int, default=60, help="Length of each segment in seconds")
    args = args.parse_args()

    if args.video_dir is not None:
        split_video(args.video_dir, args.length)
        
    if args.audio_dir is not None:
        split_audio(args.audio_dir, args.length)