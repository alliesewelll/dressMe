"""Explainable baseline ranking of owned items, not model confidence."""
import re
from styling import suggest_items


def normalize(value):
    return ' '.join(re.findall(r'\w+', (value or '').casefold()))


def rank_wardrobe(items, profile, limit=10):
    palette = set()
    styles = set()
    if profile:
        # Do not personalize using the generic fallback palette.
        if profile.color_season or profile.undertone:
            suggestion = suggest_items(profile.color_season, profile.undertone, None)
            if not any('general palette' in row['reason'] for row in suggestion['suggestions']):
                palette = {normalize(color) for color in suggestion['palette']}
        styles = {normalize(value) for value in re.split(r'[,;\n]', profile.preferred_styles or '') if normalize(value)}
    results = []
    for item in items:
        reasons = []
        score = 0
        if normalize(item.primary_color) in palette:
            score += 2
            reasons.append(f'{item.primary_color} matches your saved palette.')
        description = ' ' + normalize(' '.join(filter(None, [item.item_name, item.category,
            item.subcategory, item.pattern, item.material]))) + ' '
        matches = sorted(style for style in styles if f' {style} ' in description)
        if matches:
            score += 1
            reasons.append('Matches your saved style keywords: ' + ', '.join(matches) + '.')
        if not reasons:
            reasons.append('No exact palette or style-keyword match; still an option to explore.')
        results.append({'item_id': item.item_id, 'item_name': item.item_name,
                        'score': score, 'reasons': reasons})
    return sorted(results, key=lambda row: (-row['score'], row['item_id']))[:limit]
