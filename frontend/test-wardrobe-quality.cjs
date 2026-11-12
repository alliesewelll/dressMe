const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const nodes = Object.fromEntries(['#check-wardrobe-quality', '#wardrobe-quality-status', '#wardrobe-quality-results'].map(id => [id, {}]));
const events = {};
let resolve;
const context = vm.createContext({document: {querySelector: id => nodes[id]},
 window: {addEventListener: (name, fn) => events[name] = fn}, mode: 'demo',
 api: path => {assert.equal(path, 'wardrobe-quality'); return new Promise(r => resolve = r);},
 esc: value => String(value).replaceAll('<', '&lt;')});
vm.runInContext(fs.readFileSync(__dirname + '/wardrobe-quality.js', 'utf8'), context);
(async () => {
 const button = nodes['#check-wardrobe-quality'], status = nodes['#wardrobe-quality-status'], results = nodes['#wardrobe-quality-results'];
 assert.equal(button.disabled, true);
 await button.onclick(); assert.equal(resolve, undefined);
 context.mode = 'live'; events['wardrobe-context']();
 const report = {item_count: 60, items_with_missing_details: 55, missing_counts: {primary_color: 55},
  items: [{item_name: '<Shirt>', missing_fields: ['primary_color']}], truncated: true};
 let request = button.onclick(); resolve(report); await request;
 assert.match(status.textContent, /55 of 60/);
 assert.match(results.innerHTML, /&lt;Shirt>/);
 assert.match(results.innerHTML, /Missing: color/);
 assert.match(results.innerHTML, /color: 55/);
 assert.match(results.innerHTML, /Showing 1 pieces/);
 request = button.onclick(); context.mode = 'demo'; events['wardrobe-context'](); resolve(report); await request;
 assert.equal(results.innerHTML, ''); assert.equal(button.disabled, true);
 assert.match(status.textContent, /Connect/);
 context.mode = 'live'; events['wardrobe-context']();
 request = button.onclick(); resolve({item_count: 0}); await request;
 assert.match(status.textContent, /Add a piece/);
 request = button.onclick(); resolve({item_count: 2, items_with_missing_details: 0}); await request;
 assert.match(status.textContent, /All your pieces/); assert.equal(results.innerHTML, '');
 context.api = async () => {throw new Error('Offline');}; await button.onclick();
 assert.match(status.textContent, /Try again/); assert.equal(button.disabled, false);
 console.log('Wardrobe detail checks passed: rendering, empty/complete, stale response, demo, and retry.');
})().catch(error => {console.error(error); process.exitCode = 1;});
