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


def normalize_path(path):
    """Normalize a file path to avoid duplicates with different path formats"""
    # Use realpath to resolve any symbolic links and normalize path
    return os.path.normpath(os.path.abspath(os.path.realpath(path)))


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
                # Use join + normalization to ensure consistent paths
                video_path = os.path.join(VIDEOS_DIR, file)
                normalized_path = normalize_path(video_path)
                all_videos.append(normalized_path)
                print(f"Found video: {normalized_path}")
    except Exception as e:
        print(f"Error listing videos: {e}")

    return all_videos


def cleanup_annotation_data():
    """Cleanup annotation data by normalizing paths and merging duplicate entries"""
    annotation_data = load_annotations()
    if not annotation_data:
        return False

    # Create a new dict with normalized paths
    new_data = {}
    merged_paths = {}

    for path, annotations in annotation_data.items():
        norm_path = normalize_path(path)

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
            if (
                annotation not in new_data[norm_path]
            ):  # This works because dicts are comparable
                new_data[norm_path].append(annotation)

    # Only save if there were changes
    if new_data != annotation_data:
        result = save_annotations(new_data)
        return result, merged_paths
    return True, {}


@app.route("/cleanup_annotations", methods=["POST"])
def cleanup_annotations():
    """Handle annotation data cleanup"""
    success, merged_paths = cleanup_annotation_data()

    if success:
        if merged_paths:
            # Report what was merged
            message = "Annotation data cleaned up. Merged paths:"
            for norm_path, old_paths in merged_paths.items():
                if old_paths:  # Only show paths that were actually merged
                    video_name = os.path.basename(norm_path)
                    message += (
                        f"<br>• {video_name}: merged {len(old_paths)} duplicate paths"
                    )
            flash(message, "success")
        else:
            flash("Annotation data checked. No issues found.", "success")
    else:
        flash("Failed to clean up annotation data", "error")

    # Redirect to the same page
    return redirect(url_for("index"))


@app.route("/")
def index():
    """Render the main page with all available videos"""
    annotation_data = load_annotations()

    # Debug output to check paths
    print("\nLoaded annotation paths:")
    for path in annotation_data:
        print(f"  Original: {path}")
        print(f"  Normalized: {normalize_path(path)}")

    # Convert paths to normalized format
    norm_annotation_data = {}
    for path, annotations in annotation_data.items():
        norm_path = normalize_path(path)
        if norm_path not in norm_annotation_data:
            norm_annotation_data[norm_path] = []
        # Use extend instead of append to avoid nested lists
        for annotation in annotations:
            if annotation not in norm_annotation_data[norm_path]:
                norm_annotation_data[norm_path].append(annotation)

    all_video_paths = get_all_videos()  # These are already normalized

    # Debug output to compare paths
    print("\nComparing paths:")
    for video_path in all_video_paths:
        print(f"Video path: {video_path}")
        print(f"Has annotations: {video_path in norm_annotation_data}")

    # Get filter parameters
    filter_mode = request.args.get("filter", "all")  # Default to showing all videos
    search_query = request.args.get("search", "").lower()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))  # Show 50 videos per page

    # Track paths that appear in annotations but not in video directory
    missing_videos = []
    for video_path in norm_annotation_data:
        if video_path not in all_video_paths:
            video_basename = os.path.basename(video_path)
            all_basenames = [os.path.basename(p) for p in all_video_paths]
            if video_basename not in all_basenames:
                missing_videos.append(video_path)
            else:
                # If basename matches but full path doesn't, this is likely
                # a path normalization issue
                print(
                    f"Path mismatch for {video_basename} - in annotations but not exact match in videos dir"
                )

    # Process all videos and their annotation status
    filtered_videos = []
    for video_path in all_video_paths:
        annotations = norm_annotation_data.get(video_path, [])
        is_annotated = len(annotations) > 0

        # Apply filtering by annotation status
        if (filter_mode == "annotated" and not is_annotated) or (
            filter_mode == "not_annotated" and is_annotated
        ):
            continue

        # Apply search filtering
        video_name = os.path.basename(video_path)
        if search_query and search_query not in video_name.lower():
            continue

        filtered_videos.append(
            {
                "path": video_path,
                "name": video_name,
                "annotation_count": len(annotations),
                "is_annotated": is_annotated,
            }
        )

    # Sort videos: annotated videos first, then by name
    filtered_videos.sort(key=lambda x: (not x["is_annotated"], x["name"].lower()))

    # Calculate pagination
    total_pages = (len(filtered_videos) + per_page - 1) // per_page
    page = min(max(page, 1), total_pages if total_pages > 0 else 1)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_videos = filtered_videos[start_idx:end_idx]

    # Calculate some stats for display
    total_annotations = sum(len(anns) for anns in norm_annotation_data.values())
    annotation_issues = len(annotation_data) != len(norm_annotation_data)
    annotated_count = sum(1 for v in filtered_videos if v["is_annotated"])
    not_annotated_count = len(filtered_videos) - annotated_count

    # Get the currently selected video, if any
    selected_video = request.args.get("video")
    current_video = None
    annotations = []

    if selected_video:
        # Decode the selected video path
        try:
            video_path = normalize_path(
                base64.b64decode(selected_video).decode("utf-8")
            )
            if os.path.exists(video_path):
                current_video = {
                    "path": video_path,
                    "name": os.path.basename(video_path),
                    "encoded_path": selected_video,
                }
                annotations = norm_annotation_data.get(video_path, [])
        except:
            pass

    return render_template(
        "index.html",
        videos=paginated_videos,
        current_video=current_video,
        annotations=annotations,
        filter_mode=filter_mode,
        search_query=search_query,
        total_videos=len(all_video_paths),
        displayed_videos=len(filtered_videos),
        current_page=page,
        total_pages=total_pages,
        per_page=per_page,
        total_annotations=total_annotations,
        annotation_issues=annotation_issues,
        missing_videos=missing_videos,
        annotated_count=annotated_count,
        not_annotated_count=not_annotated_count,
    )


@app.route("/filter_videos", methods=["POST"])
def filter_videos():
    """Handle video filtering"""
    filter_mode = request.form.get("filter", "all")
    search_query = request.form.get("search", "")

    # Preserve the currently selected video if any
    selected_video = request.args.get("video")
    if selected_video:
        return redirect(
            url_for(
                "index", filter=filter_mode, search=search_query, video=selected_video
            )
        )
    return redirect(url_for("index", filter=filter_mode, search=search_query))


@app.route("/select_video", methods=["POST"])
def select_video():
    """Handle video selection"""
    video_path = request.form.get("video_path")
    # Preserve the current filter when selecting a video
    filter_mode = request.form.get("filter_mode", "all")

    if video_path:
        # Normalize path before encoding
        norm_path = normalize_path(video_path)
        # Encode the path to make it URL-safe
        encoded_path = base64.b64encode(norm_path.encode()).decode()
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

    # Normalize path before using it
    video_path = normalize_path(video_path)

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

    # Normalize path before using it
    video_path = normalize_path(video_path)

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
