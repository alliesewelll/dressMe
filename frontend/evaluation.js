// Rates use their own response counts; missing outcomes are not zeros.
function evaluationMarkup(metrics, escapeText) {
 const percent=value=>value===null?'Not enough data':`${Math.round(value*100)}%`;
 return metrics.map(row=>`<article class="palette-card"><h4>${escapeText(row.recommendation)}</h4><p>${row.recommendation_count} saved recommendations · ${row.feedback_count} reviewed</p><dl>
 <div><dt>Feedback coverage</dt><dd>${percent(row.feedback_coverage)}</dd></div>
 <div><dt>Liked</dt><dd>${percent(row.like_rate)}</dd></div>
 <div><dt>Purchased</dt><dd>${percent(row.purchase_rate)}</dd></div>
 <div><dt>Average rating</dt><dd>${row.average_rating===null?'Not rated':row.average_rating.toFixed(1)+' / 5'}</dd></div>
 </dl><p class="fine">Likes: ${row.feedback_count} reviews · Purchases: ${row.purchase_response_count} answers · Ratings: ${row.rating_count} answers</p></article>`).join('');
}
if(typeof module!=='undefined')module.exports={evaluationMarkup};
if(typeof document!=='undefined')(() => {
 const status=document.querySelector('#evaluation-status'), cards=document.querySelector('#evaluation-cards'), button=document.querySelector('#refresh-evaluation');
 let generation=0, context=`${mode}:${user}`;
 async function refresh(){
  const ticket=++generation, target=user;cards.innerHTML='';
  if(mode!=='live'){status.textContent='Connect your wardrobe to view real feedback trends. Demo activity is not included.';button.disabled=false;return;}
  button.disabled=true;status.textContent='Loading your report…';
  try{
   const result=await api('recommendation-evaluation');
   if(ticket!==generation||mode!=='live'||target!==user)return;
   cards.innerHTML=evaluationMarkup(result.metrics,esc);
   status.textContent=result.metrics.length?'Report updated from your saved feedback.':'No saved recommendations yet. Your report will appear here after you save some.';
  }catch(error){if(ticket===generation)status.textContent=`Could not load the report: ${error.message} Use Refresh report to retry.`;}
  finally{if(ticket===generation)button.disabled=false;}
 }
 button.onclick=refresh;
 window.addEventListener('feedback-saved',refresh);
 window.addEventListener('wardrobe-context',()=>{
  const next=`${mode}:${user}`;if(next===context)return;context=next;generation++;cards.innerHTML='';button.disabled=false;
  status.textContent=mode==='live'?'Select Refresh report to view this user’s feedback trends.':'Connect your wardrobe to view real feedback trends. Demo activity is not included.';
 });
})();
