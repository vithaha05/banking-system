#!/bin/bash
# Banking System - Run Script

echo "Starting Banking Transaction Processing System..."
echo "================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run the application
echo "Starting server on http://localhost:8080"
echo "API Documentation: http://localhost:8080/docs"
echo ""
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload

