# M3U8 Video Downloader

This Python script provides a fast and efficient way to download video content streamed via the HLS (HTTP Live Streaming) protocol. It parses an `.m3u8` playlist, concurrently downloads all the transport stream (`.ts`) video segments, and then uses FFmpeg to concatenate them into a single, playable video file (e.g., `.mp4`).

## Features

- **Concurrent Downloads**: Downloads up to 10 video segments simultaneously for significant speed improvements.
- **Automatic Concatenation**: Uses FFmpeg to seamlessly join the downloaded video segments in the correct order.
- **Efficient & Resilient**: Skips segments that are already downloaded and not empty, allowing for easy resumption of failed downloads.
- **Cleanup**: Automatically removes the individual `.ts` segment files and temporary helper files after a successful conversion.
- **Error Handling**: Provides feedback if the M3U8 file or segments fail to download.
- **Command-Line Interface**: Simple to use with command-line arguments for the M3U8 URL and the desired output filename.

## How It Works

1.  **Fetch Playlist**: The script first downloads the main `.m3u8` file from the provided URL.
2.  **Parse Segments**: It then parses this file to extract the URLs for all the individual `.ts` video segments.
3.  **Download Concurrently**: The script downloads the `.ts` files asynchronously, with a limit of 10 concurrent downloads to be efficient without overwhelming the server.
4.  **Concatenate with FFmpeg**: Once all segments are downloaded, it generates a list file and uses FFmpeg to concatenate them into a single output file. This process is very fast as it copies the streams without re-encoding.
5.  **Clean Up**: After the final video is created, the script deletes the temporary `video_segments` directory and all its contents.

## Prerequisites

Before running this script, you must have the following installed:

1.  **Python 3.7+**
2.  **aiohttp**: A Python library for asynchronous HTTP requests.
3.  **FFmpeg**: An open-source tool for handling multimedia files. It must be installed and accessible in your system's PATH.

## Installation

1.  **Clone the repository or download the script:**
    ```sh
    git clone https://github.com/zakcali/downloadm3u8.git
    cd downloadm3u8
    ```

2.  **Install the required Python library:**
    ```sh
    pip install aiohttp
    ```

3.  **Install FFmpeg:**
    -   **Windows**: Download a build from the [FFmpeg website](https://ffmpeg.org/download.html) and add the `bin` directory to your system's PATH.
    -   **macOS (using Homebrew)**:
        ```sh
        brew install ffmpeg
        ```
    -   **Linux (using apt)**:
        ```sh
        sudo apt update
        sudo apt install ffmpeg
        ```

## Usage

Run the script from your terminal using the following command structure:

```sh
python downloadm3u8.py "<M3U8_URL>" "<OUTPUT_FILENAME>"
```

### Arguments:

-   `M3U8_URL`: The full URL to the `.m3u8` playlist file. **This should be enclosed in quotes.**
-   `OUTPUT_FILENAME`: The desired name for the final video file (e.g., `output.mp4`, `video.mkv`).

### Example:

```sh
python downloadm3u8.py "https://example.com/path/to/your/stream.m3u8" "my_downloaded_video.mp4"
```

## Disclaimer

This tool is intended for downloading content that you have the legal right to access and save. Please be aware of the terms of service for the websites you are using this script on and respect copyright laws. The developer assumes no liability for any misuse of this script.
