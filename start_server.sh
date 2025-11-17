#!/bin/bash

# Socratic Learning Companion - Startup Script

echo "======================================================================="
echo "  Socratic Learning Companion - Starting Server"
echo "======================================================================="
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python is not installed or not in PATH"
    exit 1
fi

echo "✅ Python found: $(python --version)"
echo ""

# Check if required packages are installed
echo "Checking dependencies..."
python -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: FastAPI or Uvicorn not found. Installing..."
    pip install -q fastapi uvicorn
fi

python -c "import google.generativeai" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Google Generative AI not found. Please run: pip install google-generativeai"
fi

echo "✅ Dependencies checked"
echo ""

# Start the FastAPI server
echo "======================================================================="
echo "  Starting FastAPI Backend on http://localhost:8000"
echo "======================================================================="
echo ""
echo "📝 API Documentation will be available at:"
echo "   - Swagger UI: http://localhost:8000/docs"
echo "   - ReDoc: http://localhost:8000/redoc"
echo ""
echo "🌐 Frontend: Open frontend/index.html in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "======================================================================="
echo ""

# Run the server
python -m uvicorn src.api.main:app --reload --port 8000 --host 0.0.0.0
