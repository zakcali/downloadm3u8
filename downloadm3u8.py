import asyncio
import aiohttp
import os
import subprocess
from urllib.parse import urljoin
import argparse  # Import argparse for command-line argument parsing


async def download_file(session, url, filename):
    if not os.path.exists(filename):  # Check if file already exists
        async with session.get(url) as response:
            with open(filename, 'wb') as f:
                async for chunk in response.content.iter_chunked(1024):
                    f.write(chunk)
        print(f"Downloaded: {filename}")
    else:
        print(f"Skipping: {filename} (already exists)")


def parse_m3u8(content, base_url):
    segments = []
    for line in content.split('\n'):
        if line.endswith('.ts'):
            segments.append(urljoin(base_url, line.strip()))
    return segments


async def download_segments(segments, output_dir):
    semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent downloads

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i, segment_url in enumerate(segments):
            tasks.append(asyncio.create_task(download_file_with_semaphore(
                session, segment_url, os.path.join(output_dir, f'segment_{i:03d}.ts'), semaphore
            )))
        await asyncio.gather(*tasks)


async def download_file_with_semaphore(session, url, filename, semaphore):
    async with semaphore:  # Acquire the semaphore before downloading
        await download_file(session, url, filename)


def concatenate_segments(input_dir, output_dir, output_file):
    segment_list = os.path.join(input_dir, 'segment_list.txt')
    with open(segment_list, 'w') as f:
        for filename in sorted(os.listdir(input_dir)):
            if filename.endswith('.ts'):
                f.write(f"file '{output_dir}\\{filename}'\n")

    ffmpeg_cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', segment_list,
        '-fflags', '+genpts+igndts',  # Add this line to force generation of PTS
        '-c', 'copy',
        output_file
    ]

    subprocess.run(ffmpeg_cmd, check=True)


async def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Download and concatenate video segments from an m3u8 URL.")
    parser.add_argument('m3u8_url', help="The m3u8 URL to download video segments from")
    parser.add_argument('output_file', help="The name of the output file (e.g., output.mp4)")

    # Parse arguments
    args = parser.parse_args()

    m3u8_url = args.m3u8_url  # Get the m3u8 URL from the command line
    output_file = args.output_file  # Get the output file name from the command line
    base_url = m3u8_url.rsplit('/', 1)[0] + '/'
    output_dir = 'video_segments'

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Download m3u8 file
    print("Downloading m3u8 file...")
    async with aiohttp.ClientSession() as session:
        async with session.get(m3u8_url) as response:
            m3u8_content = await response.text()

    # Parse m3u8 file
    print("Parsing m3u8 file...")
    segments = parse_m3u8(m3u8_content, base_url)

    # Download segments concurrently (max 5 at a time)
    print("Downloading video segments concurrently (max 5 at a time)...")
    await download_segments(segments, output_dir)

    # Concatenate segments
    print("Concatenating segments...")
    concatenate_segments(output_dir, output_dir, output_file)

    print(f"Video download and conversion complete. Output file: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
content_copy
