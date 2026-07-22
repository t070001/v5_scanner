#!/bin/bash
echo "Setting up analysis_tools virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "Done! Activate with: source analysis_tools/venv/bin/activate"
