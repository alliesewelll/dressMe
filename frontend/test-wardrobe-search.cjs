const assert = require('node:assert/strict');
const {filterWardrobe} = require('./wardrobe-search.js');
const items = [
 {item_name:'Weekend shirt',primary_color:'Pink',material:'Linen',brand:'Example',category:' Tops ',pattern:'Striped'},
 {item_name:'Pink skirt',category:'Bottoms',material:'Cotton'},
 {item_name:'Gift',category:null,brand:null},
];
assert.equal(filterWardrobe(items,' PINK   linen ')[0],items[0]);
assert.equal(filterWardrobe(items,'pink linen').length,1);
assert.equal(filterWardrobe(items,'EXAMPLE striped','tops').length,1);
assert.equal(filterWardrobe(items,'pink','Bottoms')[0],items[1]);
assert.equal(filterWardrobe(items,'pink linen','Bottoms').length,0);
assert.deepEqual(filterWardrobe(items,''),items);
assert.equal(filterWardrobe(items,'not-found').length,0);
assert.equal(filterWardrobe(items,'ＰＩＮＫ').length,2);
assert.equal(items[0].category,' Tops ');
const complete = {item_name: 'Complete shirt', category: 'Tops', primary_color: 'pink', material: 'linen', pattern: 'solid', subcategory: 'shirt'};
const missing = {...complete, material: '  '};
const closet = [complete, missing];
assert.deepEqual(filterWardrobe(closet, '', '', true), [missing]);
assert.deepEqual(filterWardrobe(closet, 'pink', 'tops', true), [missing]);
assert.deepEqual(filterWardrobe(closet, 'linen', '', true), []);
assert.deepEqual(filterWardrobe(closet, '', 'Bottoms', true), []);
assert.deepEqual(filterWardrobe(closet, ''), closet);
for (const field of ['primary_color', 'category', 'material', 'pattern', 'subcategory']) {
 for (const blank of [null, undefined, '', '  ']) {
  const piece = {...complete, [field]: blank};
  assert.deepEqual(filterWardrobe([piece], '', '', true), [piece]);
 }
}
missing.material = 'cotton';
assert.deepEqual(filterWardrobe(closet, '', '', true), []);
console.log('Wardrobe search checks passed, including combined missing-detail filters and completed edits.');
const {sortWardrobe} = require('./wardrobe-search.js');
const sortable = [{item_id:3,item_name:'Zebra',times_worn:2},{item_id:2,item_name:'Apple',times_worn:0},{item_id:1,item_name:'apple',times_worn:0}];
const ids = rows => rows.map(row => row.item_id);
assert.deepEqual(ids(sortWardrobe(sortable, 'least-worn')), [1,2,3]);
assert.deepEqual(ids(sortWardrobe(sortable, 'most-worn')), [3,1,2]);
assert.deepEqual(ids(sortWardrobe(sortable, 'name')), [1,2,3]);
assert.deepEqual(ids(sortWardrobe(sortable)), [3,2,1]);
assert.deepEqual(ids(sortable), [3,2,1]);
assert.deepEqual(sortWardrobe([], 'name'), []);
assert.deepEqual(ids(sortWardrobe(filterWardrobe(sortable, 'apple'), 'least-worn')), [1,2]);
sortable[2].times_worn = 5;
assert.deepEqual(ids(sortWardrobe(sortable, 'least-worn')), [2,3,1]);
console.log('Sorting checks passed: wear counts, names, ties, filtering, and unchanged source order.');
