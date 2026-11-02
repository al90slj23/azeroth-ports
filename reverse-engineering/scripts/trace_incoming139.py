#!/usr/bin/env python3
"""Current1391076/source432/history48/real locale static declarations."""
from datetime import datetime,timezone
import hashlib,json,re,struct
from incoming139_tools import ROOT,SOURCE_SHA,original,static_reader,function_proof,save,sha,PROFILE
import sqlite3
def trace(out):
    raw,identity,ranges=original();read=static_reader(raw,identity)
    indices={1076,83304,20060,59230,56864,994,1173,28155,1466,38882,5719,93344}
    proof,texts=function_proof(raw,identity,ranges,indices,out)
    assert proof[1076]['signature']==('7f7d7e7f7f7f','')and proof[1076]['body_bytes']==12535
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:
        callees=[dict(callee=i,sites=n)for i,n in db.execute('select callee,count(*)from calls where caller=1076 group by callee order by callee')]
    text=texts[1076];lines=[x.strip()for x in text.splitlines()];windows={}
    for name,a,b,terms in(
        ('entry_phase_protection',8,23,('i32.load8_u offset=2587','i32.load8_u offset=2576')),
        ('mode1_wave2540',24,52,('call 38882','i32.load offset=2540')),
        ('armor54_lightning_rank3pct',112,266,('i32.const 54','i32.const 16','i32.const 5892788','f32.const 0x1.8p+1','f32.const 0x1.9p+6')),
        ('shield139_offsets',807,1019,('f32.load offset=1444','f32.store offset=1448','f32.store offset=1348','f32.load offset=764','call 28155','call 1466')),
        ('shield736_740',1435,1503,('f32.load offset=736','f32.store offset=736','f32.store offset=740','i64.store offset=736')),
        ('HP_taken_before_category',1797,1813,('f32.store offset=1652','f32.store offset=1440','f64.store offset=992')),
        ('source432_category424',1814,1881,('i32.const 432','i32.const 188','i32.const 180','i32.load8_u')),
        ('source432_history_name424',3192,3383,('i32.const 432','i32.const 392','i32.const 244','call 59230','i32.const 384','i32.load8_u')),
        ('spellResolver_is_conditional',3393,3405,('local.get 4','local.get 5','call 4562')),
        ('history48_prune_write',3548,3714,('f32.const -0x1.4p+3','i32.const 399','i32.const 48','i32.store8 offset=44','f32.store offset=36','f32.store offset=24'))):
        chunk='\n'.join(lines[a-1:b]);assert all(t in chunk for t in terms),name;windows[name]=dict(first_line=a,last_line=b,text=chunk,sha256=hashlib.sha256(chunk.encode()).hexdigest())
    p,n=struct.unpack('<2I',read(5401532,8));english_raw=read(p,n);english=json.loads(english_raw);assert english['game.title']=='Azeroth Survivors'and english['Melee']=='Melee'
    selected={k:english[k]for k in('Melee','Spell','Boss mechanic','enemy.600')}
    names={};npc=[]
    for pointer in(5830904,):
        nameptr,namecount,identifier=struct.unpack('<3I',read(pointer+16,12));fallback=read(nameptr,namecount).decode('utf8');key='enemy.'+str(identifier);value=english.get(key,fallback);names[str(pointer)]=value;npc.append(dict(pointer=pointer,raw72_hex=read(pointer,72).hex(),fallback=fallback,key=key,english=value))
    lightning=[]
    for i in range(114):
        row=5882752+i*88;ptr,n=struct.unpack('<2I',read(row,8))
        if n==16 and read(ptr,n)==b'lightning_shield':lightning.append(dict(index=i,definition_pointer=row-12,spell_id=struct.unpack('<I',read(row+32,4))[0],raw88_hex=read(row-12,88).hex()))
    assert len(lightning)==1 and lightning[0]['spell_id']==324
    fallback={}
    for category,p,n,icon,icon_n in((0,5909746,5,5912206,12),(1,5912218,5,5881728,23),(2,5912223,13,5880090,23)):
        text=read(p,n).decode('utf8');fallback[str(category)]=[english.get(text,text),read(icon,icon_n).decode('utf8')]
    result=dict(version='0.139.0',actual_build='f79c5e2b4',source_sha256=SOURCE_SHA,trace_source_sha256=sha(__file__),functions=proof,direct_callees=callees,windows=windows,English=dict(table_address=5401532,embedded_pointer=struct.unpack('<I',read(5401532,4))[0],bytes=len(english_raw),sha256=hashlib.sha256(english_raw).hexdigest(),entries=len(english),selected=selected),fallback=fallback,ordinary_english_names=names,NPC_declarations=npc,lightning_shield=lightning[0],source_headers=dict(live32=[1704,1708,1712,32],items8=[2024,2028,2032,8],modifiers36=[2048,2052,2056,36],NPC432=[1784,1788,1792,432],history48=[968,972,976,980]),read_proofs=read.proof,original_calls=0,limits=['Static recovery is not runtime acceptance.','No old snapshot/actual or natural NPC/owner producer is consumed.'])
    save(out/'trace.json',result);return result
def main():
    out=ROOT/'evidence'/('incoming139-static-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'));out.mkdir();trace(out);print(json.dumps(dict(directory=str(out),sha256=sha(out/'trace.json'))))
if __name__=='__main__':main()
