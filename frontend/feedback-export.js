(() => {
 const button = document.querySelector('#download-feedback');
 const status = document.querySelector('#export-status');
 let generation = 0;
 function reset() {
  generation++;
  button.disabled = mode !== 'live';
  status.textContent = mode === 'live' ? '' : 'Connect your wardrobe to export feedback.';
 }
 window.addEventListener('wardrobe-context', reset);
 button.onclick = async () => {
  if (mode !== 'live') return;
  const ticket = ++generation, target = user;
  button.disabled = true;
  status.textContent = 'Preparing your CSV…';
  try {
   const response = await fetch(`/users/${target}/feedback-features.csv`, {signal: AbortSignal.timeout(10000)});
   if (!response.ok) throw new Error(`Download failed (${response.status}).`);
   if (!(response.headers.get('content-type') || '').startsWith('text/csv')) throw new Error('The server did not return a CSV.');
   const blob = await response.blob();
   if (ticket !== generation || mode !== 'live' || user !== target) return;
   const url = URL.createObjectURL(blob), link = document.createElement('a');
   link.href = url;
   link.download = `feedback-features-${target}.csv`;
   document.body.appendChild(link);
   link.click();
   link.remove();
   setTimeout(() => URL.revokeObjectURL(url), 1000);
   status.textContent = 'CSV download started. Includes color and category trends from up to 100 recently reviewed recommendations.';
  } catch (error) {
   if (ticket === generation) status.textContent = `${error.message} Please try again.`;
  } finally {
   if (ticket === generation) button.disabled = mode !== 'live';
  }
 };
 reset();
})();
