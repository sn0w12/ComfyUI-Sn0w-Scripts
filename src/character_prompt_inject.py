import re

from ..sn0w import ConfigReader
from .character_select import CharacterSelectNode

GENERIC_TAGS = {
    "1girl",
    "1boy",
    "1other",
    "2girls",
    "2boys",
    "multiple girls",
    "multiple boys",
    "solo",
    "solo focus",
    "looking at viewer",
    "full body",
    "upper body",
    "lower body",
    "portrait",
    "close-up",
    "from side",
    "from behind",
    "from above",
    "from below",
    "simple background",
    "white background",
    "transparent background",
    "highres",
    "absurdres",
    "commentary",
    "artist name",
    "signature",
    "watermark",
    "sleeveless",
    "bare shoulders",
    "open clothes",
    "collarbone",
}

COLOR_WORDS = {
    "black",
    "white",
    "red",
    "blue",
    "green",
    "yellow",
    "orange",
    "purple",
    "pink",
    "brown",
    "grey",
    "gray",
    "blonde",
    "blond",
    "silver",
    "aqua",
    "cyan",
    "teal",
    "magenta",
    "maroon",
    "navy",
    "violet",
    "indigo",
    "turquoise",
    "lavender",
    "gold",
    "golden",
    "copper",
    "scarlet",
    "crimson",
    "emerald",
    "azure",
    "multicolored",
    "streaked",
    "gradient",
    "rainbow",
    "dark",
    "light",
    "pale",
}

ACCESSORY_HINTS = (
    "ornament",
    "hairband",
    "hairclip",
    "hair clip",
    "headband",
    "hair bow",
    "ribbon",
    "bow",
    "earrings",
    "jewelry",
    "glasses",
    "headphones",
    "hat",
    "cap",
    "mask",
    "crown",
    "tiara",
    "veil",
)

HAIR_LENGTHS = {
    "short hair": "short",
    "medium hair": "medium",
    "long hair": "long",
    "very long hair": "very long",
    "absurdly long hair": "absurdly long",
}

HAIR_TEXTURES = {
    "curly hair": "curly",
    "wavy hair": "wavy",
    "straight hair": "straight",
    "messy hair": "messy",
    "spiked hair": "spiked",
    "drill hair": "drill",
    "flipped hair": "flipped",
}

HAIR_STYLES = {
    "ponytail": "tied in a ponytail",
    "side ponytail": "tied in a side ponytail",
    "twintails": "tied in twintails",
    "braid": "tied in a braid",
    "twin braids": "tied in twin braids",
    "hair bun": "tied in a bun",
    "double bun": "tied in double buns",
    "hair up": "tied up",
    "bob cut": "cut in a bob",
    "hime cut": "with a hime cut",
}

SUBJECT_RE = re.compile(
    r"\b(?P<article>a|an|the)\s+"
    r"(?P<modifiers>(?:(?!(?:a|an|the|of|with|in|on|at|by|and|or)\b)[a-z][\w'-]*\s+){0,3})"
    r"(?P<noun>girl|boy|woman|man|person|character|figure|lady|guy|child|teenager|adult|princess|knight|warrior|witch|soldier)\b",
    re.IGNORECASE,
)

GERUND_RE = re.compile(r"[A-Za-z]+ing\b")
GENERIC_TAG_RE = re.compile(r"\d+(?:girl|boy|other)s?$")
PLACEHOLDER_RE = re.compile(r"\{\{\s*char([1-4])\s*\}\}", re.IGNORECASE)
CHARACTER_SLOTS = 4

SERIES_PARTICLES = {
    "no",
    "to",
    "wa",
    "ga",
    "ni",
    "de",
    "o",
    "e",
    "ya",
    "na",
    "mo",
    "ka",
    "wo",
    "of",
    "the",
    "and",
    "in",
    "on",
    "at",
    "for",
    "a",
    "an",
}


class CharacterPromptInjectNode:
    """
    Injects up to four selected characters into a natural language prompt.
    """

    db = CharacterSelectNode.db

    @classmethod
    def INPUT_TYPES(cls):
        character_names = ["None"] + cls.db.get_character_names(
            include_default=not ConfigReader.get_setting("sn0w.CharacterSettings.DisableDefaultCharacters", False),
        )

        required = {"prompt": ("STRING", {"default": "", "multiline": True})}
        for index in range(1, CHARACTER_SLOTS + 1):
            required[f"character_{index}"] = (character_names + ["SN0W_CHARACTER_SELECTOR"],)

        return {
            "required": required,
        }

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("PROMPT",)
    FUNCTION = "inject_character"
    CATEGORY = "sn0w"

    def inject_character(self, prompt, character_1, character_2, character_3, character_4):
        prompt = (prompt or "").strip()
        slot_values = (character_1, character_2, character_3, character_4)
        characters = [self._resolve_character(character) for character in slot_values]

        if PLACEHOLDER_RE.search(prompt):
            return (self._replace_placeholders(prompt, characters),)

        character_data = characters[0]
        if character_data is None:
            return (prompt,)

        name, series, tag_text, gender = character_data
        if self._mentions(prompt, name):
            return (prompt,)

        label = self._label(name, series)
        features = self._features(self._parse_tags(tag_text), prompt)

        if not prompt:
            return (self._full_description(label, gender, features)[0],)

        match = SUBJECT_RE.search(prompt)
        if match:
            return (self._inject_at_subject(prompt, match, name, label, features, gender),)

        return (self._inject_at_end(prompt, label, features),)

    def _replace_placeholders(self, prompt, characters):
        described = set()

        def replace(match):
            index = int(match.group(1)) - 1
            character_data = characters[index]
            if character_data is None:
                return match.group(0)

            name, series, tag_text, gender = character_data
            if name.lower() in described:
                return name

            after = prompt[match.end() :]
            if re.match(r"\s*['’]s\b", after):
                return name

            described.add(name.lower())
            label = self._label(name, series)
            features = self._features(self._parse_tags(tag_text), prompt)
            description, is_appositive = self._full_description(label, gender, features)
            if is_appositive and after.strip() and not re.match(r"\s*[,.;:!?\"”’)\]]", after):
                description += ","
            return description

        return PLACEHOLDER_RE.sub(replace, prompt)

    def _full_description(self, label, gender, features):
        subject = {"1girl": "a girl", "1boy": "a boy"}.get(gender, "")
        if not subject:
            return self._describe(label, features), False
        return f"{label}, {self._describe(subject, features)}", True

    def _label(self, name, series):
        series = self._title_series(series)
        if not series or series.lower() in ("original", "custom"):
            return name
        return f"{name} from {series}"

    def _title_series(self, series):
        words = series.replace("_", " ").split()
        return " ".join(
            word.lower() if index and word.lower() in SERIES_PARTICLES else word[:1].upper() + word[1:]
            for index, word in enumerate(words)
        )

    def _resolve_character(self, character):
        if character in (None, "", "None", "SN0W_CHARACTER_SELECTOR"):
            return None

        raw_name = self._clean_name(character)
        if not raw_name:
            return None

        db_character = self.db.get_character_by_name(raw_name)
        if db_character is None:
            return raw_name.title(), "", "", ""

        name = re.sub(r"\s*\([^)]*\)\s*$", "", db_character.name).strip().title()
        series = db_character.copyright[0] if db_character.copyright else ""
        return name, series, ", ".join(db_character.prompt), db_character.gender

    def _inject_at_subject(self, prompt, match, name, label, features, gender):
        after = prompt[match.end() :]
        if after.lstrip().startswith(("'", "’")):
            return prompt[: match.start()] + name + after

        article = match.group("article").lower()
        modifiers = re.sub(r"\s+", " ", match.group("modifiers")).strip()
        noun = self._adjust_noun(match.group("noun").lower(), gender)
        subject = " ".join(part for part in (article, modifiers, noun) if part)
        description = self._describe(subject, features)

        comma = ""
        if after.strip() and not re.match(r"\s*[,.;:!?]", after):
            comma = ","

        return prompt[: match.start()] + f"{label}, {description}{comma}" + after

    def _inject_at_end(self, prompt, label, features):
        description = self._describe(label, features)

        if GERUND_RE.match(prompt):
            return f"{description}, {prompt}"

        body = prompt.rstrip().rstrip(",;:")
        ending = ""
        match = re.search(r"([.!?])\s*$", body)
        if match:
            body = body[: match.start()]
            ending = match.group(1)

        return f"{body}, featuring {description}{ending}"

    def _describe(self, subject, features):
        if not features:
            return subject
        return f"{subject} with {self._join(features)}"

    def _features(self, tags, prompt):
        prompt_text = prompt.lower().replace("_", " ")
        hair = {"color": "", "length": "", "texture": "", "style": "", "details": []}
        eyes = ""
        other = []

        for tag in tags:
            if self._mentions(prompt_text, tag):
                continue

            lowered = tag.lower()
            if self._is_accessory(lowered):
                continue
            if self._is_hair(lowered):
                if lowered in HAIR_STYLES:
                    hair["style"] = hair["style"] or HAIR_STYLES[lowered]
                elif lowered in HAIR_LENGTHS:
                    hair["length"] = hair["length"] or HAIR_LENGTHS[lowered]
                elif lowered in HAIR_TEXTURES:
                    hair["texture"] = hair["texture"] or HAIR_TEXTURES[lowered]
                elif self._has_color(tag):
                    hair["color"] = hair["color"] or lowered.replace("hair", "").strip()
                else:
                    hair["details"].append(tag)
            elif "eyes" in lowered:
                eyes = eyes or tag
            else:
                other.append(tag)

        parts = []
        hair_phrase = self._hair_phrase(hair)
        if hair_phrase:
            parts.append(hair_phrase)
        if eyes:
            parts.append(eyes)
        parts.extend(other)
        return parts

    def _hair_phrase(self, hair):
        base = " ".join(part for part in (hair["length"], hair["color"], hair["texture"]) if part)
        if base:
            base += " hair"

        phrase = base
        if hair["style"]:
            phrase = f"{phrase} {hair['style']}" if phrase else f"hair {hair['style']}"
        if hair["details"]:
            details = self._join(hair["details"])
            phrase = f"{phrase} with {details}" if phrase else details
        return phrase

    def _is_hair(self, lowered):
        return "hair" in lowered or lowered in HAIR_STYLES

    def _is_accessory(self, lowered):
        return bool(re.search(rf"\b(?:{'|'.join(ACCESSORY_HINTS)})\b", lowered))

    def _parse_tags(self, tag_text):
        tags = []
        seen = set()
        for tag in tag_text.split(","):
            tag = tag.replace("\\", "")
            tag = re.sub(r":\s*[-+]?[\d.]+\)?\s*$", "", tag).strip()
            tag = tag.strip("()").strip()
            tag = re.sub(r"\s+", " ", tag.replace("_", " "))
            lowered = tag.lower()
            if not tag or lowered in seen or lowered in GENERIC_TAGS or GENERIC_TAG_RE.fullmatch(lowered):
                continue
            seen.add(lowered)
            tags.append(tag)
        return tags

    def _clean_name(self, value):
        if not value:
            return ""
        # Widget values are "copyright|name" or "copyright|parent|child"; the selector's
        # CHARACTER NAME output is "(name, copyright:strength)".
        name = str(value).split("|")[-1].replace("\\", "").strip()
        name = name.split(",")[0].strip()
        name = re.sub(r":\s*[-+]?[\d.]+\s*\)\s*$", "", name).strip()
        if name.startswith("("):
            name = name[1:].strip()
        return name.replace("_", " ")

    def _adjust_noun(self, noun, gender):
        if gender == "1girl":
            return {"boy": "girl", "man": "woman", "guy": "girl"}.get(noun, noun)
        if gender == "1boy":
            return {"girl": "boy", "woman": "man", "lady": "man"}.get(noun, noun)
        return noun

    def _has_color(self, tag):
        return bool(set(re.findall(r"[a-z]+", tag.lower())) & COLOR_WORDS)

    def _mentions(self, text, phrase):
        return bool(re.search(rf"(?<!\w){re.escape(phrase.lower())}(?!\w)", text.lower()))

    def _join(self, items):
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} and {items[1]}"
        return ", ".join(items[:-1]) + f", and {items[-1]}"
