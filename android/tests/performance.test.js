'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const perf = require('../web/android-performance.js');

test('presets map to bounded real engine CVars, preserving Android compiler workarounds', () => {
  assert.deepEqual(perf.cvars(perf.PRESETS.cool), {
    renderScale:'0.50',farclip:'177',WorldDetail:'0',spellEffectLevel:'0',
    weatherDensity:'0',ffxGlow:'0',pbr_lite:'1',pipe_warm:'0',
  });
  assert.equal(perf.cvars(perf.PRESETS.balanced).renderScale, '0.75');
  assert.equal(perf.cvars(perf.PRESETS.clear).weatherDensity, '3');
  assert.equal(perf.cvars({resolution:10,distance:9999,detail:-99}).renderScale, '0.50');
  assert.equal(perf.cvars({resolution:10,distance:9999,detail:-99}).farclip, '420');
});
test('malformed preferences cannot introduce arbitrary settings or nonfinite values', () => {
  assert.deepEqual(perf.normalize(null),perf.ORIGINAL);
  assert.deepEqual(perf.normalize([]),perf.ORIGINAL);
  assert.equal(perf.normalize({resolution:false}).resolution,100);
  assert.equal(perf.normalize({resolution:'NaN'}).resolution,100);
  assert.equal(perf.normalize({detail:Infinity}).detail,2);
  assert.equal(perf.cvars({arbitraryCommand:'unsafe'}).arbitraryCommand,undefined);
});
test('TOML update touches only bounded graphic CVars, preserving other fields and sections', () => {
  const input = '# original comment\n[cvars]\nrealmName = "Elwynn Forest"\nrenderScale = "1.25"\nscriptMemory = "0"\n[other]\nrenderScale = "leave me"\n';
  const output = perf.mergeConfig(input,perf.cvars(perf.PRESETS.cool));
  assert.ok(output.includes('realmName = "Elwynn Forest"'));
  assert.ok(output.includes('scriptMemory = "0"'));
  assert.ok(output.includes('[other]\nrenderScale = "leave me"'));
  assert.equal(output.match(/renderScale = "0.50"/g).length,1);
  assert.ok(output.includes('pbr_lite = "1"'));
  assert.equal(perf.mergeConfig('',{bad:'oops'}),'\n[cvars]');
  assert.throws(()=>perf.mergeConfig('x'.repeat(1024*1024+1),{}));
});
test('thermal values come only from sane system readings, with no string or fake fallback', () => {
  assert.deepEqual(perf.thermal({batteryCelsius:38.4,thermalStatus:2}),{batteryCelsius:38.4,thermalStatus:2});
  assert.deepEqual(perf.thermal({batteryCelsius:'38',thermalStatus:20}),{batteryCelsius:null,thermalStatus:-1});
  assert.deepEqual(perf.thermal({batteryCelsius:999,thermalStatus:1.5}),{batteryCelsius:null,thermalStatus:-1});
});
function browserContext(preference,host='127.0.0.1',config=null,marker=null) {
  const store = new Map();
  store.set(perf.CONFIG_KEY,config === null ? '# benilla\n[cvars]\nrealmName = "Elwynn Forest"\n' : config);
  if(marker) store.set(perf.HUD_MIGRATION_KEY,marker);
  store.set('rogue.characters','untouched-account-data');
  if(preference) store.set(perf.STORAGE_KEY,JSON.stringify(preference));
  const window={};window.top=window;
  const context={window,Event:class{constructor(type){this.type=type;}},location:{hostname:host},
    localStorage:{getItem:key=>store.get(key)||null,setItem:(key,value)=>store.set(key,value)},
    document:{readyState:'loading',addEventListener(){},dispatchEvent(){}}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../web/android-performance.js'),'utf8'),context);
  return {window,store};
}
test('boot hook applies a pending choice once after original env defaults without touching URL/timing/save', () => {
  const {window,store}=browserContext({...perf.PRESETS.cool,pending:true});
  window.__wenilla_env={farclip:'420',pipe_warm:'0',pbr_lite:'1'};
  assert.equal(window.__wenilla_env.renderScale,undefined);
  window.__azerothAndroidPerformance.applyBootOptions();
  assert.equal(window.__wenilla_env.renderScale,'0.50');
  assert.equal(window.__wenilla_env.farclip,'177');
  assert.equal(JSON.parse(store.get(perf.STORAGE_KEY)).pending,false);
  assert.equal(store.get('rogue.characters'),'untouched-account-data');
  window.__wenilla_env.renderScale='0.85';
  window.__azerothAndroidPerformance.applyBootOptions();
  assert.equal(window.__wenilla_env.renderScale,'0.85');
  assert.equal(window.requestAnimationFrame,undefined);
});
test('first install and consumed choices never overwrite original game graphics', () => {
  for(const preference of [null,{...perf.PRESETS.cool,pending:false}]) {
    const {window,store}=browserContext(preference);
    const original=store.get(perf.CONFIG_KEY);
    window.__wenilla_env={farclip:'420'};
    window.__azerothAndroidPerformance.applyBootOptions();
    assert.equal(window.__wenilla_env.renderScale,undefined);
    assert.ok(store.get(perf.CONFIG_KEY).startsWith(original));
    assert.equal(window.__wenilla_env.hudScale,'0.50');
    assert.equal(store.get(perf.HUD_MIGRATION_KEY),'done');
  }
  const {window}=browserContext({...perf.PRESETS.cool,pending:true},'example.com');
  assert.equal(window.__azerothAndroidPerformance,undefined);
});

test('compact HUD migration only adds HUD on first adapter3 boot, leaving graphic and account settings intact', () => {
  const config = '# retain comments\n[cvars]\nrenderScale = "0.85"\nfarclip = "350"\nrealmName = "Elwynn Forest"\n[other]\nvalue = "keep"\n';
  const {window,store} = browserContext(null,'127.0.0.1',config);
  window.__wenilla_env = {farclip:'420'};
  window.__azerothAndroidPerformance.applyBootOptions();
  assert.equal(window.__wenilla_env.hudScale,'0.50');
  assert.equal(window.__wenilla_env.renderScale,undefined);
  assert.equal(window.__wenilla_env.farclip,'350');
  assert.ok(store.get(perf.CONFIG_KEY).includes('renderScale = "0.85"'));
  assert.ok(store.get(perf.CONFIG_KEY).includes('farclip = "350"'));
  assert.ok(store.get(perf.CONFIG_KEY).includes('[other]\nvalue = "keep"'));
  assert.equal(store.get('rogue.characters'),'untouched-account-data');
  assert.equal(store.get(perf.STORAGE_KEY),undefined);
});
test('any explicit HUD preference is preserved, including quoted key spelling and user values outside slider range', () => {
  for(const key of ['hudScale','"hudScale"',"'hudScale'",'HUDSCALE']) {
    const config = `[cvars]\n${key} = "0.65" # user choice\nrenderScale = "0.85"\n`;
    const {window,store} = browserContext(null,'127.0.0.1',config);
    window.__wenilla_env = {farclip:'420'};
    window.__azerothAndroidPerformance.applyBootOptions();
    assert.equal(store.get(perf.CONFIG_KEY),config);
    assert.equal(window.__wenilla_env.hudScale,undefined);
    assert.equal(store.get(perf.HUD_MIGRATION_KEY),'done');
  }
});
test('completed HUD migration never reapplies when user later resets or edits in-game HUD', () => {
  for(const config of ['[cvars]\n','[cvars]\nhudScale = "0.95"\n']) {
    const {window,store} = browserContext(null,'127.0.0.1',config,'done');
    window.__wenilla_env = {farclip:'420'};
    window.__azerothAndroidPerformance.applyBootOptions();
    assert.equal(store.get(perf.CONFIG_KEY),config);
    assert.equal(window.__wenilla_env.hudScale,undefined);
  }
});
test('pending HUD-only adjustment does not reset existing resolution, terrain or effect detail', () => {
  const config='[cvars]\nhudScale = "0.75"\nrenderScale = "0.85"\nfarclip = "350"\nWorldDetail = "1"\n';
  const {window,store}=browserContext({...perf.PRESETS.clear,hudScale:90,pending:true,pendingFields:['hudScale']},'127.0.0.1',config,'done');
  window.__wenilla_env={farclip:'420'};
  window.__azerothAndroidPerformance.applyBootOptions();
  assert.equal(window.__wenilla_env.hudScale,'0.90');
  assert.equal(window.__wenilla_env.renderScale,undefined);
  assert.equal(window.__wenilla_env.WorldDetail,undefined);
  assert.ok(store.get(perf.CONFIG_KEY).includes('renderScale = "0.85"'));
  assert.ok(store.get(perf.CONFIG_KEY).includes('farclip = "350"'));
  assert.ok(store.get(perf.CONFIG_KEY).includes('WorldDetail = "1"'));
  assert.equal(JSON.parse(store.get(perf.STORAGE_KEY)).pending,false);
});

test('every cold boot restores actual saved terrain distance over upstream 420 without rewriting config', () => {
  for(const actual of ['177','350','777']) {
    const config=`# keep this\n[cvars]\nfarclip = "${actual}"\nhudScale = "0.85"\nrenderScale = "0.90"\n`;
    const {window,store}=browserContext({...perf.PRESETS.cool,pending:false},'127.0.0.1',config,'done');
    window.__wenilla_env={farclip:'420',pbr_lite:'1'};
    window.__azerothAndroidPerformance.applyBootOptions();
    assert.equal(window.__wenilla_env.farclip,actual);
    assert.equal(window.__wenilla_env.renderScale,undefined);
    assert.equal(store.get(perf.CONFIG_KEY),config);
  }
});

function frameEnvironment() {
  let clock = 1000, next = 1;
  const nativeJobs = new Map(), canceled = [], target = {}, perfClock = {};
  const gate = perf.createFrameGate({
    request(owner, callback) { assert.equal(owner,target); const id=next++;nativeJobs.set(id,callback);return id; },
    cancel(owner,id) { assert.equal(owner,target);canceled.push(id);nativeJobs.delete(id); },
    now:()=>clock, performanceObject:perfClock,
  });
  return {gate,target,perfClock,nativeJobs,canceled,setClock:value=>clock=value,
    fire(timestamp=clock) {const jobs=[...nativeJobs.values()];nativeJobs.clear();for(const callback of jobs)callback(timestamp);}};
}
test('engine frame gate holds existing callbacks while panel is open and restores them exactly once',()=>{
  const h=frameEnvironment(),values=[];
  h.gate.requestFrame(h.target,at=>values.push(at));
  assert.equal(h.nativeJobs.size,1);
  h.gate.setPanelOpen(true);h.gate.setPanelOpen(true);
  assert.equal(h.nativeJobs.size,0);assert.equal(h.gate.pendingCount(),1);
  h.setClock(6000);h.fire();assert.deepEqual(values,[]);
  h.gate.setPanelOpen(false);h.gate.setPanelOpen(false);
  assert.equal(h.nativeJobs.size,1);
  h.fire(6016);assert.deepEqual(values,[1016]);
  assert.equal(h.gate.pendingCount(),0);h.fire(6032);assert.deepEqual(values,[1016]);
});
test('engine-only monotonic clock freezes and excludes every panel interval, while Date timestamps remain real',()=>{
  const h=frameEnvironment(),date={now:()=>1700000000000};
  h.gate.setPanelOpen(true);h.setClock(3000);
  assert.equal(h.gate.monotonicNow(h.perfClock),1000);
  assert.equal(h.gate.monotonicNow(date),1700000000000);
  h.gate.setPanelOpen(false);h.setClock(3100);
  assert.equal(h.gate.monotonicNow(h.perfClock),1100);
  h.gate.setPanelOpen(true);h.setClock(5100);h.gate.setPanelOpen(false);
  assert.equal(h.gate.monotonicNow(h.perfClock),1100);
  h.setClock(5116);assert.equal(h.gate.monotonicNow(h.perfClock),1116);
});
test('requests made while panel is open remain cancelable and are never lost or duplicated',()=>{
  const h=frameEnvironment(),values=[];
  h.gate.setPanelOpen(true);
  const kept=h.gate.requestFrame(h.target,()=>values.push('kept'));
  const removed=h.gate.requestFrame(h.target,()=>values.push('removed'));
  assert.notEqual(kept,removed);assert.equal(h.nativeJobs.size,0);
  h.gate.cancelFrame(h.target,removed);h.gate.cancelFrame(h.target,removed);
  assert.equal(h.gate.pendingCount(),1);
  h.gate.setPanelOpen(false);h.fire();assert.deepEqual(values,['kept']);
});
test('cancellation also suppresses already-queued native callbacks and rejects a wrong target',()=>{
  const h=frameEnvironment(),values=[];
  const id=h.gate.requestFrame(h.target,()=>values.push('unexpected'));
  const stale=[...h.nativeJobs.values()][0];
  h.gate.cancelFrame({},id);assert.equal(h.gate.pendingCount(),1);
  h.gate.cancelFrame(h.target,id);stale(1016);
  assert.deepEqual(values,[]);assert.equal(h.gate.pendingCount(),0);
});
test('engine callbacks can schedule the next frame after closing the panel without a dead loop',()=>{
  const h=frameEnvironment(),values=[];
  h.gate.requestFrame(h.target,at=>{values.push(at);h.gate.requestFrame(h.target,next=>values.push(next));});
  h.fire(1016);assert.deepEqual(values,[1016]);assert.equal(h.nativeJobs.size,1);
  h.gate.setPanelOpen(true);h.setClock(9000);h.gate.setPanelOpen(false);
  h.fire(9032);assert.deepEqual(values,[1016,1032]);assert.equal(h.gate.pendingCount(),0);
});
test('invalid callbacks and scheduler failure cannot leave engine frame handles behind',()=>{
  const h=frameEnvironment();assert.throws(()=>h.gate.requestFrame(h.target,null),TypeError);
  const gate=perf.createFrameGate({request(){throw new Error('closed');},cancel(){},now:()=>0,performanceObject:{}});
  assert.throws(()=>gate.requestFrame({},()=>{}),/closed/);assert.equal(gate.pendingCount(),0);
});


test('v3 migrates saved default 100% and the old adapter 75%, preserving other custom sizes',()=>{
  for(const [value,legacy,expected] of [['1',null,true],['0.75','done',true],['0.75',null,false],['0.65','done',false],['0.9','done',false],['0.5',null,false]]){
    assert.equal(perf.shouldCompactHud({found:true,value},legacy),expected);
  }
  assert.equal(perf.shouldCompactHud({found:false,value:null},null),true);
  assert.equal(perf.shouldCompactHud({found:true,value:'invalid'},'done'),false);
});
test('v3 migration corrects persisted default 100% once and leaves a later user 100% reset alone',()=>{
  const config='[cvars]\nhudScale = "1"\nrenderScale = "0.85"\n';
  const h=browserContext(null,'127.0.0.1',config);
  h.window.__wenilla_env={farclip:'420'};h.window.__azerothAndroidPerformance.applyBootOptions();
  assert.equal(h.window.__wenilla_env.hudScale,'0.50');
  assert.ok(h.store.get(perf.CONFIG_KEY).includes('hudScale = "0.50"'));
  assert.ok(h.store.get(perf.CONFIG_KEY).includes('renderScale = "0.85"'));
  const reset=browserContext(null,'127.0.0.1',config,'done');
  reset.window.__wenilla_env={};reset.window.__azerothAndroidPerformance.applyBootOptions();
  assert.equal(reset.window.__wenilla_env.hudScale,undefined);assert.equal(reset.store.get(perf.CONFIG_KEY),config);
});
test('old adapter marker allows its 75% default to migrate while a pending user HUD choice wins',()=>{
  const h=browserContext(null,'127.0.0.1','[cvars]\nhudScale = "0.75"\n');
  h.store.set(perf.LEGACY_HUD_MIGRATION_KEY,'done');h.window.__wenilla_env={};
  h.window.__azerothAndroidPerformance.applyBootOptions();assert.equal(h.window.__wenilla_env.hudScale,'0.50');
  const chosen=browserContext({hudScale:85,pending:true,pendingFields:['hudScale']},'127.0.0.1','[cvars]\nhudScale = "1"\n');
  chosen.window.__wenilla_env={};chosen.window.__azerothAndroidPerformance.applyBootOptions();
  assert.equal(chosen.window.__wenilla_env.hudScale,'0.85');assert.equal(chosen.store.get('rogue.characters'),'untouched-account-data');
});
