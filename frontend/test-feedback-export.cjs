const vm = require('node:vm'), fs = require('node:fs'), assert = require('node:assert/strict');
const button = {}, status = {}, events = {};
let resolve, downloads = 0, revoked = 0, path;
const context = vm.createContext({mode:'demo', user:1,
 document:{querySelector:id=>id==='#download-feedback'?button:status,
 body:{appendChild(){}},createElement:()=>({click(){downloads++},remove(){}})},
 window:{addEventListener:(name,fn)=>events[name]=fn},
 fetch:url=>{path=url;return new Promise(r=>resolve=r)},
 AbortSignal:{timeout:()=>null}, URL:{createObjectURL:()=> 'blob:test',revokeObjectURL:()=>revoked++},setTimeout:fn=>fn()});
vm.runInContext(fs.readFileSync(__dirname+'/feedback-export.js','utf8'),context);
const ok = {ok:true,headers:{get:()=> 'text/csv; charset=utf-8'},blob:async()=>({})};
(async()=>{
 assert.equal(button.disabled,true);await button.onclick();assert.equal(downloads,0);
 context.mode='live';events['wardrobe-context']();
 let pending=button.onclick();resolve(ok);await pending;
 assert.equal(path,'/users/1/feedback-features.csv');assert.equal(downloads,1);assert.equal(revoked,1);
 pending=button.onclick();context.user=2;events['wardrobe-context']();resolve(ok);await pending;assert.equal(downloads,1);
 pending=button.onclick();resolve({ok:false,status:500});await pending;
 assert.match(status.textContent,/try again/);assert.equal(button.disabled,false);
 pending=button.onclick();resolve({...ok,headers:{get:()=> 'text/html'}});await pending;
 assert.equal(downloads,1);assert.match(status.textContent,/did not return a CSV/);
 console.log('CSV export checks passed: demo, success, user switch, failure, content type, URL cleanup.');
})().catch(e=>{console.error(e);process.exitCode=1});
