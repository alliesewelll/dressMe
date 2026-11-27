// Owned-item matches use the backend's explainable baseline, not AI confidence.
(() => {
 const button = document.querySelector('#load-wardrobe-matches');
 const status = document.querySelector('#wardrobe-match-status');
 const results = document.querySelector('#wardrobe-matches');
 const categoryFilter = document.querySelector('#match-category');
 const strengthFilter = document.querySelector('#match-strength');
 const limitFilter = document.querySelector('#match-limit');
 let generation = 0;
 let shownIds = new Set();
 let shownKeywords = new Set();
 function refreshCategories() {
  const selected = (categoryFilter.value || '').trim().toLowerCase();
  const categories = new Map();
  for (const value of ['Tops', 'Bottoms', 'Dresses', 'Outerwear', 'Shoes', 'Accessories', ...items.map(item => item.category)]) {
   const label = (value || '').trim();
   if (label && !categories.has(label.toLowerCase())) categories.set(label.toLowerCase(), label);
  }
  categoryFilter.replaceChildren(new Option('All clothing', ''),
   ...[...categories.values()].map(label => new Option(label, label)));
  categoryFilter.value = categories.get(selected) || '';
 }
 function scoreDetails(item) {
  const detail = item.breakdown;
  if (!detail) return '';
  const colorLabel = {exact: 'Exact palette color', related: 'Related palette shade', none: 'No palette match'}[detail.color_match] || 'Palette color';
  return `<dl class="clothing-details"><div><dt>${esc(colorLabel)}</dt><dd>${esc(detail.color_points)} / 2 points</dd></div><div><dt>Style keywords</dt><dd>${esc(detail.style_points)} / 1 point</dd></div></dl>`
   + (detail.matched_style_keywords?.length ? `<p class="fine">Matched keywords: ${detail.matched_style_keywords.map(esc).join(', ')}.</p><div>${detail.matched_style_keywords.map(keyword => `<button class="text-button" data-match-keyword="${esc(keyword)}">Find more ${esc(keyword)} pieces ↗</button>`).join(' ')}</div>` : '');
 }
 function reset() {
  generation++;
  results.innerHTML = '';
  shownIds.clear();
  shownKeywords.clear();
  button.disabled = mode !== 'live';
  status.textContent = mode === 'live'
   ? 'Find pieces that match your saved palette and style preferences.'
   : 'Connect your wardrobe to find matches from your own clothes.';
 }
 button.onclick = async () => {
  if (mode !== 'live') return;
  const ticket = ++generation;
  button.disabled = true;
  results.innerHTML = '';
  shownIds.clear();
  shownKeywords.clear();
  status.textContent = 'Finding your matches…';
  try {
   const response = await api('wardrobe-ranking?limit=' + encodeURIComponent(limitFilter.value || '5') + '&include_coverage=true&min_score=' + encodeURIComponent(strengthFilter.value || '0') + (categoryFilter.value ? '&category=' + encodeURIComponent(categoryFilter.value) : ''));
   if (ticket !== generation) return;
   shownIds = new Set(response.items.map(item => item.item_id));
   shownKeywords = new Set(response.items.flatMap(item => item.breakdown?.matched_style_keywords || []));
   results.innerHTML = response.items.map(item => `<article class="suggestion"><h3>${esc(item.item_name)}</h3><p>${item.reasons.map(esc).join(' ')}</p>${scoreDetails(item)}<small>${item.score} / 3 matching points</small><button class="text-button" data-match-edit="${esc(item.item_id)}" aria-label="Edit details for ${esc(item.item_name)}">Edit details ↗</button></article>`).join('');
   status.textContent = response.items.length
    ? 'Your top wardrobe matches. Points reflect exact or related palette colors and style-keyword matches, not confidence.'
    : Number(strengthFilter.value) > 0 ? 'No pieces meet these filters. Try Explore all pieces, another category, or update your style preferences.' : categoryFilter.value ? 'No pieces in this category yet. Try All clothing or add a piece.' : 'Add a piece to your wardrobe to get started.';
   const coverage = response.coverage;
   if (coverage && coverage.candidate_count > 0) {
    const scope = categoryFilter.value ? 'in this category' : 'in your wardrobe';
    status.textContent = `${coverage.matching_item_count} of ${coverage.candidate_count} pieces ${scope} match your palette or style keywords. ${coverage.eligible_count} pass your match-strength filter; showing ${response.items.length}. ` + status.textContent;
   }
  } catch (error) {
   if (ticket === generation) status.textContent = `Unable to load matches: ${error.message} Try again.`;
  } finally {
   if (ticket === generation) button.disabled = false;
  }
 };
 results.onclick = event => {
  const keyword = event.target.closest('[data-match-keyword]');
  if (keyword && mode === 'live' && shownKeywords.has(keyword.dataset.matchKeyword)) {
   searchWardrobeKeyword(keyword.dataset.matchKeyword);
   return;
  }

  const edit = event.target.closest('[data-match-edit]');
  if (!edit || mode !== 'live') return;
  const id = Number(edit.dataset.matchEdit);
  if (!shownIds.has(id)) return;
  const item = items.find(piece => piece.item_id === id);
  if (!item) {
   status.textContent = 'This piece is no longer loaded. Reconnect your wardrobe and find matches again.';
   return;
  }
  openItemForm(item);
 };
 // Any wardrobe or preference edit invalidates the previous ranking.
 categoryFilter.onchange = reset;
 strengthFilter.onchange = reset;
 limitFilter.onchange = reset;
 window.addEventListener('wardrobe-context', () => { refreshCategories(); reset(); });
 refreshCategories();
 reset();
})();
