#!/usr/bin/env python3
"""
Script to fix annotation path issues by normalizing all paths
and merging duplicate entries.
"""

import json
import os


def normalize_path(path):
    """Normalize a file path to avoid duplicates with different path formats"""
    return os.path.normpath(os.path.abspath(os.path.realpath(path)))


def fix_annotation_data(annotation_file):
    """Fix annotation data by normalizing paths and merging duplicate entries"""
    try:
        # Load the annotation file
        with open(annotation_file, "r") as f:
            annotation_data = json.load(f)

        print(f"Loaded {len(annotation_data)} video entries from annotation file")

        # Create a new dict with normalized paths
        new_data = {}
        merged_paths = {}

        for path, annotations in annotation_data.items():
            print(f"\nProcessing: {path}")
            norm_path = normalize_path(path)
            print(f"Normalized: {norm_path}")

            # Keep track of path normalization for reporting
            if norm_path not in merged_paths:
                merged_paths[norm_path] = []
            if path != norm_path:
                merged_paths[norm_path].append(path)

            # Add annotations to the normalized path
            if norm_path not in new_data:
                new_data[norm_path] = []

            # Merge annotations without duplicates
            for annotation in annotations:
                if annotation not in new_data[norm_path]:
                    new_data[norm_path].append(annotation)

        # Report what was merged
        print("\nPath merging results:")
        for norm_path, old_paths in merged_paths.items():
            if old_paths:
                video_name = os.path.basename(norm_path)
                print(f"• {video_name}: merged {len(old_paths)} duplicate paths")
                for old in old_paths:
                    print(f"  - {old}")

        # Only save if there were changes
        if new_data != annotation_data:
            backup_file = annotation_file + ".bak"
            print(f"Creating backup of original file as {backup_file}")
            with open(backup_file, "w") as f:
                json.dump(annotation_data, f, indent=4)

            print(f"Writing fixed annotation data to {annotation_file}")
            with open(annotation_file, "w") as f:
                json.dump(new_data, f, indent=4)

            print(f"Fixed annotation file now has {len(new_data)} video entries")
            return True
        else:
            print("No changes needed in the annotation data")
            return False
    except Exception as e:
        print(f"Error fixing annotation data: {e}")
        return False


if __name__ == "__main__":
    annotation_file = os.path.join(
        os.path.dirname(__file__), "backend", "data", "annotation.json"
    )
    if not os.path.exists(annotation_file):
        print(f"Annotation file not found: {annotation_file}")
    else:
        print(f"Fixing annotation file: {annotation_file}")
        if fix_annotation_data(annotation_file):
            print("Successfully fixed annotation data.")
        else:
            print("No changes made to annotation data or error occurred.")
