"""Compare two saved preview JSON files; changes do not establish improvement."""
import argparse
import json
from pathlib import Path


def validate(snapshot):
    if not isinstance(snapshot, dict) or type(snapshot.get('user_id')) is not int:
        raise ValueError('Each snapshot must contain an integer user_id.')
    if not isinstance(snapshot.get('items'), list):
        raise ValueError('Each snapshot must contain an items list.')
    if 'filters' in snapshot:
        filters = snapshot['filters']
        if not isinstance(filters, dict) or set(filters) != {'category', 'limit', 'min_score'}:
            raise ValueError('Filters must contain category, limit, and min_score.')
        if filters['category'] is not None and not isinstance(filters['category'], str):
            raise ValueError('Filter category must be text or null.')
        if type(filters['limit']) is not int or not 1 <= filters['limit'] <= 50:
            raise ValueError('Filter limit must be an integer from 1 to 50.')
        if type(filters['min_score']) is not int or not 0 <= filters['min_score'] <= 3:
            raise ValueError('Filter min_score must be an integer from 0 to 3.')
    ids = []
    for item in snapshot['items']:
        if not isinstance(item, dict) or type(item.get('item_id')) is not int:
            raise ValueError('Each item must contain an integer item_id.')
        ids.append(item['item_id'])
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate item IDs make ranks ambiguous.')
    return ids


def compare(before, after):
    old, new = validate(before), validate(after)
    if before['user_id'] != after['user_id']:
        raise ValueError('Compare snapshots for the same user.')
    filter_changes = []
    filters_known = 'filters' in before and 'filters' in after
    if filters_known:
        for key in ('category', 'limit', 'min_score'):
            previous, current = before['filters'][key], after['filters'][key]
            if key == 'category':
                previous = previous.strip().lower() if previous is not None else None
                current = current.strip().lower() if current is not None else None
            if previous != current:
                filter_changes.append({'field': key, 'before': previous, 'after': current})
    warnings = []
    if not filters_known:
        warnings.append('Filter metadata is missing; filter consistency cannot be checked.')
    elif filter_changes:
        warnings.append('Filters differ. Shortlist changes may be caused by the selected filters.')
    warnings.append('Wardrobe and profile consistency are not checked.')
    old_rank = {item_id: rank for rank, item_id in enumerate(old, 1)}
    new_rank = {item_id: rank for rank, item_id in enumerate(new, 1)}
    shared = set(old) & set(new)
    union = set(old) | set(new)
    return {
        'user_id': before['user_id'],
        'before_method': before.get('method'), 'after_method': after.get('method'),
        'before_count': len(old), 'after_count': len(new),
        'filters_match': not filter_changes if filters_known else None,
        'filter_changes': filter_changes,
        'warnings': warnings,
        'shared_count': len(shared),
        'overlap_jaccard': len(shared) / len(union) if union else None,
        'entered_item_ids': [item_id for item_id in new if item_id not in old_rank],
        'exited_item_ids': [item_id for item_id in old if item_id not in new_rank],
        'rank_changes': [{'item_id': item_id, 'before_rank': old_rank[item_id],
                          'after_rank': new_rank[item_id],
                          'positions_gained': old_rank[item_id] - new_rank[item_id]}
                         for item_id in new if item_id in shared and old_rank[item_id] != new_rank[item_id]],
        'note': 'Compares saved shortlists only. Use the same filters and wardrobe for controlled comparisons; changes are not evidence of better recommendations.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    args = parser.parse_args()
    try:
        result = compare(json.loads(args.before.read_text()), json.loads(args.after.read_text()))
    except (OSError, ValueError) as error:
        parser.exit(1, f'Cannot compare snapshots: {error}\n')
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
