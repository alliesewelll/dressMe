const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(__dirname + '/app.js', 'utf8');
const fields = Object.fromEntries(['item_name','category','primary_color','brand','subcategory','material','pattern'].map(key => [key, {value: ''}]));
fields.category.options = [{value: 'Tops'}];
fields.category.add = option => fields.category.options.push(option);
const title = {}, button = {}, message = {};
const form = {elements: fields, reset() {for (const field of Object.values(fields)) field.value = ''; fields.category.value = 'Tops';}, querySelector: key => key === 'h2' ? title : button};
let calls = [];
const context = vm.createContext({mode:'demo',user:1,items:[{item_id:1,item_name:'Shirt',category:'Custom',material:'cotton',times_worn:9}],
 $: key => key === '#item-form' ? form : message, show() {}, render() {},
 Option: function(text,value) {this.value=value;},
 FormData: function() {return Object.entries(fields).map(([key,field]) => [key,field.value]);},
 api: async (...args) => {calls.push(args);return {item_id:1,...args[2],times_worn:9};}});
vm.runInContext(source.slice(source.indexOf('let editingItem = null;'), source.indexOf("$('#item-form').onsubmit=")), context);
(async () => {
 vm.runInContext('openItemForm(items[0])', context);
 assert.equal(title.textContent, 'Edit your piece');
 assert.equal(fields.category.value, 'Custom');
 assert.equal(fields.material.value, 'cotton');
 fields.material.value = ' linen '; fields.brand.value = '';
 await context.saveItemForm(form);
 assert.equal(context.items.length, 1); assert.equal(context.items[0].times_worn, 9);
 assert.equal(context.items[0].material, 'linen'); assert.equal(context.items[0].brand, null);
 context.mode = 'live'; vm.runInContext('openItemForm(items[0])', context);
 fields.material.value = 'silk'; await context.saveItemForm(form);
 assert.equal(calls[0][0], 'wardrobe/1'); assert.equal(calls[0][1], 'PATCH');
 assert.equal(context.items[0].material, 'silk');
 vm.runInContext('openItemForm(items[0])', context); fields.material.value = 'wool';
 context.api = async () => {throw new Error('Offline');};
 await assert.rejects(context.saveItemForm(form), /Offline/);
 assert.equal(context.items[0].material, 'silk'); assert.equal(fields.material.value, 'wool');
 context.user = 2; await assert.rejects(context.saveItemForm(form), /wardrobe changed/);
 context.mode = 'demo'; context.openItemForm();
 assert.equal(title.textContent, 'Add a piece'); assert.equal(fields.material.value, '');
 fields.item_name.value = 'New top'; await context.saveItemForm(form);
 assert.equal(context.items.length, 2); assert.equal(context.items[0].times_worn, 0);
 console.log('Item editing checks passed: prefill, demo/live update, wear count, clear, failed save, user change, and add.');
})().catch(error => {console.error(error);process.exitCode=1;});
