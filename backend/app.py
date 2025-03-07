from flask import Flask, request, jsonify, render_template, send_from_directory
import json, os

app = Flask(__name__, static_folder="../frontend", template_folder="../frontend")

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "annotations.json")
VIDEOS_DIR = os.path.join(os.path.dirname(__file__), "..", "videos")


def load_annotations():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


@app.route("/videos", methods=["GET"])
def get_videos():
    video_files = [
        f for f in os.listdir(VIDEOS_DIR) if f.endswith((".mp4", ".avi", ".mov"))
    ]
    annotations = load_annotations()
    video_list = [{"filename": f, "annotated": f in annotations} for f in video_files]
    return jsonify(video_list)


@app.route("/annotations/<filename>")
def annotations(filename):
    annotations_data = load_annotations()
    ann = annotations_data.get(filename, [])
    return render_template("annotation.html", filename=filename, annotations=ann)


@app.route("/videos/<path:filename>")
def video_files(filename):
    return send_from_directory(VIDEOS_DIR, filename)


@app.route("/annotations/<filename>", methods=["POST"])
def save_annotations(filename):
    data = request.get_json()
    annotations = load_annotations()
    # Convert dictionaries back to tuples for saving
    annotations[filename] = [
        (item["start_time"], item["end_time"]) for item in data.get("annotations", [])
    ]
    with open(DATA_FILE, "w") as f:
        json.dump(annotations, f)
    return jsonify({"message": "Annotations saved successfully"})


@app.route("/api/annotations/<filename>", methods=["GET"])
def get_annotations(filename):
    annotations_data = load_annotations()
    ann = annotations_data.get(filename, [])
    return jsonify(ann)


@app.route("/")
def index():
    """Serve the main index.html page"""
    return send_from_directory("../frontend", "index.html")


if __name__ == "__main__":
    app.run(debug=True)
