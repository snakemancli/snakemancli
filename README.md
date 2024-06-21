## Hi there 👋

# SnakemanCLI - Bulk Video and Image Processing Tool

SnakemanCLI is a comprehensive tool designed to download and process videos and images, perform TTS, add captions, convert image formats, and more. The tool is wrapped with a command line interface to simplify the workflow.

## License

This project is licensed under the Zero-Clause BSD license.

## Requirements

- Python 3.x
- google-api-python-client
- yt-dlp
- moviepy
- ffmpeg-python
- requests
- Pillow

## Setup

### Using a Virtual Environment

It is recommended to use a virtual environment to manage dependencies. Follow these steps to set up the project:

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
Install the required packages:

bash
Copy code
pip install google-api-python-client yt-dlp moviepy ffmpeg-python requests pillow
Set up your environment variables:

bash
Copy code
export OPENAI_API_KEY="sk-pppppppprrrrrrrooooooojjjjjeeeeccccctttttkkkkkeeeeyyyyy"
export GOOGLE_APPLICATION_CREDENTIALS="/home/based/king/snakeman/project-name-420-twotimesaday.json"
export YOUTUBE_API_KEY="g3tth3k3y5fr0mth3w3b5it35"
Usage
The setup.sh script creates a command called snakeman that provides a menu-driven interface to perform various tasks.

Running the setup script
Make the setup script executable:

bash
Copy code
chmod +x setup.sh
Run the setup script:

bash
Copy code
./setup.sh
Command Line Interface
After running the setup script, use the snakeman command to access the menu:

bash
Copy code
snakeman
The menu provides the following options:

