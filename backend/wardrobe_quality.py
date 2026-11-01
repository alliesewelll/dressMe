"""Metadata completeness checks; not a measure of recommendation accuracy."""
FIELDS = ('primary_color', 'category', 'material', 'pattern', 'subcategory')


def summarize_quality(items, limit=50):
    missing_counts = dict.fromkeys(FIELDS, 0)
    incomplete = []
    item_count = 0
    for item in items:
        item_count += 1
        missing = [field for field in FIELDS if not (getattr(item, field) or '').strip()]
        for field in missing:
            missing_counts[field] += 1
        if missing:
            incomplete.append({'item_id': item.item_id, 'item_name': item.item_name,
                               'missing_fields': missing})
    return {'item_count': item_count, 'items_with_missing_details': len(incomplete),
            'missing_counts': missing_counts,
            'items': sorted(incomplete, key=lambda row: row['item_id'])[:limit],
            'truncated': len(incomplete) > limit}
