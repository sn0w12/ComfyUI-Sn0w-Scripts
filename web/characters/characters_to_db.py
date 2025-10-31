import json
import sqlite3


def extract_series_name(character_name):
    """Extract series name from character name."""
    if not character_name or "(" not in character_name:
        return ""
    last_open = character_name.rfind("(")
    last_close = character_name.rfind(")")
    if last_open != -1 and last_close > last_open:
        return character_name[last_open + 1 : last_close].strip()
    return ""


# Load the JSON data
with open("characters.json", "r") as f:
    data = json.load(f)

# Create SQLite database
conn = sqlite3.connect("characters.db")
cursor = conn.cursor()

# Create table with all columns
cursor.execute("""
CREATE TABLE IF NOT EXISTS characters (
    name TEXT PRIMARY KEY,
    gender TEXT,
    series TEXT,
    associated_string TEXT,
    prompt TEXT,
    clothing_tags TEXT,
    is_custom INTEGER DEFAULT 0
)
""")

# Create indexes
cursor.execute("CREATE INDEX IF NOT EXISTS idx_series ON characters(series)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_custom ON characters(is_custom)")

# Insert data
for name, info in data.items():
    series = info.get("series", extract_series_name(name)).lower()
    associated_string = info.get("associated_string", "")
    prompt = info.get("prompt", "")
    clothing_tags = info.get("clothing_tags", "")
    gender = info.get("gender", "")
    cursor.execute(
        """
    INSERT OR REPLACE INTO characters (name, gender, series, associated_string, prompt, clothing_tags, is_custom)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (name, gender, series, associated_string, prompt, clothing_tags, 0),
    )

# Commit and close
conn.commit()
conn.close()

print("Database created and data inserted.")
