#!/usr/bin/env python3
"""Bind fresh139 PE instruction boundaries and partial25511 correspondence.

Static evidence only: neither Windows code nor WASM is executed here.
"""
from pathlib import Path
import hashlib,json,re,struct
from decompile_latest_native_focus import PE
from incoming139_tools import ROOT,original,function_proof,sha,save

RUN=ROOT/'evidence/native139-upgrade-focus-20261102T115527.969158Z'
NATIVE=ROOT/'originals/official-release-20261102T011227.335145Z/windows-0.139.0/AzerothSurvivors.exe'


def trace():
    out=RUN/'static-correspondence';out.mkdir(exist_ok=False)
    p=json.loads((RUN/'prepared.json').read_text());s=json.loads((RUN/'run-summary.json').read_text())
    assert sha(RUN/'prepared.json')=='8f35e936f291dcc6e39cccaf353d145f7beab655c63eb77037d9e943242e0d2f'
    assert sha(RUN/'run-summary.json')=='986479747f915a1e9752005373bade2f50ab2d85ffaeed56294b8e76f03ddb20'
    assert s['terminal']['exit_code']==0 and not s['terminal']['timed_out'] and s['terminal']['pid_missing'] and s['terminal']['pgid_missing']
    assert sha(NATIVE)==p['native_sha256']==s['native_sha256']
    f=json.loads((RUN/'functions.json').read_text());assert sha(RUN/'functions.json')==s['functions_sha256']
    pe=PE(NATIVE.read_bytes());decoded=[]
    for i,fn in enumerate(f['functions']):
        assert fn['accepted_for_bounded_semantic_inspection'] and fn['undecoded_bytes']==0
        selection=fn['selection'];a=int(selection['start'],16);z=int(selection['end_exclusive'],16)
        assert pe.containing(a)[:2]==(a,z)
        code=pe.data[selection['file_offset']:selection['file_offset']+z-a]
        assert hashlib.sha256(code).hexdigest()==selection['sha256']
        llvm={}
        for line in(RUN/('llvm-'+str(i)+'.stdout')).read_text().splitlines():
            m=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\t',line)
            if m:llvm[int(m[1],16)]=bytes.fromhex(m[2]).hex()
        ghidra={int(x['address'],16):x['bytes']for x in fn['instructions']}
        assert llvm==ghidra
        cursor=a
        for at,h in sorted(llvm.items()):
            assert at==cursor and bytes.fromhex(h)==pe.data[pe.offset(at,len(h)//2):pe.offset(at,len(h)//2)+len(h)//2]
            cursor+=len(h)//2
        assert cursor==z
        decoded.append(dict(start=hex(a),end_exclusive=hex(z),bytes=z-a,sha256=selection['sha256'],LLVM_Ghidra_instruction_boundary_count=len(llvm),all_original_bytes_decoded_agree=True,computed_jumps=selection['verified_switches'],semantic_status='firstfunctionstatic25511correspondence'if i==0 else'candidateinspectiononly'))
    raw,identity,ranges=original();proof,texts=function_proof(raw,identity,ranges,{25511},out)
    assert proof[25511]['signature']==('7f7f7f','7d')
    assert all('offset='+str(x)in texts[25511]for x in[5405004,5405040,5405076,5405112,5405148])
    scalar={}
    for address,want in [(0x1464d5d10,0x3f000000),(0x1464d5b60,0x3f800000),(0x147a1f88c,0xbe4ccccd),(0x14653d154,0x3f4ccccd),(0x1464d5e04,0x40a00000),(0x1464e2df8,0x3e800000),(0x1464d5ea0,0x40c00000)]:
        value=struct.unpack_from('<I',pe.data,pe.offset(address,4))[0];assert value==want
        scalar[hex(address)]=dict(bits=value,float=struct.unpack('<f',struct.pack('<I',value))[0])
    partial=[dict(field='definitionpointer',native=0,wasm=0,native_width=8,wasm_width=4),dict(field='kind0upgradecounter',native=36,wasm=32,width=4),dict(field='cooldownmultiplier',native=20,wasm=16,width=4),dict(field='additionalcount',native=24,wasm=20,width=4),dict(field='radiusmultiplier',native=28,wasm=24,width=4),dict(field='durationmultiplier',native=32,wasm=28,width=4)]
    rules=[dict(kind=0,rule='table0[tier] / (f32(u32(counter)*0.5)+1)',native_table='0x147a1fc5c',wasm_table=5405004),dict(kind=1,rule='table1[tier]*nonnegative((cooldown-0.2)/0.8)',native_table='0x147a1fc88',wasm_table=5405040),dict(kind=2,rule='f32(min(saturating_u32(cap-count),table2[tier]));cap12unlessdefinitionexec11;exec11namedseal_fate/soul_fire/lightwell/faerie_firecap2else0',native_table='0x147a1fcb8',wasm_table=5405076),dict(kind=3,rule='table3[tier]*nonnegative((5-radius)*0.25)',native_table='0x147a1fce8',wasm_table=5405112),dict(kind=4,rule='table4[tier]*nonnegative((6-duration)/5)',native_table='0x147a1fd18',wasm_table=5405148)]
    result=dict(kind='static_current139_native_upgrade_value_correspondence_only',version='0.139.0',build='f79c5e2b4',native_sha256=s['native_sha256'],wasm_sha256=p['wasm_sha256'],trace_script_sha256=sha(__file__),native_functions=decoded,current_WASM25511=proof[25511],partial_owned_field_correspondence=partial,native_definition_execution_byte=117,wasm_definition_execution_byte=84,native_scalar_constants=scalar,static_rule_correspondence=rules,valid_domain='kind0..4 actualenum/tier0..4;rawinvalidenum andpanicboundsnotexecuted',evidence_layers=dict(static_PE_and_original_instructions=True,independent_LLVM_Ghidra_boundaries=True,static_WASM_correspondence=True,model_selfcheck=False,original_native_instruction_emulation=False,full_WASM_function_differential=False,Windows_application_execution=False),limits=['Staticruleassociationdoesnotprovebehavioralequivalence.','Ghidraprototypeisanalystannotation;nativeGame/Unit/entireownedlayoutandWindowscallingcontextremainunrestored.','FirstfunctionusesMAXSS;ordinaryCconditionalpseudocodeisnotproofforNaN/signedzero. Originalinstructionemulationisaseparatenextstage.','Second610Bfunctionisinspectiononly;itsfullmetadata/callersareunmapped.','CurrentWASMfirst-cleaveupgrade19fixtureacceptanceisaseparatedomain;allfivegenericnativebranchesarenotdynamicallyaccepted.','Noneofthegame/nativeexecutable/WASMwasexecutedbythistrace.'],new_runtime_cases=0,full_mainloop_frames=0,native_windows_execution=False,complete_games=0)
    save(out/'correspondence.json',result)
    print(json.dumps(dict(directory=str(out),correspondence_sha256=sha(out/'correspondence.json'),native_functions=2,decoded_bytes=1123,decoded_instructions=257,original_executions=0)))
    return result


if __name__=='__main__':trace()
