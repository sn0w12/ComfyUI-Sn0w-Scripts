def simplify_tags(tags_string):
    # Configuration for special phrases
    special_phrases = {
        'eye': {
            'remove': ['covering eyes', 'over eyes', 'covered eyes', 'covering face', 'covering own eyes', 'from behind', 'facing away', 'penis over eyes'],
            'keep': ['looking at viewer']
        },
        'sclera': {
            'remove': ['covering eyes', 'over eyes', 'covered eyes', 'covering face', 'covering own eyes', 'from behind', 'facing away', 'penis over eyes'],
            'keep': ['looking at viewer']
        },
        'mouth': {
            'remove': ['from behind', 'facing away'],
            'keep': ['looking at viewer']
        },
        'teeth': {
            'remove': ['from behind', 'facing away'],
            'keep': ['looking at viewer']
        },
    }

    tags = [tag.strip() for tag in tags_string.split(',')]
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

    for tag in tags:
        if tag in tag_map:
            # Append non-superior tags to removed_tags if their superior counterparts are not already included
            if tag_map[tag] not in final_tags:
                removed_tags.append(tag)
            continue

        should_remove_tag = False
        for keyword, conditions in special_phrases.items():
            if keyword in tag:
                # Ensure the tag itself is not in the 'remove' array to be preserved
                if tag not in conditions['remove'] and not global_keep_conditions[keyword] and any(remove_phrase in tags_string for remove_phrase in conditions['remove']):
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
    removed_tags = list(set(removed_tags))

    # Join the final list of tags back into a string
    simplified_tags_string = ', '.join(final_tags)

    return simplified_tags_string, removed_tags

# Test the function with an example string
tags_string = "(mirko, boku no hero academia:1.2), animal ears, breasts, dark-skinned female, large breasts, long hair, parted bangs, rabbit ears, rabbit girl, red eyes, toned, white hair, 1boy, 1girl, after ejaculation, animal ear fluff, animal hands, bell, bikini, black bikini, black thighhighs, blush, breasts apart, cat ears, cat paws, cat tail, clothed female nude male, collar, covered erect nipples, cum, cum in mouth, cum on penis, cum on tongue, facial, fake animal ears, fake tail, fang, fur collar, gloves, gluteal fold, highleg, highleg bikini, holding, holding leash, kneeling, large penis, leash, leash pull, micro bikini, navel, neck bell, nude, open mouth, paw gloves, penis, penis on face, penis over eyes, pet play, smile, stomach, swimsuit, tail, tail ornament, thighhighs, veins, veiny penis, (masterpiece, exceptional, best aesthetic, best quality, masterpiece, extremely detailed:1.1)"
simplified_tags_string, removed_tags = simplify_tags(tags_string)
print('Simplified Tags:', simplified_tags_string)
print('Removed Tags:', removed_tags)
