// Local virtual draping: no image bytes are sent to the API or browser storage.
(() => {
 let portraitURL=null, generation=0;
 const canvas=document.querySelector('#skin-canvas'), ctx=canvas.getContext('2d',{willReadFrequently:true});
 let source=null, point={x:0,y:0};
 function drawSample(){if(!source)return;ctx.drawImage(source,0,0,canvas.width,canvas.height);ctx.strokeStyle='white';ctx.lineWidth=3;ctx.strokeRect(point.x-10,point.y-10,20,20);ctx.strokeStyle='black';ctx.lineWidth=1;ctx.strokeRect(point.x-11,point.y-11,22,22);}
 function analyze(){
  if(!source)return;
  ctx.drawImage(source,0,0,canvas.width,canvas.height);
  const x=Math.max(0,Math.min(canvas.width-1,Math.round(point.x))), y=Math.max(0,Math.min(canvas.height-1,Math.round(point.y)));
  const data=ctx.getImageData(Math.max(0,x-5),Math.max(0,y-5),Math.min(10,canvas.width-Math.max(0,x-5)),Math.min(10,canvas.height-Math.max(0,y-5))).data;
  const channels=[[],[],[]];for(let i=0;i<data.length;i+=4){if(data[i+3]<240)continue;channels.forEach((c,j)=>c.push(data[i+j]));}
  const out=document.querySelector('#detector-result');
  if(!channels[0].length){out.textContent='Choose an opaque area of your skin.';drawSample();return;}
  const rgb=channels.map(c=>{c.sort((a,b)=>a-b);return c[Math.floor(c.length/2)];});const result=rankSkinSample(rgb);
  out.innerHTML=result.error?`<p>${esc(result.error)}</p>`:`<h4>Your sample has a ${esc(result.cast)} color cast</h4><p>${esc(result.explanation)}</p><p>Palettes to compare, not a definitive result:</p>${result.names.map(n=>`<button class="quiet" data-detected="${esc(n)}">Compare ${esc(n)}</button>`).join('')}`;
  drawSample();
 }
 canvas.addEventListener('click',e=>{const box=canvas.getBoundingClientRect();point={x:(e.clientX-box.left)*canvas.width/box.width,y:(e.clientY-box.top)*canvas.height/box.height};analyze();});
 canvas.addEventListener('keydown',e=>{const moves={ArrowLeft:[-8,0],ArrowRight:[8,0],ArrowUp:[0,-8],ArrowDown:[0,8]};if(e.key==='Enter'){e.preventDefault();analyze();}else if(moves[e.key]){e.preventDefault();point.x=Math.max(0,Math.min(canvas.width-1,point.x+moves[e.key][0]));point.y=Math.max(0,Math.min(canvas.height-1,point.y+moves[e.key][1]));drawSample();}});
 document.querySelector('#analyze-skin').onclick=analyze;
 document.querySelector('#detector-result').onclick=e=>{const b=e.target.closest('[data-detected]');if(!b)return;sides[0]={season:stylingData.catalog.findIndex(p=>p.name===b.dataset.detected),color:0};renderStudio();status.textContent=`Comparing ${b.dataset.detected} in palette A. Use its button below to save it.`;};
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
   source=image;const scale=Math.min(1,700/image.naturalWidth,700/image.naturalHeight);canvas.width=Math.max(1,Math.round(image.naturalWidth*scale));canvas.height=Math.max(1,Math.round(image.naturalHeight*scale));point={x:canvas.width/2,y:canvas.height/2};drawSample();document.querySelector('#detector').hidden=false;document.querySelector('#detector-result').textContent='Select a skin area to get an estimate.';
   document.querySelector('#remove-photo').disabled=false;renderStudio();status.textContent='Compare the same photo in both frames. Tap a swatch to try each color, then choose a palette.';
  }catch{URL.revokeObjectURL(candidate);if(ticket===generation)status.textContent='Could not open this image. Try a smaller JPEG, PNG, or WebP (under 40 megapixels).';}
  event.target.value='';
 });
 document.querySelector('#remove-photo').addEventListener('click',()=>{generation++;if(portraitURL)URL.revokeObjectURL(portraitURL);portraitURL=null;source=null;ctx.clearRect(0,0,canvas.width,canvas.height);document.querySelector('#detector').hidden=true;document.querySelector('#detector-result').textContent='';document.querySelector('#portrait-file').value='';document.querySelector('#remove-photo').disabled=true;status.textContent='Photo removed from this tab.';renderStudio();});
 renderStudio();
})();
