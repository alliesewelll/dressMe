const {evaluationMarkup}=require('./evaluation.js');
const assert=require('node:assert/strict');
const metric={recommendation:'BUY',recommendation_count:3,feedback_count:2,feedback_coverage:2/3,like_rate:0,purchase_rate:null,average_rating:null,purchase_response_count:0,rating_count:0};
const html=evaluationMarkup([metric],s=>s);
assert.ok(html.includes('67%'));assert.ok(html.includes('0%'));assert.ok(html.includes('Not enough data'));assert.ok(html.includes('Not rated'));assert.ok(html.includes('Purchases: 0 answers'));
assert.ok(evaluationMarkup([{...metric,average_rating:4.25}],s=>s).includes('4.3 / 5'));
assert.equal(evaluationMarkup([],s=>s),'');
console.log('7 evaluation display checks passed');
