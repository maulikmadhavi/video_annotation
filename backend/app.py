from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    send_from_directory,
    redirect,
    url_for,
    flash,
)
import json, os, base64

app = Flask(__name__, static_folder="../frontend", template_folder="../frontend")
app.secret_key = "video-annotation-tool-secret-key"  # For flash messages

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "annotation.json")
VIDEOS_DIR = os.path.join(os.path.dirname(__file__), "..", "videos")


def load_annotations():
    """Load annotations from JSON file"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        print(f"Error loading annotation file: {e}")
        return {}


def save_annotations(annotation_data):
    """Save annotations to JSON file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

        with open(DATA_FILE, "w") as f:
            json.dump(annotation_data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving annotation file: {e}")
        return False


def get_all_videos():
    """Get all video files from the videos directory"""
    all_videos = []
    try:
        for file in os.listdir(VIDEOS_DIR):
            if file.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
                video_path = os.path.join(VIDEOS_DIR, file)
                all_videos.append(video_path)
    except Exception as e:
        print(f"Error listing videos: {e}")

    return all_videos


@app.route("/")
def index():
    """Render the main page with all available videos"""
    annotation_data = load_annotations()
    all_video_paths = get_all_videos()
    videos = []
    filter_mode = request.args.get("filter", "all")  # Default to showing all videos

    # Process all videos and their annotation status
    for video_path in all_video_paths:
        annotations = annotation_data.get(video_path, [])
        is_annotated = len(annotations) > 0

        # Apply filtering
        if (filter_mode == "annotated" and not is_annotated) or (
            filter_mode == "not_annotated" and is_annotated
        ):
            continue

        video_name = os.path.basename(video_path)
        videos.append(
            {
                "path": video_path,
                "name": video_name,
                "annotation_count": len(annotations),
                "is_annotated": is_annotated,
            }
        )

    # Sort videos: annotated videos first, then by name
    videos.sort(key=lambda x: (not x["is_annotated"], x["name"].lower()))

    # Get the currently selected video, if any
    selected_video = request.args.get("video")
    current_video = None
    annotations = []

    if selected_video:
        # Decode the selected video path
        try:
            video_path = base64.b64decode(selected_video).decode("utf-8")
            if os.path.exists(video_path):
                current_video = {
                    "path": video_path,
                    "name": os.path.basename(video_path),
                    "encoded_path": selected_video,
                }
                annotations = annotation_data.get(video_path, [])
        except:
            pass

    return render_template(
        "index.html",
        videos=videos,
        current_video=current_video,
        annotations=annotations,
        filter_mode=filter_mode,
        total_videos=len(all_video_paths),
        displayed_videos=len(videos),
    )


@app.route("/filter_videos", methods=["POST"])
def filter_videos():
    """Handle video filtering"""
    filter_mode = request.form.get("filter", "all")
    # Preserve the currently selected video if any
    selected_video = request.args.get("video")
    if selected_video:
        return redirect(url_for("index", filter=filter_mode, video=selected_video))
    return redirect(url_for("index", filter=filter_mode))


@app.route("/select_video", methods=["POST"])
def select_video():
    """Handle video selection"""
    video_path = request.form.get("video_path")
    # Preserve the current filter when selecting a video
    filter_mode = request.form.get("filter_mode", "all")

    if video_path:
        # Encode the path to make it URL-safe
        encoded_path = base64.b64encode(video_path.encode()).decode()
        return redirect(url_for("index", video=encoded_path, filter=filter_mode))
    return redirect(url_for("index", filter=filter_mode))


@app.route("/add_annotation", methods=["POST"])
def add_annotation():
    """Add a new annotation"""
    video_path = request.form.get("video_path")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    encoded_path = request.form.get("encoded_path")

    if not all([video_path, start_time, end_time]):
        flash("Missing required fields", "error")
        return redirect(url_for("index", video=encoded_path))

    try:
        start_time = float(start_time)
        end_time = float(end_time)
    except ValueError:
        flash("Start time and end time must be valid numbers", "error")
        return redirect(url_for("index", video=encoded_path))

    if start_time >= end_time:
        flash("End time must be greater than start time", "error")
        return redirect(url_for("index", video=encoded_path))

    annotation_data = load_annotations()

    if video_path not in annotation_data:
        annotation_data[video_path] = []

    annotation_data[video_path].append({"start_time": start_time, "end_time": end_time})

    if save_annotations(annotation_data):
        flash("Annotation added successfully", "success")
    else:
        flash("Failed to save annotation", "error")

    return redirect(url_for("index", video=encoded_path))


@app.route("/jump_to_annotation", methods=["POST"])
def jump_to_annotation():
    """Jump to a specific annotation time"""
    video_path = request.form.get("video_path")
    start_time = request.form.get("start_time")
    encoded_path = request.form.get("encoded_path")

    # Set a session variable or parameter to indicate jump time
    return redirect(url_for("index", video=encoded_path, jump_to=start_time))


@app.route("/videos/<path:filename>")
def serve_video(filename):
    """Serve video files"""
    return send_from_directory(VIDEOS_DIR, filename)


@app.route("/delete_annotation", methods=["POST"])
def delete_annotation():
    """Delete an annotation"""
    video_path = request.form.get("video_path")
    index = request.form.get("index")
    encoded_path = request.form.get("encoded_path")

    if not all([video_path, index]):
        flash("Missing required fields", "error")
        return redirect(url_for("index", video=encoded_path))

    try:
        index = int(index)
    except ValueError:
        flash("Invalid annotation index", "error")
        return redirect(url_for("index", video=encoded_path))

    annotation_data = load_annotations()

    if video_path in annotation_data and 0 <= index < len(annotation_data[video_path]):
        # Remove the specified annotation
        annotation_data[video_path].pop(index)

        if save_annotations(annotation_data):
            flash("Annotation deleted successfully", "success")
        else:
            flash("Failed to delete annotation", "error")
    else:
        flash("Annotation not found", "error")

    return redirect(url_for("index", video=encoded_path))


if __name__ == "__main__":
    app.run(debug=True)
