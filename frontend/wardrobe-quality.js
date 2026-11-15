// Completeness describes saved metadata, not recommendation quality.
(() => {
 const button = document.querySelector('#check-wardrobe-quality');
 const status = document.querySelector('#wardrobe-quality-status');
 const results = document.querySelector('#wardrobe-quality-results');
 const labels = {primary_color: 'color', category: 'category', material: 'material', pattern: 'pattern', subcategory: 'clothing type'};
 let generation = 0;
 let missingByItem = new Map();
 function reset() {
  generation++;
  results.innerHTML = '';
  missingByItem.clear();
  button.disabled = mode !== 'live';
  status.textContent = mode === 'live' ? 'Check your whole wardrobe for missing details.' : 'Connect your wardrobe to check saved clothing details.';
 }
 button.onclick = async () => {
  if (mode !== 'live') return;
  const ticket = ++generation;
  button.disabled = true;
  results.innerHTML = '';
  missingByItem.clear();
  status.textContent = 'Checking your wardrobe…';
  try {
   const report = await api('wardrobe-quality');
   if (ticket !== generation) return;
   status.textContent = !report.item_count ? 'Add a piece to your wardrobe to get started.'
    : !report.items_with_missing_details ? 'All your pieces have these clothing details filled in.'
    : `${report.items_with_missing_details} of ${report.item_count} pieces have optional details missing. This checks your whole wardrobe, regardless of match filters.`;
   if (report.items_with_missing_details) {
    missingByItem = new Map(report.items.map(item => [item.item_id, item.missing_fields]));
    const counts = Object.entries(labels).filter(([key]) => report.missing_counts[key] > 0)
     .map(([key, label]) => `${label}: ${report.missing_counts[key]}`).join(' · ');
    results.innerHTML = `<p class="fine">Missing ${esc(counts)}</p>` + report.items.map(item =>
     `<article class="suggestion"><h3>${esc(item.item_name)}</h3><p>Missing: ${item.missing_fields.map(field => esc(labels[field] || field)).join(', ')}.</p><button class="text-button" data-quality-edit="${esc(item.item_id)}" aria-label="Add details for ${esc(item.item_name)}">Add missing details ↗</button></article>`).join('')
     + (report.truncated ? `<p class="fine">Showing ${report.items.length} pieces with missing details.</p>` : '');
   }
  } catch (error) {
   if (ticket === generation) status.textContent = `Unable to check details: ${error.message} Try again.`;
  } finally {
   if (ticket === generation) button.disabled = false;
  }
 };
 results.onclick = event => {
  const edit = event.target.closest('[data-quality-edit]');
  if (!edit || mode !== 'live') return;
  const id = Number(edit.dataset.qualityEdit);
  const missing = missingByItem.get(id);
  if (!missing) return;
  const item = items.find(piece => piece.item_id === id);
  if (!item) {
   status.textContent = 'This piece is no longer loaded. Reconnect your wardrobe and check again.';
   return;
  }
  openItemForm(item);
  const field = document.querySelector('#item-form').elements[missing.find(name => Object.hasOwn(labels, name))];
  if (field) {
   const section = field.closest('details');
   if (section) section.open = true;
   field.focus();
  }
 };
 window.addEventListener('wardrobe-context', reset);
 reset();
})();
