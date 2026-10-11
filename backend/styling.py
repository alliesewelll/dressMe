"""Editable styling heuristics, not an assessment of someone's appearance."""

PALETTES = {
    "spring": ["peach", "coral", "warm green"],
    "summer": ["dusty rose", "lavender", "soft blue"],
    "autumn": ["terracotta", "olive", "camel"],
    "winter": ["cobalt", "emerald", "berry"],
    "warm": ["terracotta", "olive", "cream"],
    "cool": ["blue", "lavender", "berry"],
    "neutral": ["teal", "soft white", "navy"],
}

# Optional silhouette ideas, phrased as effects rather than corrections to a body.
SILHOUETTES = {
    "hourglass": [("wrap top", "Tops", "An adjustable wrap can emphasize the waist."),
                  ("belted jacket", "Outerwear", "A belt lets you choose waist definition.")],
    "pear": [("textured top", "Tops", "Texture adds visual interest around the shoulders."),
             ("A-line skirt", "Bottoms", "An A-line shape offers room through the hips.")],
    "rectangle": [("wrap top", "Tops", "A wrap creates optional waist definition."),
                  ("pleated trousers", "Bottoms", "Pleats add volume and movement.")],
    "athletic": [("draped top", "Tops", "Draping adds a soft, flowing line."),
                 ("wide-leg trousers", "Bottoms", "A wider leg adds movement.")],
    "apple": [("open jacket", "Outerwear", "An open layer creates a vertical line."),
              ("relaxed shirt", "Tops", "A relaxed cut offers room through the torso.")],
    "inverted triangle": [("simple V-neck top", "Tops", "A V-neck creates a vertical neckline."),
                          ("wide-leg trousers", "Bottoms", "A wider leg adds volume below the waist.")],
}


def suggest_items(color_season=None, undertone=None, body_type=None):
    """Return generic item ideas from self-reported traits; never infer from skin depth.

    A recognized season takes precedence over undertone. Unknown inputs produce
    explicit, general suggestions instead of guessed personal attributes.
    """
    def normalize(value):
        return " ".join((value or "").strip().lower().replace("-", " ").split())

    season, tone, shape = map(normalize, (color_season, undertone, body_type))
    notes = ["These are optional styling ideas, not rules about what you can wear."]
    if season in ("spring", "summer", "autumn", "winter"):
        palette = PALETTES[season]
        basis = f"your saved {season} color season"
    elif tone in ("warm", "cool", "neutral"):
        palette = PALETTES[tone]
        basis = f"your saved {tone} undertone"
        notes.append("No recognized color season; using undertone as a starting point.")
    else:
        palette = ["navy", "teal", "soft white"]
        basis = "a general palette to try"
        notes.append("Save a color season or warm, cool, or neutral undertone for palette-based ideas.")
    cuts = SILHOUETTES.get(shape)
    if cuts is None:
        cuts = [("relaxed shirt", "Tops", "Try the fit and ease you find comfortable."),
                ("straight-leg trousers", "Bottoms", "A simple silhouette to try in your preferred fit.")]
        notes.append("No recognized body type; using general silhouettes.")
    return {
        "palette": palette,
        "suggestions": [
            {"item_name": name, "category": category, "suggested_colors": palette,
             "reason": f"Colors come from {basis}. {reason}"}
            for name, category, reason in cuts
        ],
        "notes": notes,
    }
