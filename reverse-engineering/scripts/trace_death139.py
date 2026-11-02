#!/usr/bin/env python3
"""Current139 ordinary death full913 source/callee binding; no execution."""
from datetime import datetime,timezone
import re,struct,sqlite3,ast
from incoming139_tools import ROOT,PROFILE,SOURCE_SHA,original,function_proof,static_reader,save,sha

def main():
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('death139-static-%Y%m%dT%H%M%S.%fZ');out.mkdir();raw,identity,ranges=original()
 ids={913,1446,36367,58587,46692,18421,1466,994,20752,1886,10804,24602,52397,51773,6619,15962,66558,29912,23333,11425,11499,50441,1600,46462}
 proof,texts=function_proof(raw,identity,ranges,ids,out);read=static_reader(raw,identity);npc=read(5830904,72);speeds=struct.unpack('<6I',read(1593032,24))
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:calls={str(i):list(db.execute('select callee,wat_line from calls where caller=?',(i,)))for i in ids}
 model=ROOT/'reconstruction/core_spec/death139.py';tree=ast.parse(model.read_text());decl=next(x for x in tree.body if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='DEFAULT72_139'for t in x.targets));assert bytes.fromhex(decl.value.args[0].value)==npc
 assert all(token in texts[913]for token in('f32.const 0x1.a66666p+0','f32.const 0x1.51eb86p-3','i32.const -1073741825','i32.store offset=1084','f32.store offset=2420'))
 result=dict(model_sha256=sha(model),static_model72_matches_actual139=True,reward_rule_literals_bound=True,version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,script_sha256=sha(__file__),functions=proof,direct_calls=calls,default_ordinary_definition=dict(pointer=5830904,raw72_hex=npc.hex(),xp56=struct.unpack_from('<I',npc,56)[0],cost60_bits=struct.unpack_from('<I',npc,60)[0],flag68=npc[68]),XP_unit_speeds=list(speeds),static_reads=read.proof,original_executions=0,unknowns=['positivehealing1466','full592andHP169packetstream','physicalBTreeandheapowner','nonemptyregistriesandprocs','bossandspecialdeath','movingdeath_dynamicvalidation','XPcollectionandscheduler','naturalApp/full1108/game'])
 save(out/'trace.json',result);print(str(out));print(sha(out/'trace.json'))
if __name__=='__main__':main()
