const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const colors = {camel:'#ba9870',cream:'#e4dfce',ivory:'#eee8d9',olive:'#7a8264',indigo:'#59667b',terracotta:'#b97158',black:'#40433f',blue:'#8199ac',white:'#e7e7df',navy:'#444f65',teal:'#618b89','soft white':'#ede9df',peach:'#e8b197',coral:'#d98873','warm green':'#91a17e','dusty rose':'#c8999e',lavender:'#b3a5c6','soft blue':'#9baec7',cobalt:'#4d6cab',emerald:'#4a7f66',berry:'#91526c',brown:'#917258',pink:'#d4a5a7'};
for (const entry of stylingData.catalog) for (const color of entry.colors) colors[color.name]=color.hex;
function art(category,color){
 const fill=colors[String(color).toLowerCase()]||'#ef9ab9';
 const paths = category==='Bottoms' ? '<path d="M68 30h105l-8 160h-45l-1-102-12 102H60z"/><path d="M69 45h102M118 30v58" fill="none"/>' : category==='Dresses' ? '<path d="M92 25h55l10 55 32 111H48L80 80z"/><path d="M94 25q26 32 51 0M80 80h77" fill="none"/>' : category==='Outerwear' ? '<path d="M79 29l40 10 40-10 38 40-21 27-17-20 10 117H68L79 76 59 96 39 69z"/><path d="M79 29l40 10-21 40-19-22m80-28-40 10 20 40 20-22M119 40v153M81 125h26m24 0h25" fill="none"/>' : '<path d="M81 35l38 12 38-12 40 36-26 29-18-17 8 106H76l7-106-18 17-26-29z"/><path d="M91 39q28 37 56 0M81 174h74" fill="none"/>';
 return `<svg class="clothing-sticker" viewBox="0 0 240 220" role="img" aria-label="${esc(category || 'Clothing')} placeholder illustration">
 <g aria-hidden="true" fill="#ffacd0"><path d="M32 29h6v6h6v6h-6v6h-6v-6h-6v-6h6zM198 153h5v5h5v5h-5v5h-5v-5h-5v-5h5z"/><path d="M187 30h5v5h5v5h-5v5h-5v-5h-5v-5h5z" fill="#fff" stroke="#cc4c85" stroke-width="1.5"/></g>
 <g transform="translate(3 5)" fill="#bc4f8160" stroke="#bc4f8160" stroke-width="11" stroke-linejoin="round">${paths}</g>
 <g fill="${fill}" stroke="#fff9fc" stroke-width="12" stroke-linejoin="round">${paths}</g>
 <g fill="${fill}" stroke="#873953" stroke-width="2.5" stroke-linejoin="round">${paths}</g>
 <path d="M91 96l-3 57" fill="none" stroke="#fff" stroke-opacity=".55" stroke-width="5" stroke-linecap="square"/>
 <g transform="translate(139 100)" fill="#ff9bc5" stroke="#873953" stroke-width="2" stroke-linejoin="round"><path d="M0 0l-15-8v16L0 2l15 6V-8L0 0M-2 3l-6 14m10-14 6 14"/><path d="M-3-3h6v7h-6z" fill="#fff0f7"/></g>
 </svg>`;
}
const initialItems = [
 ['Camel wool coat','Outerwear','Camel','Everlane',18],['Ivory silk blouse','Tops','Ivory','Quince',12],['Straight-leg denim','Bottoms','Indigo','Madewell',27],['Olive linen shirt','Tops','Olive','Uniqlo',8],['Everyday knit','Tops','Cream','COS',0],['Terracotta midi dress','Dresses','Terracotta','Sézane',3]
].map((x,i)=>({item_id:i+1,item_name:x[0],category:x[1],primary_color:x[2],brand:x[3],times_worn:x[4]}));
let items=[], profile={}, suggestions={}, mode='demo', user=1, category='';
function demoSuggestions(){
 const season=(profile.color_season||'').toLowerCase(), tone=(profile.undertone||'').toLowerCase(), shape=(profile.body_type||'').toLowerCase();
 const key=season in stylingData.palettes && !['warm','cool','neutral'].includes(season)?season:tone;
 const palette=stylingData.palettes[key]||['navy','teal','soft white'];
 const cuts=stylingData.silhouettes[shape]||[['relaxed shirt','Tops','Try the fit and ease you find comfortable.'],['straight-leg trousers','Bottoms','A simple silhouette to try in your preferred fit.']];
 return {palette,suggestions:cuts.map(c=>({item_name:c[0],reason:c[2],suggested_colors:palette}))};
}
function demo(){mode='demo';items=structuredClone(initialItems);profile={color_season:'True Autumn',undertone:'Warm',body_type:'Hourglass'};suggestions=demoSuggestions();render();}
async function api(path,method='GET',body){
 const response=await fetch(`/users/${user}/${path}`,{method,headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(10000)});
 if(!response.ok){let detail;try{detail=(await response.json()).detail}catch{}throw new Error(typeof detail==='string'?detail:`Could not complete request (${response.status}). Check your backend and user ID.`)}
 return response.status===204?null:response.json();
}
async function loadLive(){
 let all=[],offset=0;
 while(true){const page=await api(`wardrobe?limit=100&offset=${offset}`);all.push(...page);if(page.length<100)break;offset+=100;}
 let p={},s={palette:[],suggestions:[]};
 // An existing user can have no profile yet.
 const response=await fetch(`/users/${user}/style-profile`,{signal:AbortSignal.timeout(10000)});
 if(response.ok){p=await response.json();s=await api('style-suggestions');}else if(response.status!==404){throw new Error('Unable to load your style profile.');}
 items=all;profile=p;suggestions=s;mode='live';render();
}
function render(){
 window.dispatchEvent(new CustomEvent("wardrobe-context",{detail:{mode,user}}));
 $('#connection').textContent=mode==='demo'?'Demo wardrobe ↗':`User ${user} · Live wardrobe ↗`;
 $('#mode-note').textContent=mode==='demo'?'✧ Demo mode · Explore a sample closet. Changes last until you refresh.':'✧ Connected to your local backend · Changes are saved to your wardrobe.';
 $('#count').textContent=items.length;$('#wears').textContent=items.reduce((s,x)=>s+x.times_worn,0);$('#unworn').textContent=items.filter(x=>!x.times_worn).length;
 $('#item-count').textContent=`${items.length} pieces`;
 renderGrid();
 $('#profile-copy').innerHTML=profile.color_season||profile.undertone||profile.body_type?`<p>${[profile.color_season&&profile.color_season+' palette',profile.undertone&&profile.undertone+' undertone',profile.body_type].filter(Boolean).map(esc).join(' · ')}</p>`:'<p>Set your preferences to find your starting palette.</p>';
 if(profile.preferred_styles) $('#profile-copy').innerHTML+=`<p>Your style: ${esc(profile.preferred_styles)}</p>`;
 $('#swatches').innerHTML=(suggestions.palette||[]).map(c=>`<div class="swatch" style="background:${colors[c]||'#a4a88e'}" title="${esc(c)}" role="img" aria-label="${esc(c)}"></div>`).join('');
 $('#suggestions').innerHTML=(suggestions.suggestions||[]).map(s=>`<article class="suggestion"><h3>${esc(s.item_name)} ↗</h3><p>${esc(s.reason)}</p><small>TRY IT IN ${(s.suggested_colors||[]).map(esc).join(' · ')}</small></article>`).join('')||'<p>Add a style profile to see color and silhouette ideas.</p>';
}
function renderGrid(){const search=$('#search').value.toLowerCase().trim();const filtered=items.filter(i=>(!category||i.category===category)&&i.item_name.toLowerCase().includes(search));
 $('#grid').innerHTML=filtered.map(i=>`<article class="card"><div class="card-art"><span class="wear-badge">${i.times_worn?i.times_worn+(i.times_worn===1?' wear':' wears'):'A fresh favorite'}</span>${art(i.category,i.primary_color)}</div><h3>${esc(i.item_name)}</h3><div class="card-meta"><span>${esc(i.brand||i.category||'Your wardrobe')}</span><span>${esc(i.primary_color||'')}</span></div><button class="wear-button" data-wear="${i.item_id}">＋ Wore it today</button></article>`).join('')||'<div class="empty">No pieces here yet. Add a piece or try another search.</div>';
}
function show(id){const d=$(id);d.querySelector('.form-error').textContent='';d.showModal();}
$('#hero-art').innerHTML=art('Outerwear','Cream');
$('#search').addEventListener('input',renderGrid);
$('.filters').addEventListener('click',e=>{const b=e.target.closest('[data-category]');if(!b)return;category=b.dataset.category;document.querySelectorAll('[data-category]').forEach(x=>x.classList.toggle('selected',x===b));renderGrid()});
$('#add').onclick=()=>show('#item-dialog');$('#connection').onclick=()=>show('#connect-dialog');
$('#edit-profile').onclick=()=>{const f=$('#profile-form');for(const key of ['color_season','undertone','body_type']){const v=profile[key]||'';f.elements[key].value=[...f.elements[key].options].find(o=>o.value.toLowerCase()===v.toLowerCase())?.value||'';}f.elements.preferred_styles.value=profile.preferred_styles||'';show('#profile-dialog')};
for(const b of document.querySelectorAll('[data-close]'))b.onclick=()=>b.closest('dialog').close();
$('#demo').onclick=()=>{demo();$('#connect-dialog').close();$('#message').textContent='Sample wardrobe loaded.'};
async function submit(form,fn){const b=form.querySelector('[type=submit]');b.disabled=true;form.querySelector('.form-error').textContent='';try{await fn();form.closest('dialog').close()}catch(e){form.querySelector('.form-error').textContent=e.message}finally{b.disabled=false}}
$('#connect-form').onsubmit=e=>{e.preventDefault();submit(e.target,async()=>{const oldUser=user;user=Number(e.target.elements.user.value);try{await loadLive();$('#message').textContent='Your wardrobe is connected.'}catch(error){user=oldUser;throw error}})};
$('#item-form').onsubmit=e=>{e.preventDefault();submit(e.target,async()=>{const body=Object.fromEntries(new FormData(e.target));for(const k in body)body[k]=body[k].trim()||null;if(!body.item_name)throw new Error('Please give your piece a name.');if(mode==='demo')items.unshift({...body,item_id:Math.max(0,...items.map(i=>i.item_id))+1,times_worn:0});else items.unshift(await api('wardrobe','POST',body));render();e.target.reset();$('#message').textContent='Your new piece is in the wardrobe.'})};
$('#profile-form').onsubmit=e=>{e.preventDefault();submit(e.target,async()=>{const body=Object.fromEntries(new FormData(e.target));for(const k in body)body[k]=body[k].trim()||null;if(mode==='demo'){profile=body;suggestions=demoSuggestions()}else{profile=await api('style-profile','PATCH',body);suggestions=await api('style-suggestions')}render();$('#message').textContent='Style preferences updated.'})};
$('#grid').onclick=async e=>{const b=e.target.closest('[data-wear]');if(!b)return;b.disabled=true;try{const id=Number(b.dataset.wear),i=items.find(x=>x.item_id===id);if(mode==='demo')i.times_worn++;else Object.assign(i,await api(`wardrobe/${id}/wear`,'POST'));render();$('#message').textContent=`One more wear for ${i.item_name}.`}catch(error){$('#message').textContent=error.message;b.disabled=false}};
initColorGuide();
demo();

function initColorGuide(){
 const families=['Spring','Summer','Autumn','Winter'];
 const select=$('#profile-form').elements.color_season;
 select.innerHTML='<option value="">Not sure yet</option>'+families.map(f=>`<optgroup label="${f}"><option value="${f}">${f} · general palette</option>${stylingData.catalog.filter(p=>p.family===f).map(p=>`<option>${esc(p.name)}</option>`).join('')}</optgroup>`).join('');
 $('#palette-guide').innerHTML=families.map(f=>{
  const entries=stylingData.catalog.filter(p=>p.family===f);
  return `<section class="palette-family"><h3>${f} <small>${esc(entries[0].family_description)}</small></h3><div class="palette-cards">${entries.map(p=>`<article class="palette-card"><h4>${esc(p.name)}</h4><p>${esc(p.description)}</p><div class="palette-strip">${p.colors.map(c=>`<div><span style="background:${c.hex}" role="img" aria-label="${esc(c.name)}"></span><small>${esc(c.name)}</small></div>`).join('')}</div><button class="text-button" data-palette="${esc(p.name)}">Try this palette ↗</button></article>`).join('')}</div></section>`;
 }).join('');
 $('#palette-guide').addEventListener('click',e=>{const button=e.target.closest('[data-palette]');if(!button)return;$('#edit-profile').click();select.value=button.dataset.palette;});
}
