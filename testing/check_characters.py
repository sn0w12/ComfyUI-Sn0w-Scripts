import json
import os
import time
import requests
import xml.etree.ElementTree as ET

# Constants
CHARACTER_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'characters.json'))
LOG_FILE_PATH = os.path.abspath('testing/success_log.txt')
BASE_URL = "https://gelbooru.com/index.php?page=dapi&s=tag&q=index&name="
REQUEST_DELAY = 0.5  # Delay between requests in seconds
MIN_USES = 100

RED_TEXT = "\033[0;31m"
GREEN_TEXT = "\033[0;32m"

# Load the JSON data from the character file
with open(CHARACTER_FILE_PATH, 'r') as file:
    data = json.load(file)

# Ensure the log file directory exists
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

# Check and handle MIN_USES change
current_min_uses = None
if os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'r') as log_file:
        first_line = log_file.readline().strip()
        if first_line.isdigit():
            current_min_uses = int(first_line)

# If MIN_USES has changed, clear the log file and start fresh
if current_min_uses != MIN_USES:
    with open(LOG_FILE_PATH, 'w') as log_file:
        log_file.write(f"{MIN_USES}\n")
        print("MIN_USES has changed, re-checking entire character list.")
    successful_tags = set()
else:
    # Load successfully logged tags to avoid redundant requests
    successful_tags = set()
    with open(LOG_FILE_PATH, 'r') as log_file:
        next(log_file)  # Skip the first line with MIN_USES
        successful_tags = {line.split('[:]')[0].strip() for line in log_file}

# Record successful checks
with open(LOG_FILE_PATH, 'a') as log_file:
    if current_min_uses != MIN_USES:
        log_file.seek(0, os.SEEK_END)  # Move to the end of the file after header
    for character in data:
        tag = character['associated_string'].split(',')[0].replace(' ', '_').replace('\\', '').strip()

        if tag in successful_tags:
            continue

        url = f"{BASE_URL}{tag}"
        response = requests.get(url)
        time.sleep(REQUEST_DELAY)

        if response.status_code == 200:
            root = ET.fromstring(response.content)
            if root is not None:
                try:
                    tag_count = int(root.find('tag').find('count').text)
                    if tag_count < MIN_USES:
                        print(f"{RED_TEXT}{tag} DOES NOT HAVE ENOUGH USES: {tag_count}")
                    else:
                        print(f"{GREEN_TEXT}{tag} is good: {tag_count}")
                        log_file.write(f"{tag}[:] {tag_count}\n")
                except AttributeError:
                    print(f"Could not find count for {tag}")
            else:
                print(f"No root element found for {tag}")
        else:
            print(f"Failed to retrieve data for {tag}: {response.status_code}")
