import xml.etree.ElementTree as ET
from difflib import get_close_matches
import csv
import json
import os
import time
import requests
import sys

# Constants
CHARACTER_FILE_PATH = os.getenv("CHARACTER_FILE_PATH", "web/settings/characters.json")
TAGS_FILE_PATH = os.getenv("TAGS_FILE_PATH", "testing/danbooru-tags.csv")
BASE_URL = "https://gelbooru.com/index.php?page=dapi&s=tag&q=index&name="
REQUEST_DELAY = 0.25  # Delay between requests in seconds
MIN_USES = int(os.getenv("MIN_USES", 100))
SIMILARITY_THRESHOLD = 0.9

RED_TEXT = "\033[0;31m"
GREEN_TEXT = "\033[0;32m"
YELLOW_TEXT = "\033[0;33m"
RESET_TEXT = "\033[0m"


def validate_character(character):
    required_fields = ["name", "associated_string", "prompt"]
    return all(field in character and character[field] is not None for field in required_fields)


def load_tags(file_path):
    tags = {}
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            tags[row[0]] = int(row[1])
    return tags


def normalize_tag(tag):
    return tag.replace(" ", "_").replace("\\", "").strip()


def check_tags_exist(tags, tag_list):
    missing_tags = [normalize_tag(tag) for tag in tag_list if normalize_tag(tag) not in tags]
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


with open(CHARACTER_FILE_PATH, "r", encoding="utf-8") as file:
    characters_data = json.load(file)

tags_data = load_tags(TAGS_FILE_PATH)

successful_tags = set()
low_use_characters = []
total_valid_characters = 0
good_characters_count = 0

print(
    f"{GREEN_TEXT}Note:{RESET_TEXT} Warnings for tags do not mean they should be removed, it is just there to make sure there are no misspelt tags"
)

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

if low_use_characters:
    print("Script failed due to low-use characters. Please run the script locally to address this issue.")
    sys.exit(1)  # Exit with a non-zero status code to indicate failure
