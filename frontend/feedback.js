(() => {
 const panel=document.querySelector('#recommendation-history'), status=document.querySelector('#feedback-status');
 document.querySelector('#load-recommendations').onclick=async e=>{
  panel.innerHTML='';
  if(mode!=='live'){status.textContent='Connect an existing user to the backend to review saved recommendations. Demo suggestions are not saved recommendation records.';return;}
  const target=user;e.target.disabled=true;status.textContent='Loading…';
  try{
   const rows=await api('recommendations?limit=50');
   if(mode!=='live'||user!==target)return;
   panel.innerHTML=rows.map(r=>`<form class="palette-card" data-rec="${r.recommendation_id}" data-user="${target}"><h3>${esc(r.recommendation)} · #${r.recommendation_id}</h3><p>${esc(r.recommendation_reason||'No explanation saved.')}</p><label>Your reaction <select name="feedback"><option>LIKE</option><option>NEUTRAL</option><option>DISLIKE</option></select></label><label>Rating <select name="rating"><option value="">Not rated</option>${[1,2,3,4,5].map(n=>`<option>${n}</option>`).join('')}</select></label><label>Did you purchase it? <select name="purchased"><option value="">Not answered</option><option value="true">Yes</option><option value="false">No</option></select></label><label>Notes <textarea name="comments" maxlength="2000"></textarea></label><button class="primary">Save feedback</button><p class="feedback-result" role="status"></p></form>`).join('');
   // Load prior values so repeat reviews never silently overwrite them with defaults.
   await Promise.all([...panel.querySelectorAll('form')].map(async form=>{
    form.querySelector('button').disabled=true;
    try{const response=await fetch(`/users/${target}/recommendations/${form.dataset.rec}/feedback`,{signal:AbortSignal.timeout(10000)});
     if(response.status===404)return;
     if(!response.ok)throw new Error('Could not load existing feedback. Reload before editing.');
     const saved=await response.json();for(const k of ['feedback','rating','purchased','comments'])form.elements[k].value=saved[k]===null?'':String(saved[k]);
    }catch(error){form.dataset.failed='true';form.querySelector('.feedback-result').textContent=error.message;}
    finally{form.querySelector('button').disabled=form.dataset.failed==='true';}
   }));
   status.textContent=rows.length?'Showing the newest 50 or fewer saved recommendations.':'No saved recommendations yet. The API can record recommendations for evaluation.';
  }catch(error){status.textContent=error.message;}finally{e.target.disabled=false;}
 };
 panel.addEventListener('submit',async e=>{e.preventDefault();const form=e.target;
  if(mode!=='live'||user!==Number(form.dataset.user)){status.textContent='Your selected user changed. Reload recommendations.';panel.innerHTML='';return;}
  const b=form.querySelector('button'), output=form.querySelector('.feedback-result');b.disabled=true;
  try{const values=Object.fromEntries(new FormData(form));await api(`recommendations/${form.dataset.rec}/feedback`,'PUT',{feedback:values.feedback,rating:values.rating?Number(values.rating):null,purchased:values.purchased===''?null:values.purchased==='true',comments:values.comments||null});output.textContent='Feedback saved. Thank you!';}catch(error){output.textContent=error.message;}finally{b.disabled=false;}
 });
})();
