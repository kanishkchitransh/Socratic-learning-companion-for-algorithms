# Frontend - Socratic Learning Companion

Simple HTML/CSS/JavaScript frontend for testing the Socratic Learning Companion API.

## Features

- Student registration
- Session management
- Real-time Socratic dialogue
- Progress tracking
- Curriculum visualization

## Usage

1. Make sure the FastAPI backend is running:
   ```bash
   cd ..
   python -m uvicorn src.api.main:app --reload --port 8000
   ```

2. Open `index.html` in a web browser:
   ```bash
   # On macOS
   open index.html

   # On Linux
   xdg-open index.html

   # Or simply double-click the file
   ```

3. The frontend will automatically try to connect to the API at `http://localhost:8000`

## Workflow

1. **Register** as a student with your details
2. **Start a session** by selecting a topic
3. **Engage in Socratic dialogue** - the tutor will ask questions to guide your learning
4. **Track your progress** to see mastered topics and understanding scores
5. **View the curriculum** to see available topics and prerequisites

## Note

This is a simple testing interface. For production, consider:
- Using a frontend framework (React, Vue, etc.)
- Adding authentication
- Implementing WebSocket for real-time chat
- Adding better error handling and loading states
- Implementing responsive design improvements
