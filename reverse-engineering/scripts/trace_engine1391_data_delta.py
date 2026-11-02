#!/usr/bin/env python3
"""1391 source-bound finite declarative-table and browser-bridge delta;0 execution."""
from datetime import datetime,timezone
from pathlib import Path
import difflib,hashlib,json,re,struct,time
import map_engine1391_incremental as base
ROOT=base.ROOT
MAP=ROOT/'evidence/engine1391-refined-static-20261102T134726.927557Z/mapping.json'
MAP_SHA='bc7d702aedfb762bec50929d277f0374fdc74c5121d19dfc25b9328768117e42'
NATIVE=base.SOURCE.parent/'windows-0.139.1/AzerothSurvivors.exe'
NATIVE_SHA='1c0912276637a41a1a971886bb74626577d021af55a313128f85fdbfcc3b2f1d'
ADDRESSES={1390:dict(class_default=5877920,class_table=1601376,race_default=5874636,race_table=1601216,abilities=5882740,zones=5871348),1391:dict(class_default=5874384,class_table=1601176,race_default=5871100,race_table=1601016,abilities=5879204,zones=5867812)}

def main():
 began=time.monotonic();assert base.sha(MAP)==MAP_SHA;mapping=json.loads(MAP.read_text());sourcehash=base.sha(Path(__file__));models={1390:base.catalog(base.OLD,base.OLD_SHA,base.identity139old),1391:base.catalog(base.SOURCE,base.SOURCE_SHA,base.identity139new)}
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('engine1391-data-delta-%Y%m%dT%H%M%S.%fZ');out.mkdir();memories={};decoded={};proof=[]
 for version,model in models.items():
  memory=bytearray(model['static_bounds'][1])
  for s in model['identity']['data_segments']:
   if s['address']is not None:memory[s['address']:s['address']+s['bytes']]=model['raw'][s['file_offset']:s['file_offset']+s['bytes']]
  memories[version]=memory;a=ADDRESSES[version]
  entry=next(e for e in mapping['entries']if e['role']=='constructor');binding=entry['old']if version==1390 else entry['new'];p=MAP.parent/f'{version}-constructor-{binding["index"]}.wat';assert base.sha(p)==binding['wat_sha256'];rows=[x.strip()for x in p.read_text().splitlines()]
  #These are actual literal consumer sequences in full1571/1600, not a search
  #for vaguely similar strings or assumed static-memory relocation.
  for label,sequence in [('class_default',[f'i32.const {a["class_default"]}','local.set 6']),('class_pointer_table',[f'i32.load offset={a["class_table"]}','local.set 6']),('zone_stride_base',['i32.const 152','i32.mul',f'i32.const {a["zones"]}','i32.add']),('ability_match_len',[f'i32.const {a["abilities"]+16}','i32.add','i32.load','i32.eq']),('ability_match_pointer',[f'i32.const {a["abilities"]+12}','i32.add','i32.load']),('ability_limit',['i32.const 88','i32.add','local.tee 4','i32.const 10032','i32.ne']),('race_default',[f'i32.const {a["race_default"]}','local.set 7']),('race_table',[f'i32.load offset={a["race_table"]}','local.set 7'])]:
   sites=[j+1 for j in range(len(rows)-len(sequence)+1)if rows[j:j+len(sequence)]==sequence];assert sites,(version,label);proof.append(dict(version=version,function=binding['index'],body_sha256=binding['body_sha256'],wat_sha256=binding['wat_sha256'],kind=label,relative_sites=sites,instructions=sequence))
  def read(p,n):assert 0<=p<=p+n<=len(memory);return bytes(memory[p:p+n])
  def u(p):return struct.unpack('<I',read(p,4))[0]
  def txt(p,n):return read(p,n).decode('ascii')
  ability=[]
  for i in range(10032//88):
   p=a['abilities']+88*i;raw=read(p,88);payload={str(k):read(u(p+k),u(p+k+4)).hex()for k in(12,20,28,36)}
   scalar=bytearray(raw)
   for k in(12,20,28,36):scalar[k:k+4]=b'\0'*4
   semantic=dict(non_pointer88_hex=bytes(scalar).hex(),resolved_payload_hex=payload)
   ability.append(dict(index=i,pointer=p,ability_id=txt(u(p+12),u(p+16)),effect_tag=u(p),execution_kind=raw[84],school=raw[85],base_damage_bits=u(p+48),raw88_hex=raw.hex(),raw88_sha256=hashlib.sha256(raw).hexdigest(),semantic=semantic,semantic_sha256=hashlib.sha256(json.dumps(semantic,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
  byid={x['ability_id']:x for x in ability};assert len(byid)==114
  classes=[];races=[];zones=[]
  for cls in(1,2,3,4,5,7,8,9,11):
   p=u(a['class_table']+4*(cls-2))if cls>=2 else a['class_default'];name=txt(u(p+40),u(p+44));assert name in byid
   classes.append(dict(class_byte=cls,pointer=p,starter_id=name,hp_bits=u(p+72),armor_bits=u(p+76),numeric8_hex=read(p+72,8).hex(),raw88_hex=read(p,88).hex()))
  for race in range(1,9):
   p=u(a['race_table']+4*(race-2))if race>=2 else a['race_default'];name=txt(u(p+24),u(p+28));d=byid[name]
   races.append(dict(race_byte=race,pointer=p,racial_id=name,effect_tag=d['effect_tag'],execution_kind=d['execution_kind'],raw44_hex=read(p,44).hex()))
  for i in range(12):
   p=a['zones']+152*i;name=txt(u(p+8),u(p+12));zones.append(dict(index=i,pointer=p,identifier=name,x_bits=u(p+104),y_bits=u(p+108),field116_bits=u(p+116),position16_hex=read(p+104,16).hex(),raw152_hex=read(p,152).hex()))
  decoded[version]=dict(addresses=a,abilities=ability,classes=classes,races=races,zones=zones)
 comparisons=[]
 for domain,fields in [('abilities',('ability_id','semantic')),('classes',('class_byte','starter_id','hp_bits','armor_bits')),('races',('race_byte','racial_id','effect_tag','execution_kind')),('zones',('index','identifier','x_bits','y_bits','field116_bits'))]:
  assert len(decoded[1390][domain])==len(decoded[1391][domain])
  for i,(a,b)in enumerate(zip(decoded[1390][domain],decoded[1391][domain])):
   oa={k:a[k]for k in fields};nb={k:b[k]for k in fields};comparisons.append(dict(domain=domain,index=i,fields=list(fields),old=oa,new=nb,equal=oa==nb))
 #Exact complete browser bridge comparison; no comment/wrapper deletion.
 jsold=base.OLD.parent/'official-wenilla.js';jsnew=base.SOURCE.parent/'official-wenilla.js';a=jsold.read_text();b=jsnew.read_text();removed=[]
 bridge_equal=a==b
 (out/'wenilla-bridge.diff').write_text('\n'.join(difflib.unified_diff(a.splitlines(),jsnew.read_text().splitlines(),n=2))+'\n')
 assert base.sha(NATIVE)==NATIVE_SHA;native=NATIVE.read_bytes();references=[]
 def findall(pattern):
  sites=[];at=0
  while len(sites)<33:
   p=native.find(pattern,at)
   if p<0:break
   sites.append(p);at=p+1
  return dict(offsets=sites[:32],truncated=len(sites)>32)
 for x in decoded[1391]['classes']:references.append(dict(kind='class_hp_armor_numeric8',key=x['class_byte'],pattern_hex=x['numeric8_hex'],**findall(bytes.fromhex(x['numeric8_hex']))))
 for x in decoded[1391]['zones']:
  pattern=struct.pack('<II',x['x_bits'],x['y_bits']);references.append(dict(kind='zoneXY_numeric8',key=x['identifier'],pattern_hex=pattern.hex(),**findall(pattern)))
 assert base.sha(Path(__file__))==sourcehash and base.sha(base.SOURCE)==base.SOURCE_SHA
 result=dict(kind='1391_finite_static_declarations_and_bridge_delta_not_gameplay_acceptance',source_wasm_sha256=base.SOURCE_SHA,old_wasm_sha256=base.OLD_SHA,script_sha256=sourcehash,entry_mapping_sha256=MAP_SHA,
  constructor_literal_consumers=proof,decoded={str(k):v for k,v in decoded.items()},comparison=comparisons,semantic_equal=sum(x['equal']for x in comparisons),semantic_total=len(comparisons),
  browser_bridge=dict(old_sha256=base.sha(jsold),new_sha256=base.sha(jsnew),literal_added_wrappers=[],complete_bridge_bytes_equal=bridge_equal,diff_sha256=base.sha(out/'wenilla-bridge.diff')),
  windows_numeric_references=dict(exe_sha256=NATIVE_SHA,fields=references,scope='Static byte occurrence only;no native structure or runtime behavior inferred'),
  target_executions=0,model_executions=0,native_executions=0,old_acceptance_transferred=False,seconds=time.monotonic()-began,
  limitations=['114x88 ability semantic comparison resolves only four explicitly decoded pointer/length slices12/20/28/36;all other88B bytes compared literally','Class/race/zone comparisons cover listed fields only;full raw records are retained without claiming nested-pointer equality','Static declaration equality does not prove skill execution or complete139 behavior unchanged','New imported Date wrappers do not establish reachable gameplay purpose','Windows numeric occurrences are not semantic equivalence or Windows ABI restoration'])
 base.save(out/'delta.json',result);print(json.dumps(dict(directory=str(out),sha256=base.sha(out/'delta.json'),semantic_equal=result['semantic_equal'],semantic_total=result['semantic_total'],bridge_remaining_equal=bridge_equal,seconds=result['seconds'])),flush=True)
if __name__=='__main__':main()
