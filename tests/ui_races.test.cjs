// Execute the actual shipped script with controlled network promises and a small DOM adapter.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {webcrypto,createHash}=require('node:crypto');
const script=fs.readFileSync('src/plc_verifier/ui.html','utf8').split('<script>')[1].split('</script>')[0];
const hash=s=>createHash('sha256').update(s).digest('hex');
function setup(){
  const elements=new Map(), requests=[];
  function el(id){if(!elements.has(id))elements.set(id,{value:'',checked:false,style:{},dataset:{},textContent:'',disabled:false,children:[],append(x){this.children.push(x);},replaceChildren(){this.children=[];},scrollIntoView(){}});return elements.get(id);}
  const ctx=vm.createContext({document:{getElementById:el,createElement:()=>({append(){},style:{},click(){}}),querySelectorAll:()=>[]},fetch:(path,opts)=>{
    if(path==='/examples')return Promise.resolve({json:async()=>[]});
    return new Promise(resolve=>requests.push({path,body:JSON.parse(opts.body),resolve:(body)=>resolve({ok:true,json:async()=>body,text:async()=>body})}));
  },crypto:webcrypto,TextEncoder,Uint8Array,Blob,URL,setTimeout});
  vm.runInContext(script,ctx);
  el('source').value='OLD';el('scenario').value='YAML';
  function response(req){return {status:'PASS',engine_version:'0.1.0',program_sha256:hash(req.body.source),scenario_sha256:hash(req.body.scenario),trace:[],requirements:[],error:null,semantics:{}};}
  return {el,ctx,requests,response,visible:()=>el('result').style.display==='block'};
}
for(const field of ['source','scenario'])test(`late run discarded after ${field} edit`,async()=>{
  const h=setup(),pending=h.el('run').onclick();h.el(field).value='NEW';h.el(field).oninput();h.requests[0].resolve(h.response(h.requests[0]));await pending;assert.equal(h.visible(),false);assert.equal(vm.runInContext('result',h.ctx),null);
});
test('changing example discards old response',async()=>{
  const h=setup(),pending=h.el('run').onclick();vm.runInContext("catalog=[{source:'NEW',scenario:'OTHER'}]",h.ctx);h.el('examples').value='0';h.el('load').onclick();h.requests[0].resolve(h.response(h.requests[0]));await pending;assert.equal(h.visible(),false);
});
test('reverse responses retain only latest execution and hashes',async()=>{
  const h=setup(),first=h.el('run').onclick();h.el('source').value='NEW';h.el('source').oninput();const second=h.el('run').onclick();h.requests[1].resolve(h.response(h.requests[1]));await second;h.requests[0].resolve(h.response(h.requests[0]));await first;assert.equal(h.visible(),true);assert.equal(vm.runInContext('executed.source',h.ctx),'NEW');assert.equal(vm.runInContext('result.program_sha256',h.ctx),hash('NEW'));
});
test('mismatched response hashes are never rendered',async()=>{
  const h=setup(),p=h.el('run').onclick();h.requests[0].resolve({...h.response(h.requests[0]),program_sha256:hash('OTHER')});await p;assert.equal(h.visible(),false);
});
async function run(h){const p=h.el('run').onclick();const r=h.requests.at(-1);r.resolve(h.response(r));await p;}
test('preview uses executed snapshot and ignores late response after edit',async()=>{
  const h=setup();await run(h);const p=h.el('preview').onclick(),r=h.requests.at(-1);assert.equal(r.body.source,'OLD');h.el('source').value='NEW';h.el('source').oninput();r.resolve({payload:{status:'PASS'}});await p;assert.equal(h.el('payload').value,'');assert.equal(h.el('send').disabled,true);
});
test('reverse previews preserve latest selection',async()=>{
  const h=setup();await run(h);const a=h.el('preview').onclick(),old=h.requests.at(-1);h.el('reqSelect').value='R2';h.el('reqSelect').oninput();const b=h.el('preview').onclick(),latest=h.requests.at(-1);latest.resolve({payload:{selected:'R2'}});await b;old.resolve({payload:{selected:'OLD'}});await a;assert.equal(JSON.parse(h.el('payload').value).selected,'R2');
});
test('oversized local draft is editable but cannot be authorized; reduction works',async()=>{
  const h=setup();await run(h);const p=h.el('preview').onclick();h.requests.at(-1).resolve({payload:{data:'x'.repeat(25000)}});await p;assert.equal(h.el('authorize').disabled,true);h.el('payload').value='{"reduced":true}';h.el('payload').oninput();assert.equal(h.el('send').disabled,true);h.el('authorize').onclick();assert.equal(h.el('send').disabled,false);
});
test('late explanation cannot overwrite a changed draft or new source',async()=>{
  for(const edit of ['payload','source']){const h=setup();await run(h);h.el('payload').value='{"selected":true}';h.el('payload').oninput();h.el('authorize').onclick();const p=h.el('send').onclick(),r=h.requests.at(-1);h.el(edit).value=edit==='payload'?'{}':'NEW';h.el(edit).oninput();r.resolve({advice:'STALE'});await p;assert.ok(!h.el('advice').textContent.includes('STALE'));assert.equal(h.el('send').disabled,true);}
});
test('file selection invalidates immediately, delayed file reads cannot overwrite edits',async()=>{
  const h=setup();await run(h);let resolve;h.el('stfile').files=[{size:3,text:()=>new Promise(r=>resolve=r)}];const p=h.el('stfile').onchange();assert.equal(h.visible(),false);h.el('source').value='NEW';h.el('source').oninput();resolve('FILE');await p;assert.equal(h.el('source').value,'NEW');
});
