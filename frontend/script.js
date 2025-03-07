document.addEventListener('DOMContentLoaded', () => {
    const videoListDiv = document.getElementById('videoList');
    const videoAreaDiv = document.getElementById('videoArea');
    const videoPlayer = document.getElementById('videoPlayer');
    const startTimeInput = document.getElementById('startTime');
    const endTimeInput = document.getElementById('endTime');
    const addAnnotationButton = document.getElementById('addAnnotation');
    const annotationDisplayDiv = document.getElementById('annotationDisplay');
    const currentVideoTitle = document.getElementById('currentVideoTitle');

    let currentVideo = null;
    let annotations = [];

    function loadVideos() {
        fetch('/videos')
            .then(response => response.json())
            .then(videos => {
                videoListDiv.innerHTML = '';
                videos.forEach(video => {
                    const videoItem = document.createElement('div');
                    videoItem.className = 'video-item';
                    videoItem.textContent = video.filename;
                    
                    // Add annotation status indicator
                    const statusBadge = document.createElement('span');
                    statusBadge.className = `status-badge ${video.annotated ? 'annotated' : 'not-annotated'}`;
                    statusBadge.textContent = video.annotated ? 'Annotated' : 'Not Annotated';
                    videoItem.appendChild(statusBadge);
                    
                    videoItem.addEventListener('click', () => {
                        // Remove active class from all items
                        document.querySelectorAll('.video-item').forEach(item => {
                            item.classList.remove('active');
                        });
                        // Add active class to clicked item
                        videoItem.classList.add('active');
                        loadVideo(video.filename);
                    });
                    videoListDiv.appendChild(videoItem);
                });
            })
            .catch(error => {
                console.error('Error loading videos:', error);
                videoListDiv.innerHTML = '<p>Error loading videos</p>';
            });
    }

    function loadVideo(filename) {
        currentVideo = filename;
        currentVideoTitle.textContent = `Video: ${filename}`;
        videoPlayer.src = `videos/${filename}`;
        videoAreaDiv.style.display = 'block';

        fetch(`/annotations/${filename}`)
            .then(response => response.json())
            .then(data => {
                console.log('Received annotations:', data);
                annotations = Array.isArray(data) ? data : (data.annotations || []);
                console.log('Processed annotations:', annotations);
                displayAnnotations();
            })
            .catch(error => {
                console.error('Error loading annotations:', error);
                annotationDisplayDiv.innerHTML = '<p>Error loading annotations</p>';
            });
    }

    function displayAnnotations() {
        annotationDisplayDiv.innerHTML = '';
        console.log('Displaying annotations:', annotations);
        
        if (!annotations || annotations.length === 0) {
            annotationDisplayDiv.innerHTML = '<p>No annotations available</p>';
            return;
        }

        annotations.forEach(segment => {
            const segmentDiv = document.createElement('div');
            segmentDiv.className = 'annotation-item';
            segmentDiv.textContent = `Start: ${segment.start_time.toFixed(2)}, End: ${segment.end_time.toFixed(2)}`;
            
            // Added interactive behavior: clicking the segment jumps to the start time
            segmentDiv.title = 'Click to jump to start time';
            segmentDiv.addEventListener('click', () => {
                videoPlayer.currentTime = segment.start_time;
                videoPlayer.play();
                
                // Set a timeout to pause at the end time
                const duration = segment.end_time - segment.start_time;
                setTimeout(() => {
                    if (videoPlayer.currentTime >= segment.end_time) {
                        videoPlayer.pause();
                    }
                }, duration * 1000);
            });
            
            annotationDisplayDiv.appendChild(segmentDiv);
        });
    }

    addAnnotationButton.addEventListener('click', () => {
        const startTime = parseFloat(startTimeInput.value);
        const endTime = parseFloat(endTimeInput.value);

        if (!isNaN(startTime) && !isNaN(endTime) && startTime < endTime) {
            annotations.push({ start_time: startTime, end_time: endTime });
            annotations.sort((a, b) => a.start_time - b.start_time);
            displayAnnotations();
            saveAnnotations();
            startTimeInput.value = '';
            endTimeInput.value = '';
        } else {
            alert('Please enter valid start and end times (start must be less than end)');
        }
    });

    function saveAnnotations() {
        fetch(`/annotations/${currentVideo}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ annotations: annotations })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to save annotations');
            }
            return response.json();
        })
        .then(data => {
            console.log('Annotations saved successfully', data);
        })
        .catch(error => {
            console.error('Error saving annotations:', error);
            alert('Failed to save annotations. Please try again.');
        });
    }

    // Add keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (currentVideo && videoPlayer) {
            // Space to toggle play/pause
            if (e.code === 'Space') {
                e.preventDefault();
                if (videoPlayer.paused) {
                    videoPlayer.play();
                } else {
                    videoPlayer.pause();
                }
            }
            
            // Left arrow to go back 5 seconds
            if (e.code === 'ArrowLeft') {
                videoPlayer.currentTime = Math.max(0, videoPlayer.currentTime - 5);
            }
            
            // Right arrow to go forward 5 seconds
            if (e.code === 'ArrowRight') {
                videoPlayer.currentTime = Math.min(videoPlayer.duration, videoPlayer.currentTime + 5);
            }
        }
    });

    loadVideos();
});