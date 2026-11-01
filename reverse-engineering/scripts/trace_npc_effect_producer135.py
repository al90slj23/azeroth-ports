#!/usr/bin/env python3
"""Pinned data declarations,921→910 producer sites and880 stage gaps; no original execution."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import ast,hashlib,json,re,sqlite3,struct,sys
sys.dont_write_bytecode=True
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z';WAT_SHA='15bccec81235752573d903d098911612d8add22cc51956d03afb8fb17382a7f2'
FUNCTIONS=(880,921,910,63687,34693,5736,1525,2785,916,975,38007,2602,2573,49037,947,2376)
CHAIN=(2088,916,975,1754,3757,915,38007,2602,921,2862,2573,947,2376,49037)


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def clean(s):return re.sub(r'\(;.*?;\)','',s).strip()

def controls(lines):
 stack=[];nodes={};calls=[]
 for i,text in enumerate(lines):
  parts=clean(text).split();op=parts[0]if parts else''
  if op in('block','loop','if'):
   nodes[i]=dict(line=i,kind=op,parent=stack[-1]if stack else None,condition_window=[dict(line=j,text=lines[j].strip())for j in range(max(0,i-14),i)]);stack.append(i)
  elif op=='end':nodes[stack.pop()]['end_line']=i
  elif op=='call':calls.append(dict(line=i,index=int(parts[1]),contexts=list(stack)))
 assert not stack
 return nodes,calls


def main():
 original=SOURCE.read_bytes();assert hashlib.sha256(original).hexdigest()==SOURCE_SHA;types,imports,decl,bodies,segments=parse_source(original)
 memory=bytearray(max(s['address']+s['length']for s in segments if s['address']is not None))
 for s in segments:
  if s['address']is not None:memory[s['address']:s['address']+s['length']]=original[s['file_offset']:s['file_offset']+s['length']]
 u=lambda p:struct.unpack_from('<I',memory,p)[0]
 def text(p,n):
  assert n<1024 and 0<=p<=len(memory)-n;return bytes(memory[p:p+n]).decode('utf8')
 def descriptor(p):
  raw=bytes(memory[p:p+40]);assert len(raw)==40;tag=raw[37]
  return dict(pointer=p,raw40_hex=raw.hex(),raw_tag37=tag,normalized_tag=29 if tag<=2 else(tag-3)&255,words=list(struct.unpack('<10I',raw)),field38_u16=struct.unpack_from('<H',raw,38)[0])
 # Genuine zone table, normal72 andboss72 declarations, notoriginal runtime.
 normals=[];bosses=[];all_actions=[]
 for zone in range(12):
  z=5456016+zone*152;zone_id=text(u(z+8),u(z+12));np,nc=u(z+64),u(z+68);bp,bc=u(z+72),u(z+76);assert bc==5
  for j in range(nc):
   p=np+j*72;words=list(struct.unpack_from('<18I',memory,p));prefix=words[:4];row=dict(zone=zone,zone_id=zone_id,index=j,pointer=p,name=text(words[4],words[5]),entry=words[6],raw72_hex=bytes(memory[p:p+72]).hex(),prefix16_words=prefix)
   if prefix[0]==0:assert prefix==[0,0,0,0];row['route']='ordinary-direct-melee1073; no40B actiondeclaration inthis16Bprefix'
   elif prefix[0]==1:row.update(route='ordinary-cast16B-temporary queue; not921→910 action44 queue',spell_id=prefix[1],range_bits=prefix[2],cast_delay_bits=prefix[3])
   else:raise AssertionError('Unknown normal prefix')
   normals.append(row)
  for j in range(bc):
   p=bp+j*72;name=text(u(p),u(p+4));ap,an=u(p+8),u(p+12);hp,hn=u(p+24),u(p+28);row=dict(zone=zone,zone_id=zone_id,index=j,pointer=p,name=name,base_actions_pointer=ap,base_actions_count=an,hp_actions_pointer=hp,hp_actions_count=hn,raw72_hex=bytes(memory[p:p+72]).hex(),base_actions=[],hp_actions=[])
   for k in range(an):
    q=ap+k*44;d=descriptor(q);d.update(index=k,record44_hex=bytes(memory[q:q+44]).hex(),cooldown_bits=u(q+40));row['base_actions'].append(d);all_actions.append(dict(source='boss-base44',boss_pointer=p,zone=zone,boss_name=name,**d))
   for k in range(hn):
    q=hp+k*52;d=descriptor(q+12);d.update(index=k,record52_hex=bytes(memory[q:q+52]).hex(),name=text(u(q),u(q+4)),hp_fraction_bits=u(q+8));row['hp_actions'].append(d);all_actions.append(dict(source='boss-hp52',boss_pointer=p,zone=zone,boss_name=name,**d))
   bosses.append(row)
 assert len(normals)==148 and sum(r['prefix16_words'][0]==0 for r in normals)==124 and len(bosses)==60
 db=sqlite3.connect(f'file:{PROFILE/"index.sqlite"}?mode=ro',uri=True);out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('npc-effect-producer0135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir();texts={};identities=[]
 with(PROFILE/'official-0.135.1-full.wat').open('rb')as f:
  assert hashlib.file_digest(f,'sha256').hexdigest()==WAT_SHA
  for index in FUNCTIONS:
   a,b=db.execute('select wat_start,wat_end from functions where idx=?',(index,)).fetchone();f.seek(a);raw=f.read(b-a);(out/f'{index}.wat').write_bytes(raw);texts[index]=raw.decode().splitlines();x,y=bodies[index];ps,rs=types[decl[index-len(imports)]];identities.append(dict(index=index,wat_start=a,wat_end=b,wat_sha256=hashlib.sha256(raw).hexdigest(),body_start=x,body_end=y,body_sha256=hashlib.sha256(original[x:y]).hexdigest(),body_bytes=y-x,parameters_hex=ps.hex(),results_hex=rs.hex(),direct_callees=[v[0]for v in db.execute('select distinct callee from calls where caller=? order by callee',(index,))]))
 node921,calls921=controls(texts[921]);node880,calls880=controls(texts[880]);action_drain=next(c for c in calls921 if c['index']==910)
 pushes=[i for i,l in enumerate(texts[921])if clean(l)=='i32.store offset=156'];assert pushes==[60,4532,4955,5158,5583]
 sites=[]
 for line,kind,domain in((4532,'threshold52','U64!=MAX; U96definition+16ptr/+20len; U104one-shotbits'),(4955,'timer44','U64!=MAX; U68timerptr/U72len; U84actionptr/U88len; action+40cooldown'),(5158,'threshold52','U244!=MAX boss; U256definition+24ptr/+28len; U272one-shotbits'),(5583,'timer44','U244!=MAX boss; U248timerptr/U252len; U260actionptr/U264len; action+40cooldown')):
  sites.append(dict(line=line,family=kind,domain=domain,window=[dict(line=i,text=texts[921][i].strip())for i in range(line-48,line+3)]))
 scheduler=[]
 for call in calls880:
  if call['index']in CHAIN:
   scheduler.append(dict(index=call['index'],line=call['line'],if_contexts=[node880[n]for n in call['contexts']if node880[n]['kind']=='if'],window=[dict(line=i,text=texts[880][i].strip())for i in range(max(0,call['line']-8),call['line']+2)]))
 #Allcurrentlyretained NPCrawrecords areobservations of thosefields only.
 old=ROOT/'evidence/full0135-oracle-20261101T064308.759593Z/headless135-results.jsonl';observed=[];melee={r['pointer']for r in normals if r['prefix16_words'][0]==0}
 for case in map(json.loads,old.read_text().splitlines()):
  seen=set();counts=Counter();rows=0
  for stage in case['stages']:
   for h in stage['projection']['records']:
    b=bytes.fromhex(h);rows+=1;p=struct.unpack_from('<I',b,284)[0];seen.add(p)
    for offset in(40,64,72,80,88,96,104,232,240,244,252,264,272):
     value=struct.unpack_from('<I',b,offset)[0]
     if value!=(0xffffffff if offset in(40,64,244)else 0):counts[str(offset)]+=1
  assert set(seen)<=melee
  observed.append(dict(seed=case['id'],record_occurrences=rows,definition_pointers=sorted(seen),noncanonical_field_occurrences=dict(counts)))
 gaps=[]
 for index,scope in((916,'G648/G652 active84 and extra timers/procs; notmain1076'),(975,'owned80 definition.execution84==11 gate; otherglobals784..904 conditional behavior'),(38007,'G1836ptr/G1840len stride32 deadline+8 queue; notG1800area88'),(2602,'G1860ptr/G1864len stride112; distinctfrom1754 G1848/G1852'),(2573,'phase1 andG2116 claims88, XP/movement resources and4630'),(49037,'G400!=0 &&phase1 &&!(G2568&1) ->phase5 and17119/messages')):
  lines=texts[index];direct=sorted({lines[j+1].strip()for j,l in enumerate(lines[:-1])if l.strip()=='local.get 0'and('.load'in lines[j+1]or'.store'in lines[j+1])});gaps.append(dict(function=index,scope=scope,direct_G_memarg_candidates=direct,status='Notincluded incurrent sameG, requires originalstate readback andindependent guard/model; noemptyassumption'))
 report=dict(version='0.135.1',build='0898d5e3',original_sha256=SOURCE_SHA,wat_sha256=WAT_SHA,script_sha256=sha(Path(__file__)),functions=identities,normal_count=148,melee_prefix_zero_count=124,ranged_prefix_one_count=24,boss_count=60,declared_boss_action_records=len(all_actions),action_rawtag_counts=dict(Counter(r['raw_tag37']for r in all_actions)),normal_declarations='normal-declarations.json',boss_declarations='boss-declarations.json',action_declarations='action-declarations.json',queue921=dict(temporary_cap_ptr_len=[148,152,156],stride=44,layout={'0':'NPCindex','4..43':'complete40Bdescriptor','41':'rawtag37'},append_sites=sites,drain=action_drain,drain_window=[dict(line=i,text=texts[921][i].strip())for i in range(9191,9299)],guard='raw255 breaksentiretemporaryqueue; whenG387<=3 normalized9/raw12 andnormalized23/raw26 suppress910, otherpassedtags call910. Raw255hereisnot915 raw255!'),scheduler880=scheduler,single_state_tail_order=list(CHAIN),skipped_stages=gaps,retained_NPC_fields=dict(source=str(old.relative_to(ROOT)),sha256=sha(old),cases=observed,scope='OnlyactualNPC424fieldobservations; not915three-domainreadback andnotanoriginal915execution proof.'),known_limits=['NPCprefixzero ismelee declaration, not an actiontag andnotitself proof all915producersremaininactive.','U64family52/44 declarations andtheirconstructor notyetfullyrecovered; boss60declarationsarefullyretainedraw,butnotexecutedbythisstatictrace.','Direct callordering andifcontexts do notcomplete880host/transport/world-entry orchestration.','Prior915static semantic skip255summary was disproved bynewnonemptyprobe(popthenpanic80660/90675); do notinherit thatsummary.','Staticdata inventory doesnot countasbehavioraldifferentialvalidation; no original function executed.'],original_executed=False)
 for name,value in(('normal-declarations.json',normals),('boss-declarations.json',bosses),('action-declarations.json',all_actions),('npc-effect-producer135-static.json',report)):(out/name).write_text(json.dumps(value,indent=2)+'\n')
 print(json.dumps(dict(directory=str(out),normals=len(normals),melee=124,ranged=24,bosses=len(bosses),boss_action_records=len(all_actions),rawtag_counts=report['action_rawtag_counts'],report_sha256=sha(out/'npc-effect-producer135-static.json')),indent=2))

if __name__=='__main__':main()
