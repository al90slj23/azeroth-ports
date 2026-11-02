#!/usr/bin/env python3
"""Bound current139 perception/48x16 Aura spec;static reads only."""
from pathlib import Path
import argparse,ast,struct
from incoming139_tools import ROOT,SOURCE_SHA,original,function_proof,static_reader,sha,save


def main():
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);args=parser.parse_args();out=args.output.resolve();out.mkdir()
    raw,identity,ranges=original();ids={922,1173,10490,15962,27754,36518,20123,29910,1542,45181}
    functions,texts=function_proof(raw,identity,ranges,ids,out);read=static_reader(raw,identity)
    model=ROOT/'reconstruction/core_spec/player_effects139.py';tree=ast.parse(model.read_text());decl={}
    for node in tree.body:
        if isinstance(node,ast.Assign)and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try:decl[node.targets[0].id]=ast.literal_eval(node.value)
            except ValueError:pass
    # The explicit bytes.fromhex expression is checked as syntax,data and ID.
    source_node=next(n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(v,ast.Name)and v.id=='PERCEPTION_DEFINITION88_139'for v in n.targets))
    assert isinstance(source_node.value,ast.Call)and source_node.value.func.attr=='fromhex'
    definition=read(5891892,88);assert bytes.fromhex(ast.literal_eval(source_node.value.args[0]))==definition
    assert(struct.unpack_from('<I',definition)[0],struct.unpack_from('<I',definition,4)[0],struct.unpack_from('<I',definition,44)[0],definition[84])==(8,0x3e19999a,20600,9)
    def window(index,first,last):
        text='\n'.join(texts[index].splitlines()[first-1:last]);return dict(index=index,first_line_1based=first,last_line_1based=last,text=text)
    for word in('f32.const 0x1.ep+4 (;=30;)','call 27754','call 10490','call 1542','call 1173'):assert word in texts[922]
    assert 'f32.store offset=44'in texts[922]and'i32.store offset=16'in texts[922]
    assert 'i32.load offset=1792'in texts[27754]and'call 36518'in texts[27754]
    assert all(s in texts[20123]for s in('i32.load\n          br_if 0','f32.load offset=344','f32.load offset=332','f32.load offset=328','f32.mul','f32.add','f32.le'))
    assert all(s in texts[29910]for s in('i32.const 9','i32.const 8','i32.const 32','i32.lt_u','i32.or'))
    assert 'i32.const 48\n    i32.store offset=2008'in texts[1173]and'i32.const 1\n    i32.store8 offset=2569'in texts[1173]
    assert not any(s in texts[1173]for s in('i32.store offset=1888','call 1542'))
    spec=dict(version='0.139.0',build='f79c5e2b4',original_sha256=SOURCE_SHA,model_file=str(model.relative_to(ROOT)),model_sha256=sha(model),functions=functions,
        perception_definition88_hex=definition.hex(),static_reads=read.proof,
        layout=dict(live32=dict(source_guid64=0,kind8=8,value12='f32(owned76*definition4)',unknown_written_word16=True,spell20=20600,expiry24='now+max_nanaware(.1,f32(f32(f32(def68*1.4)*owned28)*owned68))',periodic28=0),Aura=dict(capacity=48,count=48,stride=16,active_fields=['tag0=1','spell4','expiry8','stack_count12'],inactive_fields=['tag0=0','bytes4..15None'],positive_slots='0..31',cooldown_slots='32..47',ready2569=1)),
        target_query='27754→36518→20123 actualalive NPC0==0, interpolated XY ifduration>0,ordered f32(dx²+dy²)<=30²;current exclusionvecptr8/count0;no RNG',
        self306='packed source twice,u32spell,u16flags256,u8count1,rawsourceGUID64,u8miss0,u16targetmask0;no packed explicit target',
        Aura_projection='Active live12/1020 and8/20600 only,kind12 numeric payload not consumed;same-spell strongest/first tie,spell grouping,48x16 newmask;keys47..94 spellIDs,95..100 eight nibbles(positive9/cooldown8),113..124 four stack-minus1 bytes',
        unknowns=['live12 payload12..19','live8 scratch copied+16','Inactive Aura payload4..15','Newphysical vector/BTree/allocator pointers','Otherlive/modifiers/owned-effect12cooldown Aura sources'],
        source_windows=[window(922,4845,4990),window(922,6140,6410),window(10490,280,443),window(1173,1,190),window(1173,1870,1950),window(1173,2980,3115)],
        original_executions=0,kind='static_binding_not_runtime_acceptance',scope='Defaultmode0Human sourceGUID0,warriorkit without effect12 owned sources,live12/1020 and8/20600;none is fabricated empty beyond explicit producer contracts')
    save(out/'trace.json',spec);print(str(out/'trace.json'),sha(out/'trace.json'))


if __name__=='__main__':main()
