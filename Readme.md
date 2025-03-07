# Project structure
```markdown
video-annotation/
├── backend/
│   ├── app.py          # Flask backend with routes for listing and 
|   ├── models.py       # Data models
annotation
│   ├── data/           # JSON data files (annotations.json)
│   └── utils.py        # Utility functions (e.g., file loading/saving)
├── frontend/
│   ├── index.html      # Home page listing videos
│   ├── annotation.html # Annotation page for individual videos
│   ├── script.js       # Frontend interactivity logic
│   └── style.css       # Styling for UI
├── videos/             # Your video files
└── README.md
```