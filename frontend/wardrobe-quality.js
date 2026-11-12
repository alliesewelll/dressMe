// Completeness describes saved metadata, not recommendation quality.
(() => {
 const button = document.querySelector('#check-wardrobe-quality');
 const status = document.querySelector('#wardrobe-quality-status');
 const results = document.querySelector('#wardrobe-quality-results');
 const labels = {primary_color: 'color', category: 'category', material: 'material', pattern: 'pattern', subcategory: 'clothing type'};
 let generation = 0;
 function reset() {
  generation++;
  results.innerHTML = '';
  button.disabled = mode !== 'live';
  status.textContent = mode === 'live' ? 'Check your whole wardrobe for missing details.' : 'Connect your wardrobe to check saved clothing details.';
 }
 button.onclick = async () => {
  if (mode !== 'live') return;
  const ticket = ++generation;
  button.disabled = true;
  results.innerHTML = '';
  status.textContent = 'Checking your wardrobe…';
  try {
   const report = await api('wardrobe-quality');
   if (ticket !== generation) return;
   status.textContent = !report.item_count ? 'Add a piece to your wardrobe to get started.'
    : !report.items_with_missing_details ? 'All your pieces have these clothing details filled in.'
    : `${report.items_with_missing_details} of ${report.item_count} pieces have optional details missing. This checks your whole wardrobe, regardless of match filters.`;
   if (report.items_with_missing_details) {
    const counts = Object.entries(labels).filter(([key]) => report.missing_counts[key] > 0)
     .map(([key, label]) => `${label}: ${report.missing_counts[key]}`).join(' · ');
    results.innerHTML = `<p class="fine">Missing ${esc(counts)}</p>` + report.items.map(item =>
     `<article class="suggestion"><h3>${esc(item.item_name)}</h3><p>Missing: ${item.missing_fields.map(field => esc(labels[field] || field)).join(', ')}.</p></article>`).join('')
     + (report.truncated ? `<p class="fine">Showing ${report.items.length} pieces with missing details.</p>` : '');
   }
  } catch (error) {
   if (ticket === generation) status.textContent = `Unable to check details: ${error.message} Try again.`;
  } finally {
   if (ticket === generation) button.disabled = false;
  }
 };
 window.addEventListener('wardrobe-context', reset);
 reset();
})();
