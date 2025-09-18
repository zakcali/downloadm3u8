import asyncio
import aiohttp
import os
import subprocess
from urllib.parse import urljoin
import argparse

async def download_file(session, url, filename):
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        print(f"Skipping: {filename} (already exists and is not empty)")
        return
    
    try:
        # The URL must be properly quoted before sending
        async with session.get(url, skip_auto_headers={'User-Agent'}) as response:
            response.raise_for_status()
            with open(filename, 'wb') as f:
                async for chunk in response.content.iter_chunked(1024):
                    f.write(chunk)
            print(f"Downloaded: {filename}")
    except aiohttp.ClientError as e:
        print(f"Failed to download {url}: {e}")
        raise

def parse_m3u8(content, m3u8_base_url):
    segments = []
    for line in content.split('\n'):
        line = line.strip()
        # We only care about lines that are not comments or blank
        if line and not line.startswith('#'):
            # urljoin is smart. It correctly combines the base m3u8 URL
            # with the segment line, whether the line is a relative path
            # (like 'seg-1.ts') or a full URL.
            full_segment_url = urljoin(m3u8_base_url, line)
            segments.append(full_segment_url)
    return segments

async def download_segments(segments, output_dir):
    semaphore = asyncio.Semaphore(10)
    # Adding a default User-Agent can help avoid being blocked
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = []
        for i, segment_url in enumerate(segments):
            tasks.append(asyncio.create_task(download_file_with_semaphore(
                session, segment_url, os.path.join(output_dir, f'segment_{i:03d}.ts'), semaphore
            )))
        await asyncio.gather(*tasks)

async def download_file_with_semaphore(session, url, filename, semaphore):
    async with semaphore:
        await download_file(session, url, filename)

def concatenate_segments(input_dir, output_file):
    segment_list_path = os.path.join(input_dir, 'segment_list.txt')
    ts_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.ts') and os.path.getsize(os.path.join(input_dir, f)) > 0])

    if not ts_files:
        print("\nError: No valid .ts segment files found to concatenate.")
        return

    with open(segment_list_path, 'w') as f:
        for filename in ts_files:
            # Using file paths with single quotes for ffmpeg is safer
            f.write(f"file '{filename}'\n")

    output_path = os.path.abspath(output_file)
    
    ffmpeg_cmd = [
        'ffmpeg',
        '-y',  # Overwrite output file if it exists
        '-f', 'concat',
        '-safe', '0',
        '-i', segment_list_path,
        '-fflags', '+genpts+igndts',  # Add this line to force generation of PTS
        '-map', '0:v',  # Map the video stream from the first input (0)
        '-map', '0:a',  # Map the audio stream from the first input (0)
        '-c', 'copy',
        output_path
    ]
    
    print("\nRunning ffmpeg command...")
    try:
        result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg failed with exit code {e.returncode}")
        print("ffmpeg stdout:", e.stdout)
        print("ffmpeg stderr:", e.stderr)
        return
    
    print("Cleaning up segment files...")
    for filename in ts_files:
        os.remove(os.path.join(input_dir, filename))
    os.remove(segment_list_path)
    if not os.listdir(input_dir):
        os.rmdir(input_dir)

async def main():
    parser = argparse.ArgumentParser(description="Download and concatenate video segments from an m3u8 URL.")
    parser.add_argument('m3u8_url', help="The m3u8 URL to download video segments from")
    parser.add_argument('output_file', help="The name of the output file (e.g., output.mp4)")
    args = parser.parse_args()

    m3u8_url = args.m3u8_url
    output_file = args.output_file
    
    output_dir = 'video_segments'
    os.makedirs(output_dir, exist_ok=True)

    try:
        print("Downloading m3u8 file...")
        async with aiohttp.ClientSession() as session:
            async with session.get(m3u8_url) as response:
                response.raise_for_status()
                m3u8_content = await response.text()

        print("Parsing m3u8 file...")
        segments = parse_m3u8(m3u8_content, m3u8_url)
        
        if not segments:
            print("Error: No .ts segments found in the m3u8 file.")
            return

        print(f"Found {len(segments)} segments. Downloading concurrently (max 10 at a time)...")
        await download_segments(segments, output_dir)

        print("\nConcatenating segments...")
        concatenate_segments(output_dir, output_file)

        print(f"\nVideo download and conversion complete. Output file: {output_file}")

    except aiohttp.ClientError as e:
        print(f"\nError: Failed to download the m3u8 file or its segments.")
        print(f"Details: {e}")
        print("Please check if the URL is correct and has not expired.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

