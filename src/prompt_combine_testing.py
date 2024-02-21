import re

def simplify_tags(tags_string):
    # dictionary defines categories with specific rules for removing or keeping tags.
    # remove contains phrases that, if found in a prompt, suggest the tag should be removed under certain conditions.
    # keep contains phrases that, if found in a prompt, indicate the tag should be kept.
    # if a remove tag is found and no keep tag is found, it will remove all mentions of the category except the tags found in remove.
    # keep always takes priority over remove, if any tag in keep is found nothing will be removed
    special_phrases = {
        'eye': {
            'remove': ['covering eyes', 'over eyes', 'covered eyes', 'covering face', 'covering own eyes', 'facing away'],
            'keep': ['looking at viewer']
        },
        'sclera': {
            'remove': ['covering eyes', 'over eyes', 'covered eyes', 'covering face', 'covering own eyes', 'facing away'],
            'keep': ['looking at viewer']
        },
        'mouth': {
            'remove': ['facing away'],
            'keep': ['looking at viewer']
        },
        'teeth': {
            'remove': ['facing away'],
            'keep': ['looking at viewer']
        },
    }

    # Regular expression to match parenthesized parts
    parenthesized_pattern = re.compile(r'\([^()]*\)')
    parenthesized_parts = []

    # Extract and temporarily remove parenthesized parts, storing their positions
    def extract_parenthesized(match):
        parenthesized_parts.append(match.group(0))
        return "\0"  # Use a unique placeholder to mark the position

    modified_tags_string = re.sub(parenthesized_pattern, extract_parenthesized, tags_string)

    # Split tags and initialize lists
    tags = [tag.strip() for tag in modified_tags_string.split(',')]
    final_tags = []
    removed_tags = []
    tag_map = {}

    # Mapping non-superior tags to their superior counterparts
    for tag in tags:
        for potential_superior in tags:
            if tag != potential_superior and tag in potential_superior:
                tag_parts = set(tag.split(' '))
                superior_parts = set(potential_superior.split(' '))
                if tag_parts.issubset(superior_parts) and tag_parts != superior_parts:
                    tag_map[tag] = potential_superior

    # Check for 'keep' conditions globally
    global_keep_conditions = {keyword: any(keep_phrase in tags_string for keep_phrase in conditions['keep']) for keyword, conditions in special_phrases.items()}

    # Identify tags that should not be removed because they are contained in 'remove' phrases
    non_removable_tags = set()
    for tag in tags:
        for keyword, conditions in special_phrases.items():
            if any(remove_phrase in tag for remove_phrase in conditions['remove']):
                non_removable_tags.add(tag)

    for tag in tags:
        if tag in tag_map:
            # Append non-superior tags to removed_tags if their superior counterparts are not already included
            if tag_map[tag] not in final_tags:
                removed_tags.append(tag)
            continue

        should_remove_tag = False
        for keyword, conditions in special_phrases.items():
            if keyword in tag:
                if not global_keep_conditions[keyword] and any(remove_phrase in tags_string for remove_phrase in conditions['remove']) and tag not in non_removable_tags:
                    should_remove_tag = True
                    break

        if should_remove_tag:
            removed_tags.append(tag)
        else:
            final_tags.append(tag)

    # Ensure tags explicitly listed in "remove" are not removed
    for keyword, conditions in special_phrases.items():
        for remove_tag in conditions['remove']:
            if remove_tag in removed_tags:
                removed_tags.remove(remove_tag)
                final_tags.append(remove_tag)

    # Remove duplicates in the removed_tags list by converting it to a set and back to a list
    removed_tags = ', '.join(list(set(removed_tags)))

    # Reinsert parenthesized parts back into their original positions
    final_tags_list = modified_tags_string.split(',')
    final_tags_with_parentheses = []
    for tag in final_tags_list:
        if "\0" in tag:  # If placeholder is found, replace it with the original parenthesized part
            tag = tag.replace("\0", parenthesized_parts.pop(0), 1)
        final_tags_with_parentheses.append(tag.strip())
    
    # New step: Re-sort tags to move numeric tags to the front
    numeric_tag_pattern = re.compile(r'\b\d+\+?(girls?|boys?)\b')
    numeric_tags = [tag for tag in final_tags_with_parentheses if numeric_tag_pattern.match(tag)]
    non_numeric_tags = [tag for tag in final_tags_with_parentheses if not numeric_tag_pattern.match(tag)]

    # Prioritize numeric tags in the final list
    prioritized_final_tags = numeric_tags + non_numeric_tags

    # Generate the final simplified tags string
    simplified_tags_string = ', '.join(prioritized_final_tags)

    return simplified_tags_string, removed_tags

# Test the function with an example string
tags_string = "(mirko, boku no hero academia:1.2), animal ears, breasts, dark-skinned female, large breasts, long hair, parted bangs, rabbit ears, rabbit girl, red eyes, toned, white hair, 1boy, 1girl, after ejaculation, animal ear fluff, animal hands, bell, bikini, black bikini, black thighhighs, blush, breasts apart, cat ears, cat paws, cat tail, clothed female nude male, collar, covered erect nipples, cum, cum in mouth, cum on penis, cum on tongue, facial, fake animal ears, fake tail, fang, fur collar, gloves, gluteal fold, highleg, highleg bikini, holding, holding leash, kneeling, large penis, leash, leash pull, micro bikini, navel, neck bell, nude, open mouth, paw gloves, penis, penis on face, penis over eyes, pet play, smile, stomach, swimsuit, tail, tail ornament, thighhighs, veins, veiny penis, (masterpiece, exceptional, best aesthetic, best quality, masterpiece, extremely detailed:1.1)"
simplified_tags_string, removed_tags = simplify_tags(tags_string)
print('Simplified Tags:', simplified_tags_string)
print('Removed Tags:', removed_tags)
