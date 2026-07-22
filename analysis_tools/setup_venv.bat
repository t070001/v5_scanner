@echo off
echo Setting up analysis_tools virtual environment...
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo Done! Activate with: analysis_tools\venv\Scripts\activate.bat
