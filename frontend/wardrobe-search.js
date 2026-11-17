// Every search word may match any descriptive field; no item data is changed.
function filterWardrobe(items, query, category = '', missingOnly = false) {
 const normalize = value => String(value ?? '').normalize('NFKC').toLowerCase().trim();
 const terms = normalize(query).split(/\s+/).filter(Boolean);
 const fields = ['item_name', 'category', 'subcategory', 'brand', 'primary_color', 'pattern', 'material'];
 return items.filter(item => {
  if (missingOnly && !['primary_color', 'category', 'material', 'pattern', 'subcategory']
   .some(field => !String(item[field] ?? '').trim())) return false;
  if (category && normalize(item.category) !== normalize(category)) return false;
  const values = fields.map(field => normalize(item[field]));
  return terms.every(term => values.some(value => value.includes(term)));
 });
}
function sortWardrobe(items, order = 'default') {
 const sorted = [...items];
 const name = (a, b) => String(a.item_name ?? '').localeCompare(String(b.item_name ?? ''), 'en', {sensitivity: 'base'}) || a.item_id - b.item_id;
 if (order === 'name') sorted.sort(name);
 if (order === 'least-worn') sorted.sort((a, b) => (a.times_worn ?? 0) - (b.times_worn ?? 0) || name(a, b));
 if (order === 'most-worn') sorted.sort((a, b) => (b.times_worn ?? 0) - (a.times_worn ?? 0) || name(a, b));
 return sorted;
}
if (typeof module !== 'undefined') module.exports = {filterWardrobe, sortWardrobe};
