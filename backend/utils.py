import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
ANNOTATIONS_FILE = os.path.join(DATA_DIR, "annotations.json")


def load_annotations():
    try:
        with open(ANNOTATIONS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_annotations(data):
    with open(ANNOTATIONS_FILE, "w") as f:
        json.dump(data, f, indent=4)
