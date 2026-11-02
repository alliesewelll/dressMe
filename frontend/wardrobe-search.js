// Every search word may match any descriptive field; no item data is changed.
function filterWardrobe(items, query, category = '') {
 const normalize = value => String(value ?? '').normalize('NFKC').toLowerCase().trim();
 const terms = normalize(query).split(/\s+/).filter(Boolean);
 const fields = ['item_name', 'category', 'subcategory', 'brand', 'primary_color', 'pattern', 'material'];
 return items.filter(item => {
  if (category && normalize(item.category) !== normalize(category)) return false;
  const values = fields.map(field => normalize(item[field]));
  return terms.every(term => values.some(value => value.includes(term)));
 });
}
if (typeof module !== 'undefined') module.exports = {filterWardrobe};
