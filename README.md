# Snakeman CLI

Snakeman CLI is a command-line interface for automating various video and image processing tasks. It supports downloading videos and images, captioning images, editing videos with and without TTS, and creating long-format content from local source material.

## Features

- **Download Mode**: Download videos or images using specified keywords.
- **Automated Download and Creation Mode**: Automatically download and process videos.
- **Image Captioner**: Caption downloaded images.
- **No TTS Edit**: Process videos without TTS.
- **Warhammer**: Create long-format content from local source material.
- **TTS Edit**: Process videos with TTS.
- **Dependency Check**: Install general or CPU-only requirements.

## Requirements

- Python 3.7 or higher
- Virtualenv
- Tested on Arch Linux and Gentoo

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/Jason-Goon/snakeman-CLI.git
    cd snakeman-CLI
    ```

2. Set up the virtual environment:
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

## Configuration

Before running the script, you need to update the `snakemacli.sh` file with your own API keys

This project is licensed under the Zero-Clause BSD License - see the LICENSE file for details.

