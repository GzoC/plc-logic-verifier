// Run from the repository root after acquiring the pinned WASM and running the local CLI.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync as read, writeFileSync as write} from 'node:fs';
const dir = 'docs/evidence/verification-2026-11-17/';
const mod = '.local/ironplc/runtime.mjs', bin = '.local/ironplc/runtime.wasm';
const hash = p => createHash('sha256').update(read(p)).digest('hex');
assert.equal(hash(mod),'80f34fd0403cce95dd0f78f2b151f14bf2862aaa6fde7e60d121f94650d692e6');
assert.equal(hash(bin),'4616f6016b57fad47016faf8e83946a26b5699647ba6ddc3f27db22b54a0ea2c');
const vm = await import('../'+mod);
await vm.default({module_or_path:read(bin)});
assert.equal(vm.version(),'0.254.0');
const result=JSON.parse(read('.local/ironplc/result.json'));
assert.equal(result.status,'PASS');
assert.equal(result.program_sha256,hash(dir+'shared.st'));
assert.equal(JSON.parse(vm.load_program(read(dir+'shared.st','utf8'),50000,'','','')).ok,true);
const rows=[];
for(const sample of result.trace){
 const step=JSON.parse(vm.step(1)); assert.equal(step.ok,true);assert.equal(step.total_scans,sample.scan+1);
 const map=new Map(step.variables.map(v=>[v.name.toUpperCase(),v]));
 const clock=map.get('__SYSTEM_UP_TIME').value;
 assert.equal(clock,`T#${sample.time_ms}ms`);
 const external={}, differences=[];
 for(const [key,v] of Object.entries(sample.variables)){
  const {type_name,value}=map.get(key);
  assert.ok(type_name==='INT'||(type_name==='BOOL'&&['TRUE','FALSE'].includes(value)));
  external[key]=type_name==='INT'?Number(value):value==='TRUE';
  if(external[key]!==v) differences.push(key);
 }
 rows.push({scan:sample.scan,time_ms:sample.time_ms,clock,verifier:sample.variables,external,differences});
}
assert.equal(rows.length,8);
write(dir+'runtime.json',JSON.stringify({version:vm.version(),module_sha256:hash(mod),wasm_sha256:hash(bin),source_sha256:hash(dir+'shared.st'),rows},null,2)+'\n');
assert.deepEqual(rows.map(r=>r.differences),[['Q0'],[],[],[],[],['Q0'],[],[]]);
console.log(rows.map(r=>[r.time_ms,r.differences]));
