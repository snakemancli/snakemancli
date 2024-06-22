# Snakeman Project Setup Guide

## Prerequisites
- Python 3
- pip
- System packages like ffmpeg, tesseract

## Setup Steps

```bash
# 1. Download the Repository
git clone https://github.com/snakemancli/snakemancli.git
cd snakemancli
```

# 2. Edit the top of snakemancli.sh File to Include Your API Keys
# Environment variables

```bash
vim snakemancli.sh

export OPENAI_API_KEY="your-openai-api-key"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/google-credentials.json"
export YOUTUBE_API_KEY="your-youtube-api-key"
```

# 3. Run setup.sh in the Project Root
```bash
./setup.sh
```

# 4. Use the CLI Menu to Resolve Dependencies
# Use the CLI menu to select "Dependency check"
# and resolve all required dependencies.
```bash
snakeman
```

# 5. You Are Ready to Use the Project
# Use the `snakeman` alias to start the CLI menu and run the project.
snakeman