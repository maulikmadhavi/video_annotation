#!/bin/bash

echo "Video Annotation Tool - Benchmark"
echo "================================="

# Check for ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "Warning: ffmpeg is not installed. Video generation will be disabled."
    echo "To install ffmpeg:"
    echo "  - Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  - macOS: brew install ffmpeg"
    echo "  - Windows: Download from https://ffmpeg.org/download.html"
    echo ""
fi

# Run the benchmark script
python benchmark.py

echo ""
echo "Benchmark completed."
echo "If you want to use the benchmark data, run:"
echo "  cp backend/data/benchmark_annotation.json backend/data/annotation.json"
echo ""
echo "Then start the application with:"
echo "  ./run.sh"
