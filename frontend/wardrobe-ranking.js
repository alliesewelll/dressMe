// Owned-item matches use the backend's explainable baseline, not AI confidence.
(() => {
 const button = document.querySelector('#load-wardrobe-matches');
 const status = document.querySelector('#wardrobe-match-status');
 const results = document.querySelector('#wardrobe-matches');
 const categoryFilter = document.querySelector('#match-category');
 let generation = 0;
 function reset() {
  generation++;
  results.innerHTML = '';
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
  status.textContent = 'Finding your matches…';
  try {
   const response = await api('wardrobe-ranking?limit=5' + (categoryFilter.value ? '&category=' + encodeURIComponent(categoryFilter.value) : ''));
   if (ticket !== generation) return;
   results.innerHTML = response.items.map(item => `<article class="suggestion"><h3>${esc(item.item_name)}</h3><p>${item.reasons.map(esc).join(' ')}</p><small>${item.score} / 3 matching points</small></article>`).join('');
   status.textContent = response.items.length
    ? 'Your top wardrobe matches. Points reflect exact or related palette colors and style-keyword matches, not confidence.'
    : categoryFilter.value ? 'No pieces in this category yet. Try All clothing or add a piece.' : 'Add a piece to your wardrobe to get started.';
  } catch (error) {
   if (ticket === generation) status.textContent = `Unable to load matches: ${error.message} Try again.`;
  } finally {
   if (ticket === generation) button.disabled = false;
  }
 };
 // Any wardrobe or preference edit invalidates the previous ranking.
 categoryFilter.onchange = reset;
 window.addEventListener('wardrobe-context', reset);
 reset();
})();
