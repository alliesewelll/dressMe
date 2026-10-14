// Local virtual draping: no image bytes are sent to the API or browser storage.
(() => {
 let portraitURL=null, generation=0;
 const sides=[{season:0,color:0},{season:4,color:0}];
 const grid=document.querySelector('#drape-grid'), status=document.querySelector('#photo-status');
 function renderStudio(){
  grid.innerHTML=sides.map((side,index)=>{
   const palette=stylingData.catalog[side.season];
   return `<article class="drape-card"><label>Palette ${index===0?'A':'B'}<select data-side="${index}" aria-label="Palette ${index===0?'A':'B'}">${stylingData.catalog.map((p,i)=>`<option value="${i}" ${i===side.season?'selected':''}>${esc(p.name)}</option>`).join('')}</select></label><div class="portrait-frame" style="background:${palette.colors[side.color].hex}">${portraitURL?`<img src="${portraitURL}" alt="Your portrait against ${esc(palette.colors[side.color].name)}">`:'<span>Add your portrait above</span>'}</div><p>${esc(palette.colors[side.color].name)}</p><div class="drape-colors">${palette.colors.map((c,i)=>`<button data-side="${index}" data-color="${i}" aria-label="Try ${esc(c.name)} in palette ${index===0?'A':'B'}" aria-pressed="${i===side.color}" style="background:${c.hex}"></button>`).join('')}</div><button class="primary" data-save="${index}" ${portraitURL?'':'disabled'}>Use ${esc(palette.name)}</button></article>`;
  }).join('');
 }
 grid.addEventListener('change',event=>{const select=event.target.closest('select[data-side]');if(!select)return;const side=sides[Number(select.dataset.side)];side.season=Number(select.value);side.color=0;renderStudio();grid.querySelector(`select[data-side="${select.dataset.side}"]`).focus();});
 grid.addEventListener('click',event=>{
  const color=event.target.closest('[data-color]');
  if(color){sides[Number(color.dataset.side)].color=Number(color.dataset.color);renderStudio();grid.querySelector(`[data-side="${color.dataset.side}"][data-color="${color.dataset.color}"]`).focus();return;}
  const save=event.target.closest('[data-save]');
  if(save&&portraitURL){document.querySelector('#edit-profile').click();document.querySelector('#profile-form').elements.color_season.value=stylingData.catalog[sides[Number(save.dataset.save)].season].name;}
 });
 document.querySelector('#portrait-file').addEventListener('change',async event=>{
  const file=event.target.files[0];if(!file)return;const ticket=++generation;
  if(!['image/jpeg','image/png','image/webp'].includes(file.type)||file.size>10*1024*1024){status.textContent='Choose a JPEG, PNG, or WebP image smaller than 10 MB.';event.target.value='';return;}
  const candidate=URL.createObjectURL(file);status.textContent='Loading your portrait…';
  try{
   const image=new Image();image.src=candidate;await image.decode();
   if(ticket!==generation){URL.revokeObjectURL(candidate);return;}
   if(image.naturalWidth*image.naturalHeight>40000000)throw new Error('Image too large');
   if(portraitURL)URL.revokeObjectURL(portraitURL);portraitURL=candidate;
   document.querySelector('#remove-photo').disabled=false;renderStudio();status.textContent='Compare the same photo in both frames. Tap a swatch to try each color, then choose a palette.';
  }catch{URL.revokeObjectURL(candidate);if(ticket===generation)status.textContent='Could not open this image. Try a smaller JPEG, PNG, or WebP (under 40 megapixels).';}
  event.target.value='';
 });
 document.querySelector('#remove-photo').addEventListener('click',()=>{generation++;if(portraitURL)URL.revokeObjectURL(portraitURL);portraitURL=null;document.querySelector('#portrait-file').value='';document.querySelector('#remove-photo').disabled=true;status.textContent='Photo removed from this tab.';renderStudio();});
 renderStudio();
})();
