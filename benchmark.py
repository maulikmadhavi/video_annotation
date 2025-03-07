#!/usr/bin/env python3
"""
Script to benchmark the performance of the Video Annotation Tool with large video collections.
This creates dummy data to simulate having 300-500 videos, including actual video files.
"""

import json
import os
import random
import time
import string
import subprocess
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


def check_ffmpeg():
    """Check if ffmpeg is installed"""
    try:
        subprocess.run(
            ["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return True
    except FileNotFoundError:
        return False


def create_dummy_video(output_path, duration=5):
    """Create a dummy video file using ffmpeg"""
    # Generate a simple color test pattern video
    color = random.choice(["red", "blue", "green", "yellow", "white", "black"])
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color={color}:s=640x480:d={duration}",
                "-c:v",
                "libx264",
                "-tune",
                "stillimage",
                "-pix_fmt",
                "yuv420p",
                "-t",
                str(duration),
                output_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.SubprocessError as e:
        print(f"Error creating video {output_path}: {e}")
        return False


def create_test_data(num_videos=300, annotation_percentage=30, create_videos=True):
    """Create test data for benchmarking"""
    # Path to videos directory and annotation file
    videos_dir = os.path.join(os.path.dirname(__file__), "videos")
    os.makedirs(videos_dir, exist_ok=True)

    annotation_file = os.path.join(
        os.path.dirname(__file__), "backend", "data", "benchmark_annotation.json"
    )

    # Create random video filenames
    video_filenames = []
    for i in range(num_videos):
        # Create some with standard names and some with random names
        if i < num_videos // 3:
            video_name = f"video{i+1}.mp4"
        else:
            # Random string for video name
            random_str = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=8)
            )
            video_name = f"vid_{random_str}.mp4"

        video_filenames.append(video_name)

    # Create dummy annotation data
    annotation_data = {}
    num_to_annotate = int(num_videos * annotation_percentage / 100)

    if create_videos:
        if not check_ffmpeg():
            print("Warning: ffmpeg is not installed. Cannot create actual video files.")
            print("Please install ffmpeg to create test videos.")
            create_videos = False
        else:
            print(
                f"Creating {num_videos} dummy video files. This may take some time..."
            )
            print("Videos will be very small test patterns.")

            # Create videos in parallel for better performance
            videos_created = 0

            def create_video_task(filename):
                output_path = os.path.join(videos_dir, filename)
                duration = random.uniform(
                    3, 10
                )  # Random duration between 3 and 10 seconds
                success = create_dummy_video(output_path, duration)
                return filename, success

            # Use ThreadPoolExecutor to create videos in parallel
            with ThreadPoolExecutor(
                max_workers=min(os.cpu_count() or 1, 8)
            ) as executor:
                futures = [
                    executor.submit(create_video_task, filename)
                    for filename in video_filenames
                ]

                # Show progress
                for future in as_completed(futures):
                    filename, success = future.result()
                    if success:
                        videos_created += 1
                        progress = videos_created / num_videos * 100
                        sys.stdout.write(
                            f"\rProgress: {progress:.1f}% ({videos_created}/{num_videos})"
                        )
                        sys.stdout.flush()

            print("\nVideo creation complete.")
            print(f"Created {videos_created} video files in {videos_dir}")

    # Create annotation entries
    for i in range(num_to_annotate):
        video_path = os.path.join(videos_dir, video_filenames[i])
        video_path = os.path.abspath(video_path)

        # Create random number of annotations (between 1 and 10)
        num_annotations = random.randint(1, 10)
        annotations = []

        for _ in range(num_annotations):
            # Use durations appropriate for the video length (typically between 0-10 seconds for our test videos)
            start_time = random.uniform(0, 8)
            duration = random.uniform(0.5, 2)
            end_time = min(
                start_time + duration, 10
            )  # Make sure end_time doesn't exceed video length

            annotations.append(
                {"start_time": round(start_time, 1), "end_time": round(end_time, 1)}
            )

        annotation_data[video_path] = annotations

    # Save the annotation data
    os.makedirs(os.path.dirname(annotation_file), exist_ok=True)
    with open(annotation_file, "w") as f:
        json.dump(annotation_data, f, indent=4)

    print(
        f"\nCreated benchmark data with {num_videos} videos and {num_to_annotate} annotated videos"
    )
    print(f"Annotation data saved to {annotation_file}")
    print(
        f"Total annotations created: {sum(len(anns) for anns in annotation_data.values())}"
    )

    return annotation_file


def test_load_annotations(annotation_file):
    """Test loading annotation data"""
    start_time = time.time()

    with open(annotation_file, "r") as f:
        data = json.load(f)

    end_time = time.time()

    print(f"Loading annotation data took {end_time - start_time:.4f} seconds")
    print(f"Loaded {len(data)} videos with annotations")
    print(f"Total annotations: {sum(len(anns) for anns in data.values())}")

    return data


if __name__ == "__main__":
    print("Video Annotation Tool - Benchmark Data Generator")
    print("-----------------------------------------------")

    num_videos = int(
        input("Enter number of videos to simulate (default: 300): ") or 300
    )
    annotation_percentage = int(
        input("Enter percentage of videos with annotations (default: 30): ") or 30
    )

    create_videos = input(
        "Create actual video files? This requires ffmpeg. (y/n, default: y): "
    )
    create_videos = create_videos.lower() != "n"

    annotation_file = create_test_data(num_videos, annotation_percentage, create_videos)
    test_load_annotations(annotation_file)

    print("\nBenchmark data created successfully!")
    print(
        "To use this data for testing, copy the benchmark annotation file to annotation.json:"
    )
    print(
        f"cp {annotation_file} {os.path.join(os.path.dirname(annotation_file), 'annotation.json')}"
    )
