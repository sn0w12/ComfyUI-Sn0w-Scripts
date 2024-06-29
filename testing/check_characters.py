import xml.etree.ElementTree as ET
from difflib import get_close_matches

import csv
import json
import os
import time
import requests

# Constants
CHARACTER_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../web/settings", "characters.json"))
CUSTOM_CHARACTER_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../web/settings", "custom_characters.json"))
TAGS_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "danbooru-tags.csv"))
LOG_FILE_PATH = os.path.abspath("testing/success_log.txt")
BASE_URL = "https://gelbooru.com/index.php?page=dapi&s=tag&q=index&name="
REQUEST_DELAY = 0.5  # Delay between requests in seconds
MIN_USES = 100
SIMILARITY_THRESHOLD = 0.9

RED_TEXT = "\033[0;31m"
GREEN_TEXT = "\033[0;32m"
YELLOW_TEXT = "\033[0;33m"
RESET_TEXT = "\033[0m"


def validate_character(character):
    # Check if all required fields exist and are not None
    required_fields = ["name", "associated_string", "prompt"]
    for field in required_fields:
        if not (field in character and character[field] is not None):
            return False
    return True


def load_tags(file_path):
    tags = {}
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            tags[row[0]] = int(row[1])
    return tags


def normalize_tag(tag):
    # Normalize tag by replacing spaces with underscores and removing escape characters
    return tag.replace(" ", "_").replace("\\", "").strip()


def check_tags_exist(tags, tag_list):
    missing_tags = []
    for tag in tag_list:
        normalized_tag = normalize_tag(tag)
        if normalized_tag not in tags:
            missing_tags.append(normalized_tag)
    return missing_tags


def suggest_close_tags(tags, missing_tags, n=3, threshold=0.8):
    tag_keys = list(tags.keys())
    suggestions = {}
    for tag in missing_tags:
        normalized_tag = normalize_tag(tag)
        close_matches = get_close_matches(normalized_tag, tag_keys, n=n, cutoff=threshold)
        if close_matches:
            suggestions[tag] = close_matches
    return suggestions


# Load the JSON data from the character file
with open(CHARACTER_FILE_PATH, "r", encoding="utf-8") as file:
    characters_data = json.load(file)

# Load or initialize the custom character file
if os.path.exists(CUSTOM_CHARACTER_FILE_PATH):
    with open(CUSTOM_CHARACTER_FILE_PATH, "r", encoding="utf-8") as file:
        custom_characters_data = json.load(file)
else:
    custom_characters_data = []

# Load the tags data
tags_data = load_tags(TAGS_FILE_PATH)

# Ensure the log file directory exists
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

# Check and handle MIN_USES change
current_min_uses = None
if os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, "r", encoding="utf-8") as log_file:
        first_line = log_file.readline().strip()
        if first_line.isdigit():
            current_min_uses = int(first_line)

# If MIN_USES has changed, clear the log file and start fresh
if current_min_uses != MIN_USES:
    with open(LOG_FILE_PATH, "w", encoding="utf-8") as log_file:
        log_file.write(f"{MIN_USES}\n")
        print("MIN_USES has changed, re-checking entire character list.")
    successful_tags = set()
else:
    # Load successfully logged tags to avoid redundant requests
    successful_tags = set()
    with open(LOG_FILE_PATH, "r", encoding="utf-8") as log_file:
        next(log_file)  # Skip the first line with MIN_USES
        successful_tags = {line.split("[:]")[0].strip() for line in log_file}

low_use_characters = []  # List to store characters with too few uses
total_valid_characters = 0  # Counter for total valid characters
good_characters_count = 0  # Counter for good characters

print(
    f"{GREEN_TEXT}Note:{RESET_TEXT} Warnings for tags do not mean they should be removed, it is just there to make sure there are no misspelt tags"
)

# Record successful checks and track low use characters
with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
    if current_min_uses != MIN_USES:
        log_file.seek(0, os.SEEK_END)  # Move to the end of the file after header
    for character in characters_data:
        if validate_character(character):
            total_valid_characters += 1
            associated_tags = [tag.strip() for tag in character["associated_string"].split(",")]
            prompt_tags = [tag.strip() for tag in character["prompt"].split(",")]

            missing_tags = check_tags_exist(tags_data, prompt_tags)
            if missing_tags:
                print(
                    f"{YELLOW_TEXT}Warning: The following tags for character '{character['name']}' do not exist in TAGS_FILE_PATH: {', '.join(missing_tags)}{RESET_TEXT}"
                )
                suggestions = suggest_close_tags(tags_data, missing_tags, threshold=SIMILARITY_THRESHOLD)
                for tag, matches in suggestions.items():
                    print(f"Suggestions for '{tag}': {', '.join(matches)}")

            normalized_tag = normalize_tag(associated_tags[0])

            if normalized_tag in successful_tags:
                good_characters_count += 1
                continue

            url = f"{BASE_URL}{normalized_tag}"
            response = requests.get(url, timeout=10)
            time.sleep(REQUEST_DELAY)

            if response.status_code == 200:
                root = ET.fromstring(response.content)
                if root is not None:
                    try:
                        tag_count = int(root.find("tag").find("count").text)
                        if tag_count < MIN_USES:
                            print(f"{RED_TEXT}{normalized_tag} DOES NOT HAVE ENOUGH USES: {tag_count}{RESET_TEXT}")
                            low_use_characters.append(character)
                        else:
                            print(f"{GREEN_TEXT}{normalized_tag} is good: {tag_count}{RESET_TEXT}")
                            log_file.write(f"{normalized_tag}[:] {tag_count}\n")
                            good_characters_count += 1
                    except AttributeError:
                        print(f"Could not find count for {normalized_tag}")
                else:
                    print(f"No root element found for {normalized_tag}")
            else:
                print(f"Failed to retrieve data for {normalized_tag}: {response.status_code}")
        else:
            print(f"Character not formatted correctly: {character}")

if total_valid_characters > 0:
    good_percentage = (good_characters_count / total_valid_characters) * 100
    print(f"{good_percentage:.2f}% of characters are valid.")
else:
    print("No valid characters found.")

# Prompt user and handle character transfer
if low_use_characters:
    user_input = input("Do you want to add characters with too few uses to 'custom_characters.json'? [Y/n]: ")
    if user_input.lower() == "y":
        # Remove low use characters from main data and add to custom characters
        characters_data = [character for character in characters_data if character not in low_use_characters]
        custom_characters_data.extend(low_use_characters)

        # Save the updated data back to files
        with open(CHARACTER_FILE_PATH, "w", encoding="utf-8") as file:
            json.dump(characters_data, file, indent=4)
        with open(CUSTOM_CHARACTER_FILE_PATH, "w", encoding="utf-8") as file:
            json.dump(custom_characters_data, file, indent=4)
        print("Characters transferred successfully.")
