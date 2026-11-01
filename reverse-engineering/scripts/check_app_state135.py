#!/usr/bin/env python3
"""Static original-window interpretation vs pure typed App projection.

No originalWASM function/module executes; no snapshot/browser/network/storage.
This is 32 local static recompositions, not32 original differential cases.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,random,re,struct,sys
sys.dont_write_bytecode=True
from trace_app_state135 import ROOT,SOURCE,SOURCE_SHA,extract_static
from build_full135_oracle import parse_source
from build_upgrade134_oracle import sha
from source_closure135 import core_sources

FILES=tuple(sorted(set(('scripts/check_app_state135.py','scripts/trace_app_state135.py',
 'scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py',
 'scripts/source_closure135.py',*core_sources(ROOT,'app_state135.py','app_history135.py')))))
M32=(1<<32)-1;M64=(1<<64)-1


class WindowMemory:
    def __init__(self,source,segments):self.source=source;self.segments=segments;self.values={}

    def byte(self,address):
        if address in self.values:return self.values[address]
        if address>=1048576:
            for seg in self.segments:
                if seg['address']<=address<seg['address']+seg['length']:
                    return self.source[seg['file_offset']+address-seg['address']]
            return 0 # Original static-data BSS, only immutable header reads.
        return None

    def read(self,address,size):return [self.byte(address+j)for j in range(size)]
    def write(self,address,data):
        for j,value in enumerate(data):self.values[address+j]=value
    def load(self,address,size):
        raw=self.read(address,size)
        return None if any(x is None for x in raw)else int.from_bytes(bytes(raw),'little')
    def store(self,address,size,value):self.write(address,[None]*size if value is None else(value&((1<<(size*8))-1)).to_bytes(size,'little'))


def interpret_constructor(text,source,segments,value):
    from core_spec.app_state135 import SIZE
    app,scratch=0x1000,0x5000;memory=WindowMemory(source,segments);locals_=[0]*80
    blocks={b.offset:b.data for b in value.live_blocks}
    for offset,length,temporary in((4160,368,408),(4980,36,1020)):
        memory.write(scratch+temporary,blocks.get(offset,[None]*length))
    loaded=blocks.get(4528,[None]*48);memory.write(scratch+368,loaded[12:48]);memory.write(scratch+780,value.history240)
    s0,s1=struct.unpack_from('<2Q',value.hash_maps128,16)
    locals_[0]=value.server_string_pointer;locals_[1]=app;locals_[2]=None if any(x is None for x in loaded[8:12])else int.from_bytes(loaded[8:12],'little')
    locals_[3]=scratch;locals_[4]=value.startup_flag5161;locals_[9]=value.transport_pointer
    locals_[52]=value.lcg_seed_u64;locals_[58]=None if any(x is None for x in loaded[:8])else int.from_bytes(loaded[:8],'little')
    for i,(first,second)in enumerate(((57,53),(54,51),(55,50),(56,59))):locals_[first]=(s0+i)&M64;locals_[second]=s1
    stack=[];instructions=Counter()
    for line in text.splitlines():
        line=re.sub(r'\(;.*?;\)','',line).strip()
        if not line:continue
        parts=line.split();op=parts[0];arg=parts[1]if len(parts)>1 else None;instructions[op]+=1
        offset=next((int(x.split('=')[1])for x in parts[1:]if x.startswith('offset=')),0)
        if op=='local.get':stack.append(locals_[int(arg)])
        elif op=='local.set':locals_[int(arg)]=stack.pop()
        elif op=='local.tee':locals_[int(arg)]=stack[-1]
        elif op in('i32.const','i64.const'):stack.append(int(arg)&(M32 if op=='i32.const'else M64))
        elif op in('i32.load','i64.load'):
            address=stack.pop()+offset;stack.append(memory.load(address,4 if op=='i32.load'else 8))
        elif op.startswith(('i32.store','i64.store')):
            value_word,address=stack.pop(),stack.pop()+offset
            size=1 if op.endswith('8')else 2 if op.endswith('16')else 4 if op.startswith('i32')else 8
            memory.store(address,size,value_word)
        elif op=='i32.add':b,a=stack.pop(),stack.pop();stack.append((a+b)&M32)
        elif op.startswith('i64.'):
            b,a=stack.pop(),stack.pop()
            assert a is not None and b is not None
            if op=='i64.add':value_word=a+b
            elif op=='i64.mul':value_word=a*b
            elif op=='i64.shr_u':value_word=a>>(b&63)
            elif op=='i64.xor':value_word=a^b
            elif op=='i64.and':value_word=a&b
            elif op=='i64.or':value_word=a|b
            elif op=='i64.gt_u':value_word=int(a>b)
            else:raise AssertionError(('Unexpected i64 opcode',op))
            stack.append(value_word&M64)
        elif op=='select':condition,b,a=stack.pop(),stack.pop(),stack.pop();stack.append(a if condition else b)
        elif op=='memory.copy':size,src,dst=stack.pop(),stack.pop(),stack.pop();memory.write(dst,memory.read(src,size))
        elif op=='memory.fill':size,value_word,dst=stack.pop(),stack.pop(),stack.pop();memory.write(dst,bytes([value_word&255])*size)
        else:raise AssertionError(('No calls/branches admitted in constructor window',line))
    assert not stack
    return tuple(memory.values.get(app+i)for i in range(SIZE)),instructions


def main():
    before={p:sha(ROOT/p)for p in FILES}
    sys.path.insert(0,str(ROOT/'reconstruction'))
    from core_spec.app_state135 import(AppConstructorInputs135,AppLiveBlock135,project_app_constructor135,
        app_pointer_from_tick_closure135,game_install_contract135,app_owner_layout135,UnknownAppState135)
    from core_spec.app_history135 import empty_history135,RandomState135,app_hash_maps135
    original,functions,bindings=extract_static();segments=parse_source(original)[4]
    text='\n'.join(functions[4253]['text'].splitlines()[8601:8894])+'\n'
    rng=random.Random(0x42535168);seeds=[0,1,M64,1<<63,0x123456789abcdef]+[rng.getrandbits(64)for _ in range(27)]
    wants=[];cases=[]
    for i,seed in enumerate(seeds):
        blocks=tuple(AppLiveBlock135(o,bytes((j*37+i)&255 for j in range(n)),'explicit controlled upstream-copy input;not restoredproducer')for o,n in((4160,368),(4528,48),(4980,36)))if i%2 else()
        value=AppConstructorInputs135(seed,0x11000+i*128,empty_history135(),app_hash_maps135(RandomState135(rng.getrandbits(64),rng.getrandbits(64))).bytes128,0x9000+i*16,i%2,blocks)
        want=project_app_constructor135(value);wants.append(want)
        cases.append(dict(id=i,seed_u64=str(seed),lcg_input=value.lcg_seed_u64,transport_pointer=value.transport_pointer,server_pointer=value.server_string_pointer,
            history240_hex=value.history240.hex(),hash_maps128_hex=value.hash_maps128.hex(),startup_flag5161=value.startup_flag5161,
            live_blocks=[dict(offset=b.offset,data_hex=b.data.hex(),producer=b.producer)for b in blocks]))
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('app-state0135-static-check-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    inp=out/'inputs.json';inp.write_text(json.dumps(cases,indent=2)+'\n')
    expected=out/'independent-expected.json';expected.write_text(json.dumps([list(x.storage)for x in wants],separators=(',',':'))+'\n')
    records=[];known=unknown=0
    for case,want in zip(cases,wants):
        blocks=tuple(AppLiveBlock135(b['offset'],bytes.fromhex(b['data_hex']),b['producer'])for b in case['live_blocks'])
        value=AppConstructorInputs135(case['lcg_input'],case['transport_pointer'],bytes.fromhex(case['history240_hex']),bytes.fromhex(case['hash_maps128_hex']),case['server_pointer'],case['startup_flag5161'],blocks)
        interpreted,instructions=interpret_constructor(text,original,segments,value)
        assert interpreted==want.storage and not want.legal_full_app
        known+=want.known_byte_count;unknown+=len(want.storage)-want.known_byte_count
        records.append(dict(id=case['id'],known_bytes=want.known_byte_count,unknown_bytes=5168-want.known_byte_count,unknown_ranges=want.unknown_ranges,
            instructions=dict(instructions),literal_wat_interpretation_equals_independent_model=True))
    assert app_pointer_from_tick_closure135(0x1000,5305816,lambda p:0x2000 if p==0x1008 else 0)==0x2010
    try:app_pointer_from_tick_closure135(0x1000,0,lambda p:0)
    except UnknownAppState135:pass
    else:raise AssertionError('Unrelated closure must reject')
    assert app_owner_layout135()['app_offset']==16 and game_install_contract135()['move_not_clone']
    assert before=={p:sha(ROOT/p)for p in FILES}
    for p,h in before.items():dst=out/'source-snapshot'/p;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((ROOT/p).read_bytes());assert sha(dst)==h
    (out/'constructor-window.wat.txt').write_text(text)
    result=dict(version='0.135.1',build='0898d5e3',status='passed_static_window_recomposition_not_original_differential',
        controlled_static_cases=len(cases),known_bytes_checked=known,unrestored_or_inactive_None_bytes_checked=unknown,
        source_sha256_before=before,source_sha256_after=before,source_count=len(before),original_sha256=SOURCE_SHA,
        input_sha256=sha(inp),independent_expected_sha256=sha(expected),window_sha256=sha(out/'constructor-window.wat.txt'),
        cases=records,bindings=bindings,original_function_executed=False,original_module_instantiated=False,new_original_calls=0,new_original_cases=0,
        app_complete_or_legal=False,snapshot_read=False,appstart_called=False,network_used=False,user_saves_accessed=False,
        limitation='Straightline originalWAT window interpretedlocally,not full4253 or a fresh original execution;livecopies/pointers/entropy are explicitinputs,not restoredproducers.')
    target=out/'comparison.json';target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),sha256=sha(target),controlled_static_cases=len(cases),new_original_calls=0)))


if __name__=='__main__':main()
