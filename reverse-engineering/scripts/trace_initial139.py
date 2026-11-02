#!/usr/bin/env python3
"""Fresh139 constructor declarations/layout; bounded static reads, no target.

Reads1600/cached6786/stat1542 and the actual139 data behind their literal
consumers. Does not infer newGame/profile sizes from an old wrapper. The
default input remains an explicitly selected empty376 profile plus a borrowed
flat query view; App/cache/world ownership and opening stay separate.
"""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,re,sqlite3,struct
from wasm139_profile import ROOT,SOURCE,SOURCE_SHA,binary_identity
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
DATA=ROOT/'evidence/engine139-data-delta-20261102T014028.095422Z/delta.json'
DATA_SHA='c2b0fee13ad520de0cb4feebc3a003ade8e9be339f6d9c0daf3e6db639f9c4be'
MAP=ROOT/'evidence/engine139-refined-static-20261102T013743.612949Z/mapping.json'
MAP_SHA='7b41961bce7f45e74a8d2a24305cf84d0d64f2f2d739c723b1e445af208c40f0'
FUNCTIONS=(1600,6786,1542,29912,23333,25911,10286,9431)
def sha(p):
 with p.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
 before=sha(Path(__file__));assert sha(SOURCE)==SOURCE_SHA and sha(DATA)==DATA_SHA and sha(MAP)==MAP_SHA
 raw=SOURCE.read_bytes();identity,ranges=binary_identity(raw);delta=json.loads(DATA.read_text());role_map=json.loads(MAP.read_text());assert delta['source_wasm_sha256']==SOURCE_SHA and role_map['bindings']['constructor']==1600
 decoded=delta['decoded']['139'];addresses=decoded['addresses'];memory=bytearray(max(s['address']+s['bytes']for s in identity['data_segments']if s['address']is not None))
 for s in identity['data_segments']:
  if s['address']is not None:memory[s['address']:s['address']+s['bytes']]=raw[s['file_offset']:s['file_offset']+s['bytes']]
 def read(p,n):assert 0<=p<=p+n<=len(memory);return bytes(memory[p:p+n])
 def u(p):return struct.unpack('<I',read(p,4))[0]
 def text(p,n):return read(p,n).decode('ascii')
 abilities={}
 for j in range(114):
  p=addresses['abilities']+j*88;name=text(u(p+12),u(p+16));row=next(a for a in decoded['abilities']if a['index']==j)
  assert row['pointer']==p and row['raw88_hex']==read(p,88).hex()and row['ability_id']==name;abilities[name]=p
 classes=[];races=[];zones=[]
 for cls in(1,2,3,4,5,7,8,9,11):
  p=addresses['class_default']if cls==1 else u(addresses['class_table']+4*(cls-2));name=text(u(p+40),u(p+44));source=next(c for c in decoded['classes']if c['class_byte']==cls)
  assert source['pointer']==p and source['raw88_hex']==read(p,88).hex()and source['starter_id']==name
  classes.append(dict(class_byte=cls,pointer=p,starter_id=name,definition_pointer=abilities[name],hp_bits=u(p+72),armor_bits=u(p+76),raw88_hex=read(p,88).hex(),definition88_hex=read(abilities[name],88).hex()))
 for race in range(1,9):
  p=addresses['race_default']if race==1 else u(addresses['race_table']+4*(race-2));name=text(u(p+24),u(p+28));source=next(c for c in decoded['races']if c['race_byte']==race);definition=abilities[name]
  assert source['pointer']==p and source['raw44_hex']==read(p,44).hex()and source['racial_id']==name
  races.append(dict(race_byte=race,pointer=p,racial_id=name,definition_pointer=definition,effect_tag=u(definition),execution_kind=read(definition+84,1)[0],raw44_hex=read(p,44).hex(),definition88_hex=read(definition,88).hex()))
 for j in range(12):
  p=addresses['zones']+j*152;source=decoded['zones'][j];name=text(u(p+8),u(p+12));assert source['pointer']==p and source['identifier']==name and source['raw152_hex']==read(p,152).hex()
  zones.append(dict(index=j,pointer=p,identifier=name,x_bits=u(p+104),y_bits=u(p+108),field116_bits=u(p+116),raw152_hex=read(p,152).hex()))
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('initial139-static-%Y%m%dT%H%M%S.%fZ');out.mkdir();functions={};texts={}
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as wat:
  db.row_factory=sqlite3.Row;db.execute('pragma query_only=ON')
  for index in FUNCTIONS:
   row=dict(db.execute('select *from functions where idx=?',(index,)).fetchone());assert(row['body_start'],row['body_end'])==ranges[index][:2]and row['wat_end']-row['wat_start']<=1048576
   wat.seek(row['wat_start']);value=wat.read(row['wat_end']-row['wat_start']);(out/f'{index}.wat').write_bytes(value);lines=[l.strip()for l in value.decode().splitlines()];texts[index]=lines
   functions[str(index)]=dict(**row,body_sha256=hashlib.sha256(raw[row['body_start']:row['body_end']]).hexdigest(),wat_sha256=hashlib.sha256(value).hexdigest(),signature=lines[0],function_lines=len(lines),direct_calls=[dict(line=j+1,callee=int(l.split()[1]))for j,l in enumerate(lines)if re.fullmatch(r'call \d+',l)])
 def window(index,a,b):return[dict(line=j,instruction=texts[index][j-1])for j in range(a,b+1)]
 def instances(index,pattern,context=5):
  lines=texts[index];return[dict(line=j+1,instructions=window(index,max(1,j+1-context),min(len(lines),j+1+context)))for j,l in enumerate(lines)if pattern(l)]
 assert texts[1600][677]=='memory.copy'and texts[1600][676]=='i32.const 376'and texts[1600][2707]=='memory.copy'and texts[1600][2706]=='i32.const 2592'
 assert texts[1600][2699]=='call 1542'and texts[6786][7402]=='call 1600'and texts[6786][7486]=='memory.copy'and texts[6786][7485]=='i32.const 2592'
 assert any('i32.load8_u offset=112'in l for l in texts[29912])and any('f32.load offset=108'in l for l in texts[29912])
 scalar_offsets=(488,736,740,1652,2416,2424,2428,2432,2436,2440,2444,2448,2452,2456,2460,2464,2468,2472,2516,416,440,448,456,464,1744,1764)
 patterns={o:instances(1600,lambda l,o=o:bool(re.fullmatch(r'(?:i32|i64|f32)\.store(?:8)? offset='+str(o+88)+r'(?: align=\d+)?',l)))for o in scalar_offsets}
 # Profile copies into scratch104, Game is copied from scratch88, hence+16
 # for input fields. These known tags do not imply known inactive payloads.
 proof=dict(version='0.139.0',actual_build='f79c5e2b4',original_wasm_sha256=SOURCE_SHA,script_sha256=before,role_mapping_sha256=MAP_SHA,data_delta_sha256=DATA_SHA,
  fresh=dict(version=139,addresses=addresses,classes=classes,races=races,zones=zones),functions=functions,
  physical_layout=dict(Game_bytes=2592,selected_profile_bytes=376,constructor_stack_bytes=2944,Game_copy_base_scratch=88,profile_copy_scratch=104,profile_to_Game_delta=16,owned_stride=80,definition_stride=88,definitions_count=114,borrowed_query_bytes=128,query_flat_flag120=1,query_height116='input bits',query_primary_tag56=-1,query_secondary_tag32=-1),
  windows=dict(profile_copy=window(1600,670,679),Game_copy=window(1600,2694,2709),cached_constructor_call=window(6786,7398,7405),cached_Game_copy=window(6786,7480,7490),
   query_height_call=window(1600,313,357),constructor_literal_consumers=[r for r in delta['constructor_literal_consumers']if r['version']==139],
   scalar_and_tag_store_sites=patterns,PCG_full=window(1600,372,528),
   initializer_store_sequence=window(1600,679,1180),
   exact_store_inventory=[dict(line=j+1,instruction=l)for j,l in enumerate(texts[1600])if '.store'in l],
   flat_query_early_return=instances(29912,lambda l:'i32.load8_u offset=112'in l or'f32.load offset=108'in l),
   cached_App_profile_world_access=instances(6786,lambda l:bool(re.search(r'offset=(3376|5116|5165)(?:\s|$)',l)))),
  output_production_data_module='reconstruction/core_spec/initial_state139_data.py',target_executions=0,model_executions=0,old_acceptance_transferred=False,
  limitations=['Static139 data/layout only; actual constructor behavior needs fresh139 calls.','Cached6786 profile/cache access is read for ABI/layout provenance; no cachedworld/App lifetime producer is reconstructed here.','Only selected scalar/tag store sites are recorded; actual allocator pointers and inactive/unwritten payload cells must stay unknown rather than filled from observed memory.','1542 class/race traits and numerical rules belong to the separately owned139 stats module and require its own source proof/validation.'])
 lines=['"""Literal constructor-referenced139 declarations; no runtime original IO."""',"SOURCE_WASM_SHA256="+repr(SOURCE_SHA),"DATA_DELTA_SHA256="+repr(DATA_SHA),
  'CLASS_STARTERS='+repr({c['class_byte']:(c['starter_id'],c['definition_pointer'],c['hp_bits'])for c in classes}),
  'RACIAL_ABILITIES='+repr({c['race_byte']:(c['racial_id'],c['definition_pointer'],c['execution_kind'],c['effect_tag'])for c in races}),
  'ZONE_ENTRIES='+repr(tuple((c['identifier'],c['x_bits'],c['y_bits'],c['field116_bits'])for c in zones))]
 module=ROOT/proof['output_production_data_module'];content='\n'.join(lines)+'\n'
 if module.exists():assert module.read_text()==content
 else:module.write_text(content)
 proof['production_data_sha256']=sha(module);save(out/'initial-data.json',proof);assert before==sha(Path(__file__))and sha(SOURCE)==SOURCE_SHA
 print(json.dumps(dict(directory=str(out),sha256=sha(out/'initial-data.json'),source_data_sha256=sha(module),constructor_body_sha256=functions['1600']['body_sha256'],fresh_rows=len(classes)+len(races)+len(zones),target_executions=0)),flush=True)
if __name__=='__main__':main()
