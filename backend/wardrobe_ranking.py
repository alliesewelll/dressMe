"""Explainable baseline ranking of owned items, not model confidence."""
import re
from styling import suggest_items


def normalize(value):
    return ' '.join(re.findall(r'\w+', (value or '').casefold()))


# Curated related names, not perceptual color measurements. Keep broad colors
# (blue, green, white) out so they do not erase seasonal depth or temperature.
RELATED_COLORS = (
    frozenset({'cream', 'ivory', 'off white', 'warm white'}),
    frozenset({'olive', 'olive green'}),
    frozenset({'terracotta', 'terra cotta', 'burnt orange'}),
    frozenset({'cobalt', 'cobalt blue'}),
)


def related_palette_color(color, palette):
    for group in RELATED_COLORS:
        if color in group:
            matches = sorted(group & palette)
            if matches:
                return matches[0]
    return None


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
        color = normalize(item.primary_color)
        related = related_palette_color(color, palette)
        if color in palette:
            score += 2
            reasons.append(f'{item.primary_color} exactly matches a saved palette color.')
        elif related:
            score += 1
            reasons.append(f'{item.primary_color} is a related shade of {related} in your saved palette; compare the actual garment color.')
        description = ' ' + normalize(' '.join(filter(None, [item.item_name, item.category,
            item.subcategory, item.pattern, item.material]))) + ' '
        matches = sorted(style for style in styles if f' {style} ' in description)
        if matches:
            score += 1
            reasons.append('Matches your saved style keywords: ' + ', '.join(matches) + '.')
        if not reasons:
            reasons.append('No palette or style-keyword match; still an option to explore.')
        results.append({'item_id': item.item_id, 'item_name': item.item_name,
                        'score': score, 'reasons': reasons})
    return sorted(results, key=lambda row: (-row['score'], row['item_id']))[:limit]
