// Experimental photo-color heuristic, not a trained or validated season classifier.
(function(root){
 function rankSample(rgb){
  if(rgb.length!==3||rgb.some(v=>!Number.isFinite(v)||v<0||v>255))throw new Error('Invalid RGB sample');
  const [r,g,b]=rgb, max=Math.max(...rgb), min=Math.min(...rgb);
  if(max>248&&min>230) return {error:'This sample looks overexposed. Try a less bright patch of skin.'};
  if(max<25) return {error:'This sample is too dark to analyze. Try better, even lighting.'};
  // Relative yellow versus red cast; camera white balance can change this substantially.
  const cast=(g-b)/Math.max(r-b,1);
  const warm=cast>=0.42;
  const nearBoundary=Math.abs(cast-0.42)<0.09;
  const names=warm?['True Spring','True Autumn','Soft Autumn']:['True Summer','True Winter','Soft Summer'];
  if(nearBoundary) names.splice(1,1,warm?'True Summer':'True Spring');
  return {names,cast:nearBoundary?'mixed':warm?'golden':'rosy',sample:rgb.map(Math.round),
   explanation:'This shortlist uses only the yellow-to-red balance in the selected pixels. It cannot determine your natural undertone, contrast, or exact subtype from one photo.'};
 }
 root.rankSkinSample=rankSample;
 if(typeof module!=='undefined')module.exports={rankSample};
})(typeof window!=='undefined'?window:globalThis);
