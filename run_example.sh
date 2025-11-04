#!/bin/bash

# Quick example runner for AI Recruiter Agent
# This script sets up the environment and runs the example

set -e

echo "🤖 AI Recruiter Agent - Example Runner"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip install -q -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

echo ""
echo "🚀 Running example conversation simulation..."
echo ""

# Run the example
python example_usage.py

echo ""
echo "✨ Example completed!"
echo ""
echo "To run the actual server:"
echo "  make run"
echo ""
echo "To run tests:"
echo "  make test"
echo ""
