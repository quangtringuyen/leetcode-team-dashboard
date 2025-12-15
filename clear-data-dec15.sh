#!/bin/bash

# Script to clear data for December 15, 2025
# This is a wrapper script for the Python data clearing script

set -e

echo "🗑️  LeetCode Dashboard - Clear Data for Dec 15, 2025"
echo "=================================================="
echo ""

# Check if Python script exists
if [ ! -f "clear_data_dec15.py" ]; then
    echo "❌ Error: clear_data_dec15.py not found!"
    exit 1
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Run the Python script
echo "🚀 Running data clearing script..."
echo ""
python3 clear_data_dec15.py

echo ""
echo "✅ Script execution completed!"
