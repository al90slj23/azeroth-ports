#!/usr/bin/env python3
"""Independent read-only audit of empty history / scoped address entropy.

Does not import the production model or execute original code.  Reconstructs
the53845 byte writes directly from indexed WAT and rereads all frozen results.
Four-map state replay remains static typed-input evidence, never4253 runtime.
"""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os,re,sqlite3,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'evidence/app-history0135-oracle-20261101T114831.615348Z'
RECEIPT_SHA='254783e9554e47977d44f2f07f4ce2b433db14d21ef4ac443f4470c56ba9eb05'
MODEL_SHA='d8f423c6973be125115857672d506bfc0d7d53f77cc03e04b08837a97376b7d2'
SOURCE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
INDEX_SHA='b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
ROLE_BINDINGS=[('history135_empty',0,53845),('history135_drop',0,28797),('history135_seed',0,60416),('history135_entropy',0,81334),('history135_stack',3,0)]


def sha(path):
    with Path(path).open('rb')as h:return hashlib.file_digest(h,'sha256').hexdigest()


def uint(raw,pos):
    value=shift=0
    while True:
        b=raw[pos];pos+=1;value|=(b&127)<<shift
        if b<128:return value,pos
        shift+=7;assert shift<=35


def sint32(raw,pos):
    value=shift=0
    while True:
        b=raw[pos];pos+=1;value|=(b&127)<<shift;shift+=7
        if b<128:break
        assert shift<=35
    if b&64:value-=1<<shift
    return value&0xffffffff,pos


def sections(raw):
    assert raw[:8]==b'\0asm\1\0\0\0';at=8;result=[]
    while at<len(raw):
        kind=raw[at];size,start=uint(raw,at+1);end=start+size;assert end<=len(raw);result.append((kind,at,start,end));at=end
    return result


def exports(raw,section):
    n,at=uint(raw,section[2]);result=[]
    for _ in range(n):
        length,start=uint(raw,at);name=raw[start:start+length].decode();at=start+length;kind=raw[at];index,at=uint(raw,at+1);result.append((name,kind,index))
    assert at==section[3];return result


def static_data(raw,address,size):
    section=next(s for s in sections(raw)if s[0]==11);n,at=uint(raw,section[2]);data=bytearray(size);coverage=bytearray(size);pieces=[]
    for index in range(n):
        flag,at=uint(raw,at);assert flag in(0,1,2);memory=None;addr=None
        if flag!=1:
            memory=0
            if flag==2:memory,at=uint(raw,at)
            assert raw[at]==0x41;addr,at=sint32(raw,at+1);assert raw[at]==0x0b;at+=1
        length,start=uint(raw,at);at=start+length
        if memory!=0:continue
        lo=max(addr,address);hi=min(addr+length,address+size)
        if lo<hi:
            payload=raw[start+lo-addr:start+hi-addr];data[lo-address:hi-address]=payload;coverage[lo-address:hi-address]=bytes([1])*(hi-lo)
            pieces.append(dict(segment=index,source_file_offsets=[start+lo-addr,start+hi-addr],target_offsets=[lo-address,hi-address],bytes_hex=payload.hex()))
    assert at==section[3]
    return bytes(data),dict(address=address,bytes=size,pieces=pieces,initial_zero_gap_offsets=[i for i,v in enumerate(coverage)if not v])


def closure():
    pending=[ROOT/'scripts/check_app_history135.py',ROOT/'scripts/run_app_history135_oracle.mjs'];seen=set()
    while pending:
        path=pending.pop()
        if path in seen:continue
        seen.add(path)
        if path.suffix!='.py':continue
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom):
                if node.level:
                    assert node.level==1
                    for name in([node.module]if node.module else[a.name for a in node.names]):pending.append(path.parent/(name.replace('.','/')+'.py'))
                elif node.module and node.module.startswith('core_spec'):
                    pending.append(ROOT/'reconstruction/core_spec/__init__.py')
                    if node.module=='core_spec':pending.extend(ROOT/'reconstruction/core_spec'/(a.name+'.py')for a in node.names if(ROOT/'reconstruction/core_spec'/(a.name+'.py')).exists())
                    else:pending.append(ROOT/'reconstruction'/(node.module.replace('.','/')+'.py'))
                elif node.module and(ROOT/'scripts'/(node.module+'.py')).is_file():pending.append(ROOT/'scripts'/(node.module+'.py'))
    return set(str(p.relative_to(ROOT))for p in seen)


def interpret53845(text):
    memory=bytearray(240);covered=bytearray(240);stack=[];stores=[]
    for line in text.decode().splitlines()[1:]:
        line=line.strip().rstrip(')')
        if not line:continue
        if line=='local.get 0':stack.append(0)
        elif line.startswith('i64.const '):stack.append(int(line.split()[1])&((1<<64)-1))
        elif line.startswith('i64.store'):
            m=re.search(r'offset=(\d+)',line);offset=int(m.group(1))if m else 0;value=stack.pop();base=stack.pop();at=base+offset
            assert 0<=at<=232 and not any(covered[at:at+8]);memory[at:at+8]=value.to_bytes(8,'little');covered[at:at+8]=bytes([1])*8;stores.append(dict(offset=offset,value=str(value)))
        else:raise AssertionError('Unexpected53845 instruction '+line)
    assert not stack and all(covered)and len(stores)==30
    assert all(struct.unpack_from('<3I',memory,i*12)==(0,1,0)for i in range(20))
    return bytes(memory),stores


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def main():
    receipt_path=DIRECTORY/'comparison.json';assert sha(receipt_path)==RECEIPT_SHA
    r=json.loads(receipt_path.read_text());assert(r['cases'],r['original_calls'],r['differences'],r['source_count'])==(24,96,0,10)
    assert r['status']=='passed'and r['process']['exit_code']==0 and r['process']['deadline_seconds']==60
    assert missing(r['process']['pid'])and missing(r['process']['pgid'],True)
    claimed=r['source_sha256_before'];assert set(claimed)==closure()and claimed==r['source_sha256_after']
    for name,h in claimed.items():assert sha(ROOT/name)==h==sha(DIRECTORY/'source-snapshot'/name)
    assert sha(ROOT/'reconstruction/core_spec/app_history135.py')==MODEL_SHA
    for name,h in{**r['frozen_artifacts'],**r['artifacts']}.items():assert sha(DIRECTORY/name)==h
    before={name:sha(ROOT/name)for name in claimed};before[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    module=(DIRECTORY/'app-history135.wasm').read_bytes();a,b=sections(raw),sections(module);assert[s[0]for s in a]==[s[0]for s in b]and all(s[0]!=8 for s in a)
    nonexport=[]
    for x,y in zip(a,b):
        if x[0]!=7:assert raw[x[1]:x[3]]==module[y[1]:y[3]];nonexport.append(dict(section=x[0],sha256=hashlib.sha256(raw[x[1]:x[3]]).hexdigest()))
    old=exports(raw,next(s for s in a if s[0]==7));new=exports(module,next(s for s in b if s[0]==7));assert new==old+ROLE_BINDINGS
    glob=next(s for s in a if s[0]==6);assert raw[glob[2]:glob[3]].hex()=='017f01418080c0000b'
    assert sha(PROFILE/'index.sqlite')==INDEX_SHA
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('app-history0135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    con=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row;functions=[];texts={}
    manifest=json.loads((DIRECTORY/'manifest.json').read_text());mf={x['idx']:x for x in manifest['functions']}
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        for idx in(53845,28797,60416,81334,4253):
            row=dict(con.execute('SELECT * FROM functions WHERE idx=?',(idx,)).fetchone());stream.seek(row['wat_start']);text=stream.read(row['wat_end']-row['wat_start']);texts[idx]=text
            wh=hashlib.sha256(text).hexdigest();bh=hashlib.sha256(raw[row['body_start']:row['body_end']]).hexdigest()
            assert wh==mf[idx]['wat_sha256']==sha(DIRECTORY/f'{idx}.wat')and bh==mf[idx]['body_sha256']
            if idx==4253:
                lines=text.splitlines(keepends=True)
                for name,lo,hi in(('typed-map-seeds',8488,8597),('history-and-map-writes',8757,8846)):
                    fragment=b''.join(lines[lo-1:hi]);(out/f'4253-{lo}-{hi}-{name}.wat').write_bytes(fragment)
            else:(out/f'{idx}.wat').write_bytes(text)
            functions.append(dict(**row,wat_sha256=wh,body_sha256=bh))
    con.close();history,stores=interpret53845(texts[53845]);assert b'call 71889'in texts[28797]and texts[28797].count(b'call 71889')==20
    for token in(b'global.get 0',b'i32.const 16',b'i32.sub',b'i32.const 15',b'call 106891',b'call 71889',b'i64.extend_i32_u'):assert token in texts[81334]
    for token in(b'call 81334',b'i32.const 14523256',b'i32.const 1',b'i32.store8',b'i32.const 14523248',b'i32.const 14523240'):assert token in texts[60416]
    inputs=json.loads((DIRECTORY/'inputs.json').read_text());expected=json.loads((DIRECTORY/'expected.json').read_text());results=[json.loads(line)for line in(DIRECTORY/'results.jsonl').read_text().splitlines()]
    assert len(inputs)==len(expected)==len(results)==24
    entropy_observations=[]
    for i,(c,e,result)in enumerate(zip(inputs,expected,results)):
        assert c['id']==e['id']==result['id']==i and set(c)=={'id','input'}and set(c['input'])=={'offset','poison','warm_bytes'}
        s=c['input'];assert s==dict(offset=i%8,poison=(0,0xa5,0xff)[i//8],warm_bytes=(0,1,4096,65536)[i%4])
        buffer=bytearray([s['poison']]*512);start=64+s['offset'];buffer[start:start+240]=history
        assert e['initialized']==e['dropped']==result['initialized']==result['dropped']==buffer.hex()
        seed=bytes.fromhex(result['seeded']);entropy=bytes.fromhex(result['entropy']);assert len(seed)==17 and len(entropy)==16
        seed0,seed1=struct.unpack_from('<2Q',seed);entropy0,entropy1=struct.unpack('<2Q',entropy)
        assert seed0==1048576-16-1==e['seed_first']and entropy0==1048576-1==e['entropy_first']and seed[16]==e['seed_flag']==1
        assert e['seed_second']is None and e['entropy_second']is None
        assert 0<seed1<result['memory_bytes'] and 0<entropy1<result['memory_bytes'] and result['host_calls']==0 and result['stack']==e['stack']==1048576
        entropy_observations.append(dict(id=i,seed0_known=seed0,seed1_opaque=str(seed1),entropy0_known=entropy0,entropy1_opaque=str(entropy1),seed_flag=seed[16]))
    header,headerproof=static_data(raw,5222424,16);assert struct.unpack('<4I',header)==(5222416,0,0,0)
    typed=json.loads((DIRECTORY/'typed-inline-state-replay.json').read_text());assert len(typed)==3;mask=(1<<64)-1
    for entry in typed:
        first,second=map(int,entry['input']);wanted=b''.join(header+struct.pack('<2Q',(first+j)&mask,second)for j in range(4))
        assert entry['bytes128']==wanted.hex()and entry['next_state']==[str((first+4)&mask),str(second)]
    old_dir=ROOT/'evidence/app-history0135-oracle-20261101T113852.683205Z';correction=DIRECTORY/'source-closure-correction.json'
    assert sha(correction)=='89f2d7601bc4ee5f1f3f1174bcb757e8864a4ccff4f5a41e02bea5db3340b8fd';cor=json.loads(correction.read_text())
    for name,h in cor['identical_inputs_expected_module_manifest_typed_replay_results'].items():assert sha(old_dir/name)==sha(DIRECTORY/name)==h
    runtime=r['runtime'];assert runtime['cases']==24 and runtime['original_calls']==96 and runtime['host_calls']==0 and runtime['denied_imports']==878 and runtime['peak_memory_bytes']<=33554432
    assert runtime['global_or_once_injected']is False and runtime['address_dependent_seed_second_word_predicted']is False
    runner=(ROOT/'scripts/run_app_history135_oracle.mjs').read_text();assert 'expected.json'not in runner and '.history135_stack.value='not in runner
    after={name:sha(ROOT/name)for name in before};assert before==after
    for name,h in before.items():dst=out/'source-snapshot'/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((ROOT/name).read_bytes());assert sha(dst)==h
    result=dict(status='passed_scoped_read_only_review',version='0.135.1',build='0898d5e3',receipt=str(receipt_path.relative_to(ROOT)),receipt_sha256=RECEIPT_SHA,
        source_count=10,source_closure_independently_collected=True,source_sha256_before=before,source_sha256_after=after,
        original_sha256=SOURCE_SHA,functions=functions,only_export_section_changed=True,added_exports=ROLE_BINDINGS,original_mutable_stack_global_unchanged=True,
        cases=24,original_author_calls=96,new_original_calls=0,reviewer_imported_production=False,
        complete53845_bytes=5760,full512B_poison_and_drop_observation_bytes=24*512*2,decoded53845_i64_stores=stores,
        drop_scope='Empty20vectors only; original20conditionalfreebranches are skipped byrealcap0, not patched.',
        entropy_known_stack_flag_bytes=408,entropy_opaque_address_bytes=384,entropy_observations=entropy_observations,stack_before_after=1048576,
        typed_map_static_header=dict(raw_hex=header.hex(),**headerproof),typed_map_replays=3,new_original4253_calls=0,
        source_closure_correction=dict(old_sources=7,new_sources=10,path=str(correction.relative_to(ROOT)),sha256=sha(correction),six_artifacts_byte_identical=True,cases_not_added=True),
        process_terminal_pid_and_pgid_verified_missing=True,original_runtime=runtime,
        limitations=['Knownentropyprojectionatgenuine1MiBstackonly; both8Ballocatoraddresswordsremainopaque, no independentallocation/seedprediction.',
            'Fourmap128B onlyexplicitinitializedRandomState replay and4253staticwindows;notfull4253acceptance.',
            'Nonemptyhistorydestruction, actualhistoryusage, Appownership,880,UI/network andcompletegame remain separate.'],
        artifacts={p.name:sha(p)for p in out.iterdir()if p.is_file()})
    target=out/'review.json';target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(target),cases=24,author_original_calls=96,new_original_calls=0)))


if __name__=='__main__':main()
