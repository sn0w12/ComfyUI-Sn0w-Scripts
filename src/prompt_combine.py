import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Set, Tuple
from ..sn0w import ConfigReader, Logger


@dataclass
class Tag:
    """Represents a single tag with its metadata."""

    text: str
    in_parentheses: bool = False
    parentheses_group_id: Optional[int] = None
    strength: Optional[float] = None

    def __hash__(self):
        return hash(self.text)

    def __eq__(self, other):
        if isinstance(other, Tag):
            return self.text == other.text
        return False


class CombineStringNode:
    logger = Logger()

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

    def parse_string_to_tags(self, input_string: str, separator: str) -> List[Tag]:
        """Parse an input string into a list of Tag objects."""
        if not input_string or input_string == "None":
            return []

        tags: List[Tag] = []
        # Pattern to match non-escaped parentheses with optional strength
        # Matches: (content) or (content:1.1) but not \(content\)
        paren_pattern = re.compile(r"(?<!\\)\(([^()]+?)(?::(\d+(?:\.\d+)?))?\)(?!\\)")

        # Track position in string
        last_pos = 0

        for match in paren_pattern.finditer(input_string):
            # Add any plain text before this parentheses group
            plain_text = input_string[last_pos : match.start()].strip()
            if plain_text:
                for tag_text in plain_text.split(separator):
                    tag_text = tag_text.strip()
                    if tag_text:
                        tags.append(Tag(text=tag_text, in_parentheses=False))

            # Process the parenthesized content
            content = match.group(1)
            strength_str = match.group(2)
            strength = float(strength_str) if strength_str else None

            # Generate a unique group ID for this parentheses group
            group_id = len([t for t in tags if t.in_parentheses]) + 1

            # Split the content by separator and create tags
            for tag_text in content.split(separator):
                tag_text = tag_text.strip()
                if tag_text:
                    tags.append(
                        Tag(text=tag_text, in_parentheses=True, parentheses_group_id=group_id, strength=strength)
                    )

            last_pos = match.end()

        # Add any remaining plain text after the last parentheses
        remaining_text = input_string[last_pos:].strip()
        if remaining_text:
            for tag_text in remaining_text.split(separator):
                tag_text = tag_text.strip()
                if tag_text:
                    tags.append(Tag(text=tag_text, in_parentheses=False))

        return tags

    def deduplicate_tags(self, tags: List[Tag], preserve_parentheses: bool = True) -> List[Tag]:
        """Remove duplicate tags while preserving order and optionally parentheses."""
        seen_texts: Set[str] = set()
        unique_tags: List[Tag] = []

        for tag in tags:
            # If tag is in parentheses and we're preserving them, always keep it
            if preserve_parentheses and tag.in_parentheses:
                unique_tags.append(tag)
            # Otherwise only add if we haven't seen this text before
            elif tag.text not in seen_texts:
                seen_texts.add(tag.text)
                unique_tags.append(tag)

        return unique_tags

    def simplify_tags(self, tags: List[Tag]) -> Tuple[List[Tag], List[Tag]]:
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
        tag_map: Dict[Tag, Tag] = {}
        for tag in tags:
            for potential_superior in tags:
                if tag.text in potential_superior.text and tag.text != potential_superior.text:
                    tag_map[tag] = potential_superior

        # Check global keep conditions
        all_tag_texts = [tag.text for tag in tags]
        global_keep_conditions = {
            keyword: any(keep_phrase in all_tag_texts for keep_phrase in conditions["keep"])
            for keyword, conditions in special_phrases.items()
        }

        # Identify non-removable tags (those that match remove phrases)
        non_removable_tags: Set[Tag] = {
            tag
            for tag in tags
            for keyword, conditions in special_phrases.items()
            if any(remove_phrase in tag.text for remove_phrase in conditions["remove"])
        }

        final_tags: List[Tag] = []
        removed_tags: List[Tag] = []

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
                    keyword in tag.text
                    and not global_keep_conditions[keyword]
                    and any(remove_phrase in t.text for t in tags for remove_phrase in conditions["remove"])
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

    def combine_parentheses_groups(self, tags: List[Tag]) -> List[Tag]:
        """Combine tags that belong to the same parentheses group."""
        # Group tags by their parentheses group ID
        grouped: Dict[Optional[int], List[Tag]] = {}
        non_paren_tags: List[Tag] = []

        for tag in tags:
            if tag.in_parentheses and tag.parentheses_group_id is not None:
                if tag.parentheses_group_id not in grouped:
                    grouped[tag.parentheses_group_id] = []
                grouped[tag.parentheses_group_id].append(tag)
            else:
                non_paren_tags.append(tag)

        # Combine groups with the same strength
        strength_groups: Dict[Optional[float], List[Tag]] = {}
        result_tags: List[Tag] = []

        for group_id, group_tags in grouped.items():
            if not group_tags:
                continue

            strength = group_tags[0].strength
            if strength not in strength_groups:
                strength_groups[strength] = []
            strength_groups[strength].extend(group_tags)

        # Create combined tags for each strength group
        for strength, group_tags in strength_groups.items():
            # All tags in this group share the same strength and should be in parentheses
            for tag in group_tags:
                result_tags.append(tag)

        # Add non-parenthesized tags
        result_tags.extend(non_paren_tags)

        return result_tags

    def format_tags_for_animagine(self, tags: List[Tag]) -> List[Tag]:
        """Reorder tags to put numeric tags (e.g., '2girls') first for Animagine format."""
        animagine_formatting = ConfigReader.get_setting("sn0w.PromptFormat", False)
        if not animagine_formatting:
            return tags

        numeric_tag_pattern = re.compile(r"\b\d+\+?(girls?|boys?)\b")

        numeric_tags = [tag for tag in tags if numeric_tag_pattern.match(tag.text)]
        non_numeric_tags = [tag for tag in tags if not numeric_tag_pattern.match(tag.text)]

        return numeric_tags + non_numeric_tags

    def apply_implied_tags(self, tags: List[Tag]) -> List[Tag]:
        """Add implied tags based on configuration."""
        implied_tags_config = str(ConfigReader.get_setting("sn0w.ImpliedTags", "")).split("\n")
        tag_texts = [tag.text for tag in tags]
        new_tags = list(tags)

        for pair in implied_tags_config:
            parts = pair.split(":")
            if len(parts) != 2:
                continue

            key, value = parts[0].strip(), parts[1].strip()
            if key in tag_texts and value not in tag_texts:
                # Insert the implied tag immediately after the key tag
                for idx, tag in enumerate(new_tags):
                    if tag.text == key:
                        new_tags.insert(idx + 1, Tag(text=value, in_parentheses=False))
                        break

        return new_tags

    def tags_to_string(self, tags: List[Tag], separator: str) -> str:
        """Convert a list of Tag objects back to a formatted string."""
        # Group tags by their parentheses group and strength
        strength_groups: Dict[Optional[float], List[str]] = {}
        plain_tags: List[str] = []

        for tag in tags:
            if tag.in_parentheses:
                key = tag.strength
                if key not in strength_groups:
                    strength_groups[key] = []
                strength_groups[key].append(tag.text)
            else:
                plain_tags.append(tag.text)

        # Build the result string
        result_parts: List[str] = []

        # Add parenthesized groups
        for strength, group_texts in strength_groups.items():
            content = separator.join(group_texts)
            if strength is not None:
                result_parts.append(f"({content}:{strength})")
            else:
                result_parts.append(f"({content})")

        # Add plain tags
        result_parts.extend(plain_tags)

        # Clean up multiple separators
        result = separator.join(result_parts)
        escaped_sep = re.escape(separator)
        pattern = rf"(?:\s*{escaped_sep}\s*)+"
        result = re.sub(pattern, separator, result)
        result = result.strip(separator + " ")

        return result

    def combine_string(self, separator: str, simplify: bool, **kwargs) -> Tuple[str, str]:
        """Main function to combine input strings into a single prompt."""
        # Collect input strings
        input_strings = [kwargs.get(f"string_{char}", "").strip() for char in ["a", "b", "c", "d"]]
        input_strings = [s for s in input_strings if s and s != "None"]

        if not input_strings:
            return ("", "")

        # Parse all input strings to Tag objects
        all_tags: List[Tag] = []
        for input_string in input_strings:
            tags = self.parse_string_to_tags(input_string, separator)
            all_tags.extend(tags)

        # Deduplicate tags (preserve parenthesized tags)
        all_tags = self.deduplicate_tags(all_tags, preserve_parentheses=True)

        # Apply implied tags
        all_tags = self.apply_implied_tags(all_tags)

        # Simplify tags if requested
        removed_tags: List[Tag] = []
        if simplify:
            all_tags, removed_tags = self.simplify_tags(all_tags)
            all_tags = self.combine_parentheses_groups(all_tags)

        # Format for Animagine if enabled
        all_tags = self.format_tags_for_animagine(all_tags)

        # Convert back to string
        final_string = self.tags_to_string(all_tags, separator)
        removed_string = separator.join([tag.text for tag in removed_tags])

        return (final_string, removed_string)
