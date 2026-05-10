from typing import Dict, Set, Tuple
from ..sn0w import ConfigReader, Logger


TokenStrength = tuple[str, float]
TokenStrengthList = list[TokenStrength]


class Tokens:
    def __init__(self, temp_value=-9999.0) -> None:
        self.temp_value = temp_value

    def _should_replace(
        self,
        current: float,
        new: float,
    ) -> bool:
        # Special handling for temp, more important than <1.0.
        if current == self.temp_value:
            return new > 1.0
        if current == 1.0:
            return new == self.temp_value or new >= 1.0

        return new > current

    def deduplicate(
        self,
        tokens: TokenStrengthList,
    ) -> TokenStrengthList:
        best: dict[str, float] = {}

        for token, strength in tokens:
            current = best.get(token)

            if current is None or self._should_replace(current, strength):
                best[token] = strength

        return list(best.items())

    def _ends_nesting(self, word: str) -> bool:
        return word.endswith(")") and not word.endswith(r"\)")

    def _parse_strength(self, word: str) -> float | None:
        if not self._ends_nesting(word):
            return None

        parts = word.split(":")
        if len(parts) <= 1:
            return None

        return float(parts[-1].strip(")"))

    def tokenize(self, input: str, delimiter=",") -> TokenStrengthList:
        if len(delimiter) != 1:
            raise ValueError("Delimiter must be a single character")

        token_tree: dict[int, list[str]] = {0: []}
        strength_tokens: TokenStrengthList = []

        current_nesting = 0
        word = ""

        for index, char in enumerate(input):
            is_last = index == len(input) - 1

            if is_last:
                word += char

            if char == delimiter or is_last:
                word = word.strip()
                token_tree[current_nesting].append(word)

                end_nesting = self._ends_nesting(word)
                strength = self._parse_strength(word)

                for token in token_tree[current_nesting]:
                    if strength is not None:
                        strength_tokens.append((token.replace(f":{strength})", "").strip(), strength))
                    elif end_nesting:
                        strength_tokens.append((token.strip(")"), self.temp_value))

                if end_nesting:
                    token_tree[current_nesting] = []
                    current_nesting -= 1

                word = ""
                continue

            if char == "(" and not word.endswith("\\"):
                current_nesting += 1
                if token_tree.get(current_nesting) is None:
                    token_tree[current_nesting] = []

                continue

            word += char

        for token in token_tree[0]:
            strength_tokens.append((token, 1.0))

        return strength_tokens

    def merge(self, *token_lists: TokenStrengthList) -> TokenStrengthList:
        return self.deduplicate([token for token_list in token_lists for token in token_list])

    def sort(self, tokens: TokenStrengthList) -> TokenStrengthList:
        def sort_strength(value: float) -> float:
            if value == self.temp_value:
                return 1.000001
            return value

        return sorted(tokens, key=lambda t: sort_strength(t[1]), reverse=True)

    def to_str(self, tokens: TokenStrengthList, delimiter=", ") -> str:
        token_dict: dict[float, list[str]] = {}
        for token, strength in tokens:
            token_dict.setdefault(strength, []).append(token)

        parts: list[str] = []
        for key in token_dict:
            words = token_dict[key]
            chunk = delimiter.join(words)

            if key == 1.0:
                parts.append(chunk)
                continue
            if key == self.temp_value:
                parts.append(f"({chunk})")
                continue

            parts.append(f"({chunk}:{key})")

        return delimiter.join(parts)


class CombineStringNode:
    logger = Logger()
    parser = Tokens()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "separator": ("STRING", {"default": ", "}),
                "simplify": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "string_a": ("STRING", {"default": ""}),
                "string_b": ("STRING", {"default": ""}),
                "string_c": ("STRING", {"default": ""}),
                "string_d": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = (
        "STRING",
        "STRING",
    )
    RETURN_NAMES = (
        "PROMPT",
        "REMOVED_TAGS",
    )
    FUNCTION = "combine_string"
    CATEGORY = "sn0w"

    def parse_string_to_tags(self, input_string: str, separator: str) -> TokenStrengthList:
        """Parse an input string into a list of Tag objects."""
        if not input_string or input_string == "None":
            return []

        return self.parser.tokenize(input_string, delimiter=separator.strip())

    def simplify_tags(self, tags: TokenStrengthList) -> Tuple[TokenStrengthList, TokenStrengthList]:
        """Simplify tags by removing redundant or conflicting tags."""
        remove_eyes = [
            "covering eyes",
            "over eyes",
            "covered eyes",
            "covering face",
            "covering own eyes",
            "facing away",
            "blindfold",
            "head out of frame",
            "face in pillow",
        ]
        remove_face = ["facing away"]
        keep_face = ["looking at viewer"]

        special_phrases = {
            "eye": {"remove": remove_eyes, "keep": keep_face},
            "sclera": {"remove": remove_eyes, "keep": keep_face},
            "mouth": {"remove": remove_face, "keep": keep_face},
            "teeth": {"remove": remove_face, "keep": keep_face},
        }

        # Build tag map for substring detection
        tag_map: Dict[TokenStrength, TokenStrength] = {}
        for tag in tags:
            for potential_superior in tags:
                if tag[0] in potential_superior[0] and tag[0] != potential_superior[0]:
                    tag_map[tag] = potential_superior

        # Check global keep conditions
        all_tag_texts = [tag[0] for tag in tags]
        global_keep_conditions = {
            keyword: any(keep_phrase in all_tag_texts for keep_phrase in conditions["keep"])
            for keyword, conditions in special_phrases.items()
        }

        # Identify non-removable tags (those that match remove phrases)
        non_removable_tags: Set[TokenStrength] = {
            tag
            for tag in tags
            for keyword, conditions in special_phrases.items()
            if any(remove_phrase in tag[0] for remove_phrase in conditions["remove"])
        }

        final_tags: TokenStrengthList = []
        removed_tags: TokenStrengthList = []

        for tag in tags:
            # Check if this tag has a superior tag
            superior_tag = tag_map.get(tag)
            if superior_tag and superior_tag not in final_tags:
                removed_tags.append(tag)
                continue

            # Check special phrase rules
            should_remove_tag = False
            for keyword, conditions in special_phrases.items():
                if (
                    keyword in tag[0]
                    and not global_keep_conditions[keyword]
                    and any(remove_phrase in t[0] for t in tags for remove_phrase in conditions["remove"])
                    and tag not in non_removable_tags
                ):
                    should_remove_tag = True
                    break

            if should_remove_tag:
                removed_tags.append(tag)
            else:
                # Avoid adding duplicates
                if tag not in final_tags:
                    final_tags.append(tag)

        return final_tags, removed_tags

    def apply_implied_tags(self, tags: TokenStrengthList) -> TokenStrengthList:
        """Add implied tags based on configuration."""
        implied_tags_config = str(ConfigReader.get_setting("sn0w.ImpliedTags", "")).split("\n")
        tag_texts = [tag[0] for tag in tags]
        new_tags = list(tags)

        for pair in implied_tags_config:
            parts = pair.split(":")
            if len(parts) != 2:
                continue

            key, value = parts[0].strip(), parts[1].strip()
            if key in tag_texts and value not in tag_texts:
                # Insert the implied tag immediately after the key tag
                for idx, tag in enumerate(new_tags):
                    if tag[0] == key:
                        new_tags.insert(idx + 1, (value, 1.0))
                        break

        return new_tags

    def combine_string(self, separator: str, simplify: bool, **kwargs) -> Tuple[str, str]:
        """Main function to combine input strings into a single prompt."""
        # Collect input strings
        input_strings = [kwargs.get(f"string_{char}", "").strip() for char in ["a", "b", "c", "d"]]
        input_strings = [s for s in input_strings if s and s != "None"]

        if not input_strings:
            return ("", "")

        # Parse all input strings to Tag objects
        tag_lists: list[TokenStrengthList] = []
        for input_string in input_strings:
            tag_lists.append(self.parse_string_to_tags(input_string, separator))

        all_tags = self.parser.merge(*tag_lists)
        all_tags = self.apply_implied_tags(all_tags)

        # Simplify tags if requested
        removed_tags: TokenStrengthList = []
        if simplify:
            all_tags, removed_tags = self.simplify_tags(all_tags)

        # Convert back to string
        final_string = self.parser.to_str(all_tags, separator)
        removed_string = separator.join([tag[0] for tag in removed_tags])

        return (final_string, removed_string)
