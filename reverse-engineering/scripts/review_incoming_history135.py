#!/usr/bin/env python3
"""Read-only incoming-history review; does not instantiate or execute WASM."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import argparse, ast, hashlib, importlib.util, json, math, os, struct, sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
ORIGINAL_SHA = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
DEFAULT = 'full0135-oracle-20261101T092259.307993Z'
INPUT_KEYS = {'id','group','input','capacity','head','count','storage','ops'}
POINTERS = {0:(5414827,5,5414832,12), 1:(5414844,5,5414849,23), 2:(5414872,13,5414885,23)}
NAMES = {0:('Melee','INV_Sword_04'),1:('Spell','Spell_Shadow_ShadowBolt'),2:('Boss mechanic','Spell_Fire_SelfDestruct')}
OFFSETS = {'armor_1392_bits':1568,'armor_cap_1572_bits':1572,'nearby_reduction_1444_bits':1624,
 'hp_1528_bits':1440,'shield_1532_bits':1444,'barrier_1536_bits':1448,'shield_source_1344':1344,
 'shield_source_remaining_1348_bits':1348,'reserve_768_bits':768,'absorbed_740_bits':740,
 'maximum_shield_744_bits':744,'last_hit_1648_bits':1652}


def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ff(word):return struct.unpack('<f',struct.pack('<I',word))[0]
def fb(value):return struct.unpack('<I',struct.pack('<f',value))[0]
def fadd(a,b):return fb(ff(a)+ff(b))
def fsub(a,b):return fb(ff(a)-ff(b))
def fmul(a,b):return fb(ff(a)*ff(b))
def u(raw,o):return struct.unpack_from('<I',raw,o)[0]
def put(raw,o,v):struct.pack_into('<I',raw,o,v)


def uint(raw,p):
    result=shift=0
    while True:
        x=raw[p];p+=1;result|=(x&127)<<shift
        if x<128:return result,p
        shift+=7;assert shift<64


def section_ranges(raw):
    assert raw[:8]==b'\0asm\1\0\0\0';p=8;rows=[]
    while p<len(raw):
        start=p;kind=raw[p];size,p=uint(raw,p+1);end=p+size
        assert end<=len(raw);rows.append((kind,start,p,end));p=end
    assert p==len(raw);return rows


def exports(raw,ranges):
    sec=next(x for x in ranges if x[0]==7);n,p=uint(raw,sec[2]);items=[]
    for _ in range(n):
        size,p=uint(raw,p);name=raw[p:p+size].decode();p+=size;kind=raw[p];p+=1;idx,p=uint(raw,p);items.append([name,kind,idx])
    assert p==sec[3];return items


def body(raw,ranges,index):
    sec=next(x for x in ranges if x[0]==10);n,p=uint(raw,sec[2]);found=None
    for i in range(n):
        size,p=uint(raw,p)
        if i+878==index:found=(p,p+size)
        p+=size
    assert p==sec[3] and found is not None;return found


def signature(raw,ranges,index):
    sec=next(x for x in ranges if x[0]==1);n,p=uint(raw,sec[2]);types=[]
    for _ in range(n):
        assert raw[p]==0x60;p+=1;count,p=uint(raw,p);params=raw[p:p+count];p+=count
        count,p=uint(raw,p);results=raw[p:p+count];p+=count;types.append((params.hex(),results.hex()))
    assert p==sec[3]
    sec=next(x for x in ranges if x[0]==3);n,p=uint(raw,sec[2]);declarations=[]
    for _ in range(n):t,p=uint(raw,p);declarations.append(t)
    assert p==sec[3];return types[declarations[index-878]]


def static_strings(raw,ranges):
    targets={ptr:(length,text.encode()) for category in NAMES for ptr,length,text in
      ((POINTERS[category][0],POINTERS[category][1],NAMES[category][0]),(POINTERS[category][2],POINTERS[category][3],NAMES[category][1]))}
    sec=next(x for x in ranges if x[0]==11);n,p=uint(raw,sec[2]);found={}
    for _ in range(n):
        flags,p=uint(raw,p)
        if flags==2:memory,p=uint(raw,p);assert memory==0
        assert flags in (0,1,2)
        if flags!=1:
            assert raw[p]==0x41;p+=1;offset,p=uint(raw,p);assert raw[p]==0x0b;p+=1
        length,p=uint(raw,p);end=p+length
        if flags!=1:
            for ptr,(size,expected) in targets.items():
                if offset<=ptr and ptr+size<=offset+length:
                    actual=raw[p+ptr-offset:p+ptr-offset+size];assert actual==expected;found[ptr]=actual.decode()
        p=end
    assert p==sec[3] and set(found)==set(targets);return found


def closure(snapshot,entries):
    pending=['__init__.py',*entries];seen=set();base=snapshot/'reconstruction/core_spec'
    while pending:
        name=pending.pop()
        if name in seen:continue
        seen.add(name)
        for node in ast.walk(ast.parse((base/name).read_text())):
            if isinstance(node,ast.ImportFrom) and node.level:
                assert node.level==1
                pending.extend(x.replace('.','/')+'.py' for x in ([node.module] if node.module else [a.name for a in node.names]))
            if isinstance(node,ast.Import):
                pending.extend(a.name.removeprefix('core_spec.').replace('.','/')+'.py' for a in node.names if a.name.startswith('core_spec.'))
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):assert node.func.id!='__import__'
    return sorted('reconstruction/core_spec/'+x for x in seen)


def initial_game(c,actual):
    s=c['input'];raw=bytearray(2592)
    for o,value in ((968,c['capacity']),(976,c['head']),(980,c['count']),(1432,1),(1536,s['max_hp_bits']),
                    (2540,s['wave_2532']),(184,u(actual,184)),(188,len(s['map_id'].encode('ascii'))),(1880,128),(1884,u(actual,1884))):put(raw,o,value)
    # Fixture allocation address is absent from the sidecar. If the first call
    # grows a nonempty allocation, the one old pointer word is observational.
    put(raw,972,1 if not c['capacity'] else u(actual,972))
    struct.pack_into('<Q',raw,1336,999);struct.pack_into('<d',raw,992,s['incoming_total_992'])
    raw[360:362]=b'\1\1'
    for o,key in ((2587,'phase_2579'),(2576,'protection_2568'),(2582,'mode_2574'),(2578,'minimum_one_2578')):raw[o]=s[key]
    for key,o in OFFSETS.items():put(raw,o,s[key])
    return raw


def review_cases(cases,observations,counts):
    for c,a in zip(cases,observations):
        assert c['id']==a['id'];assert len(c['ops'])==len(a['stages'])==len(c['expected'])
        s=dict(c['input']);assert s['mode_2574']==0 and not s['units'] and not s['buffs'] and not s['modifiers']
        assert s['armor_1392_bits']==0 and s['nearby_reduction_1444_bits']==0 and s['reserve_768_bits']==0 and s['shield_source_1344']==0
        cap,head,length=c['capacity'],c['head'],c['count'];data=[list(bytes.fromhex(x)) for x in c['storage']]
        labels=[('', '', '') for _ in data];previous=None
        for op,observed,model_expected in zip(c['ops'],a['stages'],c['expected']):
            assert set(op)=={'amount_bits','category','critical','now_bits'};before_cap=cap
            guard=s['phase_2579']!=1 or s['protection_2568']&1
            if not guard:
                amount=op['amount_bits'];absorbed=0;shield=s['shield_1532_bits']
                if ff(shield)>0:
                    absorbed=shield if ff(shield)<ff(amount) else amount
                    s['shield_1532_bits']=fsub(shield,absorbed)
                    x=fsub(s['barrier_1536_bits'],absorbed);s['barrier_1536_bits']=x if ff(x)>0 else 0
                    s['shield_source_remaining_1348_bits']=fsub(s['shield_source_remaining_1348_bits'],absorbed)
                    s['absorbed_740_bits']=fadd(absorbed,s['absorbed_740_bits'])
                    s['maximum_shield_744_bits']=shield if ff(shield)>ff(s['maximum_shield_744_bits']) else s['maximum_shield_744_bits']
                    if ff(s['shield_1532_bits'])<=0:
                        for key in ('barrier_1536_bits','shield_source_remaining_1348_bits','absorbed_740_bits','maximum_shield_744_bits'):s[key]=0
                    amount=fsub(amount,absorbed)
                hp_before_clamp=fsub(s['hp_1528_bits'],amount);s['hp_1528_bits']=hp_before_clamp
                s['incoming_total_992']+=ff(amount);s['last_hit_1648_bits']=op['now_bits']
                cutoff=ff(fadd(op['now_bits'],0xc1200000))
                while length and (length>399 or ff(u(bytes(data[head][24:28]),0))<cutoff):
                    counts['pruned_for_count' if length>399 else 'pruned_for_time']+=1
                    head=(head+1)%cap;length-=1
                if length==cap:
                    old_cap=cap;cap=max(4,cap*2);data.extend([[None]*48 for _ in range(cap-old_cap)]);labels.extend([None]*(cap-old_cap))
                    if head>old_cap-length:
                        prefix=old_cap-head;suffix=length-prefix
                        if prefix>suffix and cap-old_cap>=suffix:
                            data[old_cap:old_cap+suffix]=[x[:] for x in data[:suffix]];labels[old_cap:old_cap+suffix]=labels[:suffix];counts['grow_move_suffix']+=1
                        else:
                            destination=cap-prefix;data[destination:cap]=[x[:] for x in data[head:old_cap]];labels[destination:cap]=labels[head:old_cap]
                            head=destination;counts['grow_move_prefix']+=1;counts['grow_tie']+=int(prefix==suffix)
                    else:counts['grow_nonwrapped']+=1
                slot=(head+length)%cap;raw=data[slot][:];category=op['category'] if op['category'] in NAMES else 0
                np,nl,ip,il=POINTERS[category]
                raw[:46]=struct.pack('<6I5I2B',1,0,np,nl,ip,il,op['now_bits'],amount,absorbed,hp_before_clamp,s['max_hp_bits'],4,int(op['category']==2))
                #19964 performs real locale-table lookup. Its translated name
                #slice can be heap-owned even when English equals the literal
                #lookup key. Source1 and the fallback icon remain exact here.
                raw[8:12]=[None]*4
                data[slot]=list(raw);labels[slot]=('',*NAMES[category]);length+=1
                if s['minimum_one_2578'] and ff(s['hp_1528_bits'])<1:s['hp_1528_bits']=0x3f800000
                counts['appends']+=1
            else:counts['guard_stages']+=1
            assert observed['header']=={'capacity':cap,'head':head,'count':length}
            scalar={k:s[k] for k in OFFSETS};scalar['incoming_total_992_bits']=struct.pack('>d',s['incoming_total_992']).hex();scalar['phase_2579']=s['phase_2579']
            assert observed['scalar']==scalar,(c['id'],counts['stages'],'scalar')
            assert len(observed['storage'])==cap
            active_slots={(head+j)%cap for j in range(length)}
            for slot,(known,rawhex) in enumerate(zip(data,observed['storage'])):
                actual=bytes.fromhex(rawhex);assert len(actual)==48
                for offset,(want,got) in enumerate(zip(known,actual)):
                    if want is None:
                        if 8<=offset<12 and labels[slot] and labels[slot][1]:
                            counts['translated_name_pointer_observations']+=1;counts['translated_name_pointer_nonzero']+=bool(got)
                        else:
                            assert slot not in active_slots or offset in (46,47)
                            counts['independently_uninitialized_bytes']+=1;counts['independently_uninitialized_nonzero']+=bool(got)
                    else:
                        assert want==got,(c['id'],counts['stages'],slot,offset,want,got)
                        counts['independent_strict_backing_bytes']+=1
                        if offset in (46,47):counts['strict_padding_bytes']+=1
            assert len(observed['active'])==length
            for j,row in enumerate(observed['active']):
                slot=(head+j)%cap;assert row['slot']==slot and row['raw_hex']==observed['storage'][slot] and tuple(row['strings'])==labels[slot]
                if labels[slot] and labels[slot][1]:counts['static_pointer_checked_active_rows']+=1
            game=bytes.fromhex(observed['raw_game2592_hex']);assert len(game)==2592
            assert [u(game,o) for o in (968,976,980)]==[cap,head,length] and u(game,972)==observed['history_pointer']
            for key,offset in OFFSETS.items():assert u(game,offset)==scalar[key]
            assert struct.unpack_from('<Q',game,992)[0]==int(scalar['incoming_total_992_bits'],16)
            before=bytearray(previous if previous is not None else initial_game(c,game));put(before,2352,op['now_bits'])
            deltas=[[o,u(game,o)] for o in range(0,2592,4) if u(before,o)!=u(game,o)]
            recorded=observed['game_changes']
            if previous is None and c['capacity'] and cap!=before_cap:
                deltas=[x for x in deltas if x[0]!=972];recorded=[x for x in recorded if x[0]!=972];counts['first_old_heap_pointer_words_observed']+=1
            assert deltas==recorded,(c['id'],counts['stages'],'rawG changes',deltas,recorded)
            previous=game
            metadata=bytes.fromhex(observed['message_metadata_backing_hex']);assert len(metadata)==u(game,1880)*16
            assert len(observed['packets'])==u(game,1888)
            for j,packet in enumerate(observed['packets']):
                assert packet['capacity']==u(metadata,j*16) and len(bytes.fromhex(packet['raw_hex']))==u(metadata,j*16+8)
                assert packet['opcode']==struct.unpack_from('<H',metadata,j*16+12)[0];counts['packet_payload_bytes']+=len(packet['raw_hex'])//2
            nm=bytes.fromhex(observed['notification_metadata_backing_hex']);assert len(nm)==u(game,1892)*12
            assert len(observed['notifications'])==u(game,1900)
            for j,n in enumerate(observed['notifications']):assert n['capacity']==u(nm,j*12) and len(bytes.fromhex(n['raw_hex']))==u(nm,j*12+8)
            counts['rawG_bytes']+=2592;counts['stages']+=1
        counts['cases']+=1


def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',default=DEFAULT);args=p.parse_args()
    batch=Path(args.batch);batch=batch if batch.is_absolute() else ROOT/'evidence'/batch
    receipt_file=batch/'incoming-history135-comparison.json';receipt=json.loads(receipt_file.read_text());assert receipt['phase']=='full' and receipt['differences']==0
    frozen=receipt['source_sha256_before'];assert frozen==receipt['source_sha256_after'];snapshot=batch/'source-snapshot'
    for name,digest in frozen.items():assert sha(snapshot/name)==sha(ROOT/name)==digest,name
    core=closure(snapshot,['incoming_history135.py','incoming135.py']);assert set(core)<=frozen.keys()
    for name,digest in receipt['artifacts'].items():assert sha(batch/name)==digest,name
    raw=ORIGINAL.read_bytes();assert hashlib.sha256(raw).hexdigest()==ORIGINAL_SHA==receipt['original_sha256'];sections=section_ranges(raw)
    manifest=json.loads((batch/'manifest.json').read_text());module=(batch/manifest['module_file']).read_bytes();changed=section_ranges(module)
    assert hashlib.sha256(module).hexdigest()==manifest['module_sha256']
    assert [x[0] for x in sections]==[x[0] for x in changed] and 8 not in [x[0] for x in sections]
    for left,right in zip(sections,changed):
        if left[0]!=7:assert raw[left[1]:left[3]]==module[right[1]:right[3]]
    assert exports(module,changed)==exports(raw,sections)+[['research135_incoming_damage',0,1073]]
    role,=manifest['roles'];assert role['index']==1073 and role['parameters_hex']=='7f7d7e7f7f7f' and role['results_hex']==''
    assert signature(raw,sections,1073)==('7f7d7e7f7f7f','')
    a,b=body(raw,sections,1073);assert (a,b)==(role['body_start'],role['body_end']);assert hashlib.sha256(raw[a:b]).hexdigest()==role['body_sha256']=='ae8055c998f7dad212a404de8cee67a5375c9f4f94750f1e69fd5119f4f9e076'
    literals=static_strings(raw,sections)
    assert manifest['denied_function_import_count']==878 and receipt['runtime']['denied_imports']==878 and receipt['runtime']['host_calls']==0
    assert receipt['runtime']['memory_pages']==512 and receipt['runtime']['max_memory_bytes']<=32*1024*1024
    assert receipt['process']['exit_code']==0 and receipt['process']['deadline_seconds']==60
    assert not receipt['runtime']['app_start_called'] and not receipt['runtime']['network_used'] and not receipt['runtime']['user_saves_accessed']
    assert receipt['independent_expected_before_original'] and not receipt['original_input_contains_expected'] and set(receipt['original_input_keys'])==INPUT_KEYS
    command=receipt['process']['command'];assert command[1:3]==['--max-old-space-size=512','--wasm-max-mem-pages=512']
    assert Path(command[0])==ROOT/'.toolchain/runtime/node_modules/node/bin/node'
    assert sha(Path(command[0]))=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
    assert command[3:]==[str(ROOT/'scripts/run_incoming_history135_oracle.mjs'),str(batch),str(batch/'incoming-history135-inputs.json')]
    assert receipt['runtime']==json.loads((batch/'incoming-history135-runtime.json').read_text())
    cases=json.loads((batch/'incoming-history135-fixtures.json').read_text());inputs=json.loads((batch/'incoming-history135-inputs.json').read_text())
    assert len(cases)==len(inputs)==receipt['cases'] and all(set(c)==INPUT_KEYS for c in inputs)
    assert [c['id'] for c in cases]==list(range(len(cases)))
    assert [{k:c[k] for k in receipt['original_input_keys']} for c in cases]==inputs
    for key in list(sys.modules):
        if key.startswith('core_spec') or key in ('build_full135_oracle','build_upgrade134_oracle','source_closure135'):del sys.modules[key]
    sys.path.insert(0,str(snapshot/'scripts'));spec=importlib.util.spec_from_file_location('review_frozen_history_checker',snapshot/'scripts/check_incoming_history135.py');author=importlib.util.module_from_spec(spec);spec.loader.exec_module(author)
    for c in cases:assert author.expected(c)==c['expected']
    counts=Counter()
    with (batch/'incoming-history135-results.jsonl').open() as stream:
        review_cases(cases,(json.loads(line) for line in stream),counts)
        assert not stream.read().strip()
    assert counts['cases']==receipt['cases'] and counts['stages']==receipt['stages']==receipt['runtime']['calls']
    assert counts['grow_tie']>0 and counts['grow_move_suffix']>0 and counts['grow_move_prefix']>0 and counts['pruned_for_count']>0 and counts['pruned_for_time']>0 and counts['guard_stages']>0
    for name,digest in frozen.items():assert sha(snapshot/name)==sha(ROOT/name)==digest
    terminated=False
    try:os.kill(receipt['process']['pid'],0)
    except ProcessLookupError:terminated=True
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('incoming-history0135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    script=Path(__file__);(out/'reviewer-source.py').write_bytes(script.read_bytes())
    review=dict(status='passed_scoped_independent_read_only_review',receipt=str(receipt_file.relative_to(ROOT)),receipt_sha256=sha(receipt_file),
        original_sha256=ORIGINAL_SHA,source_files=len(frozen),core_closure=core,current_source_drift={},source_snapshots_verified=True,
        expected_model_replayed_without_original=True,raw_backing_independently_recomputed=True,static_pointer_literal_checks=literals,
        only_wasm_export_section_changed=True,exact_original_exports_preserved=True,original1073_body_and_all_callees_unchanged=True,
        review_counts=dict(counts),author_comparison_scope=receipt['comparison'],process_terminal_receipt_exit0=True,pid_missing_at_review=terminated,
        original_executed_by_reviewer=False,author_sources_modified_by_reviewer=False,reviewer_sha256=sha(script),
        limitations=['History and scalar component only; full1073 rawG/registry/keyed/proc semantics are not independently restored.',
          'GUID0/no source unit and spellID0 English fallback domain; no realDBC metadata or world/headless integration.',
          'Source1 and fallback icon pointers additionally compared exactly; translated name heap pointer is normalized but UTF8 contents/length are strict. Static name literals are input lookup keys, not necessarily returned slices.',
          'Only new allocator-unwritten bytes remain unknown; existing backing and old padding are strict.',
          'The original fixture history allocation address before a first grow is absent; that one old pointer word is observational in first rawG delta reconstruction.'])
    (out/'review.json').write_text(json.dumps(review,indent=2)+'\n');print(json.dumps({'directory':str(out),'review_sha256':sha(out/'review.json'),'counts':dict(counts)},indent=2))


if __name__=='__main__':main()
