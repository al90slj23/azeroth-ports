#!/usr/bin/env python3
"""Independent read-only review of partial4253 App constructor projection.

Interprets the original straight-line window with a separate byte memory at
different App/scratch addresses. Unknown reads stay None; only explicitly
decoded immutable source ranges have known initial-zero bytes. No production
module is imported or original WASM executed. Game install is only a contract.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import ast,hashlib,json,re,sqlite3,struct,sys
sys.dont_write_bytecode=True
from review_app_history135 import sections,uint,static_data

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'evidence/app-state0135-static-check-20261101T121056.399055Z'
RECEIPT_SHA='93c92bd3525979fe61ce187742eb7c763d7ed02be64150d338880ccc80f1d7c2'
MODEL_SHA='4f1e4a3b048a9491ea8edae34ec9e1c97916d8f2e1ef06b6db12c1b9bb9fb1da'
SOURCE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
INDEX_SHA='b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
M32=(1<<32)-1;M64=(1<<64)-1


def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def closure():
    pending=[ROOT/'scripts/check_app_state135.py'];seen=set()
    while pending:
        p=pending.pop()
        if p in seen:continue
        seen.add(p)
        for n in ast.walk(ast.parse(p.read_text())):
            if not isinstance(n,ast.ImportFrom):continue
            if n.level:
                assert n.level==1
                pending.extend(p.parent/(v.replace('.','/')+'.py')for v in([n.module]if n.module else[a.name for a in n.names]))
            elif n.module and n.module.startswith('core_spec'):
                pending.append(ROOT/'reconstruction/core_spec/__init__.py')
                if n.module!='core_spec':pending.append(ROOT/'reconstruction'/(n.module.replace('.','/')+'.py'))
                else:pending.extend(ROOT/'reconstruction/core_spec'/(a.name+'.py')for a in n.names if(ROOT/'reconstruction/core_spec'/(a.name+'.py')).exists())
            elif n.module and(ROOT/'scripts'/(n.module+'.py')).is_file():pending.append(ROOT/'scripts'/(n.module+'.py'))
    return set(str(p.relative_to(ROOT))for p in seen)


class Memory:
    def __init__(self):self.cells={};self.writes=[]
    def read(self,address,count):return tuple(self.cells.get(address+j)for j in range(count))
    def write(self,address,data,label):
        data=tuple(data);overlap=[j for j in range(len(data))if address+j in self.cells]
        self.cells.update({address+j:v for j,v in enumerate(data)})
        self.writes.append(dict(address=address,length=len(data),kind=label,known=sum(v is not None for v in data),overlap_bytes=len(overlap)))
    def load(self,address,width):
        data=self.read(address,width)
        return int.from_bytes(bytes(data),'little')if all(v is not None for v in data)else None


def execute_window(text,case,immutable):
    app=0x70000;scratch=0x90000;memory=Memory();local={};stack=[];opcounts=Counter();selects=[]
    for address,data in immutable.items():memory.write(address,data,'actual immutable static data')
    blocks={b['offset']:bytes.fromhex(b['data_hex'])for b in case['live_blocks']}
    memory.write(scratch+408,blocks.get(4160,(None,)*368),'explicit settings copy input')
    memory.write(scratch+1020,blocks.get(4980,(None,)*36),'explicit preferences copy input')
    loaded=blocks.get(4528,(None,)*48);memory.write(scratch+368,loaded[12:48],'explicit loaded-state copy input')
    memory.write(scratch+780,bytes.fromhex(case['history240_hex']),'explicit empty history input')
    local.update({0:case['server_pointer'],1:app,2:None if any(v is None for v in loaded[8:12])else int.from_bytes(bytes(loaded[8:12]),'little'),
        3:scratch,4:case['startup_flag5161'],9:case['transport_pointer'],52:case['lcg_input'],
        58:None if any(v is None for v in loaded[:8])else int.from_bytes(bytes(loaded[:8]),'little')})
    maps=bytes.fromhex(case['hash_maps128_hex'])
    for j,(first,second)in enumerate(((57,53),(54,51),(55,50),(56,59))):local[first],local[second]=struct.unpack_from('<2Q',maps,j*32+16)
    for line in text.splitlines():
        line=re.sub(r'\(;.*?;\)','',line).strip()
        if not line:continue
        parts=line.split();op=parts[0];opcounts[op]+=1;arg=parts[1]if len(parts)>1 else None
        match=re.search(r'offset=(\d+)',line);offset=int(match.group(1))if match else 0
        if op=='local.get':stack.append(local.get(int(arg)))
        elif op=='local.set':local[int(arg)]=stack.pop()
        elif op=='local.tee':local[int(arg)]=stack[-1]
        elif op in('i32.const','i64.const'):stack.append(int(arg)&(M32 if op=='i32.const'else M64))
        elif op in('i32.load','i64.load'):
            address=stack.pop();assert address is not None;stack.append(memory.load(address+offset,4 if op=='i32.load'else 8))
        elif re.fullmatch(r'i(?:32|64)\.store(?:8|16)?',op):
            value=stack.pop();address=stack.pop();assert address is not None
            width=int(op[op.index('store')+5:])//8 if op.endswith(('8','16'))else int(op[1:op.index('.')])//8
            data=(None,)*width if value is None else(value&((1<<(8*width))-1)).to_bytes(width,'little')
            memory.write(address+offset,data,op)
        elif op=='select':
            condition,no,yes=stack.pop(),stack.pop(),stack.pop();assert condition is not None;selects.append(condition);stack.append(yes if condition else no)
        elif op=='memory.copy':
            count,source,destination=stack.pop(),stack.pop(),stack.pop();assert None not in(count,source,destination)
            data=memory.read(source,count);memory.write(destination,data,'memory.copy temporary snapshot')
        elif op=='memory.fill':
            count,value,destination=stack.pop(),stack.pop(),stack.pop();assert None not in(count,destination)
            memory.write(destination,((value&255)if value is not None else None,)*count,'memory.fill')
        elif op.startswith(('i32.','i64.')):
            right,left=stack.pop(),stack.pop();width=32 if op.startswith('i32.')else 64;mask=(1<<width)-1
            if left is None or right is None:value=None
            else:
                name=op.split('.')[1]
                if name=='add':value=left+right
                elif name=='mul':value=left*right
                elif name=='shr_u':value=left>>(right&(width-1))
                elif name=='xor':value=left^right
                elif name=='and':value=left&right
                elif name=='or':value=left|right
                elif name=='gt_u':value=int(left>right)
                else:raise AssertionError('Unreviewed instruction '+op)
                value&=mask
            stack.append(value)
        else:raise AssertionError('Calls/branches outside static window '+line)
    assert not stack
    result=memory.read(app,5168)
    appwrites=[]
    for write in memory.writes:
        if app<=write['address']<app+5168:appwrites.append(dict(offset=write['address']-app,**{k:v for k,v in write.items()if k!='address'}))
    return result,dict(app_base=app,scratch_base=scratch,opcounts=dict(opcounts),select_conditions=selects,app_writes=appwrites)


def literal_contract(model,name):
    node=next(n for n in ast.parse(model).body if isinstance(n,ast.FunctionDef)and n.name==name)
    ret=next(n for n in node.body if isinstance(n,ast.Return));assert isinstance(ret.value,ast.Call)and ret.value.func.id=='dict'
    return{k.arg:ast.literal_eval(k.value)for k in ret.value.keywords}


def main():
    receipt_path=DIRECTORY/'comparison.json';assert sha(receipt_path)==RECEIPT_SHA
    receipt=json.loads(receipt_path.read_text());assert receipt['source_count']==10 and receipt['controlled_static_cases']==32 and receipt['new_original_calls']==0
    claimed=receipt['source_sha256_before'];assert set(claimed)==closure()and claimed==receipt['source_sha256_after']
    for n,h in claimed.items():assert sha(ROOT/n)==h==sha(DIRECTORY/'source-snapshot'/n)
    model=(ROOT/'reconstruction/core_spec/app_state135.py').read_text();assert hashlib.sha256(model.encode()).hexdigest()==MODEL_SHA
    before={n:sha(ROOT/n)for n in claimed}
    for path in(Path(__file__),ROOT/'scripts/review_app_history135.py'):before[str(path.relative_to(ROOT))]=sha(path)
    raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA and sha(PROFILE/'index.sqlite')==INDEX_SHA
    table,tableproof=static_data(raw,5222424,16);server,serverproof=static_data(raw,5221378,13);vt,vtproof=static_data(raw,5305816,20)
    assert struct.unpack('<4I',table)==(5222416,0,0,0)and server==b'azeroth.local'and struct.unpack('<5I',vt)[1:]==(12,4,4472,4473)
    element=next(s for s in sections(raw)if s[0]==9);count,pos=uint(raw,element[2]);assert count==1
    flag,pos=uint(raw,pos);assert flag==0 and raw[pos:pos+3]==b'\x41\x01\x0b';pos+=3;n,pos=uint(raw,pos);entries=[]
    for _ in range(n):value,pos=uint(raw,pos);entries.append(value)
    assert pos==element[3] and entries[4472-1]==58521 and entries[4473-1]==83825
    con=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row;functions=[];texts={}
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        for idx in(4253,880,1371,58521,83825,122123):
            row=dict(con.execute('SELECT * FROM functions WHERE idx=?',(idx,)).fetchone());stream.seek(row['wat_start']);text=stream.read(row['wat_end']-row['wat_start']);texts[idx]=text
            assert text.startswith(f'  (func (;{idx};)'.encode());functions.append(dict(**row,wat_sha256=hashlib.sha256(text).hexdigest(),body_sha256=hashlib.sha256(raw[row['body_start']:row['body_end']]).hexdigest()))
    con.close();lines=texts[4253].decode().splitlines();window='\n'.join(lines[8601:8894])+'\n'
    assert window==(DIRECTORY/'constructor-window.wat.txt').read_text()and hashlib.sha256(window.encode()).hexdigest()==receipt['window_sha256']
    inputs=json.loads((DIRECTORY/'inputs.json').read_text());expected=json.loads((DIRECTORY/'independent-expected.json').read_text())
    assert sha(DIRECTORY/'inputs.json')==receipt['input_sha256']and sha(DIRECTORY/'independent-expected.json')==receipt['independent_expected_sha256']
    assert len(inputs)==len(expected)==32;rows=[];known=unknown=0
    for i,(case,want,record)in enumerate(zip(inputs,expected,receipt['cases'])):
        assert case['id']==record['id']==i and len(want)==5168
        actual,trace=execute_window(window,case,{5222424:table,5221378:server})
        assert list(actual)==want
        count=sum(v is not None for v in actual);assert count==record['known_bytes']==(730 if i%2==0 else 1182)
        assert count+record['unknown_bytes']==5168 and record['unknown_bytes']==(4438 if i%2==0 else 3986)
        assert all(v is None for lo,length in((8,8),(24,2584),(2616,760),(3380,372),(4752,16))for v in actual[lo:lo+length])
        if i%2==0:assert all(v is None for lo,length in((4160,368),(4528,48),(4980,36))for v in actual[lo:lo+length])
        assert bytes(actual[4148:4155])==bytes(7)and bytes(actual[5163:5167])==(-16711680&M32).to_bytes(4,'little')and actual[5167]is None
        known+=count;unknown+=5168-count;rows.append(dict(id=i,known=count,unknown=5168-count,**trace))
    assert(known,unknown)==(30592,134784)==(receipt['known_bytes_checked'],receipt['unrestored_or_inactive_None_bytes_checked'])
    install=literal_contract(model,'game_install_contract135');owner=literal_contract(model,'app_owner_layout135')
    assert install['destination_app_offset']==16 and install['bytes']==2592 and install['absent_tag']==2 and install['drop_old_unless_absent_function']==1627
    assert install['move_not_clone']is True and install['additional_world_rc_increment_from_copy']==0 and install['source_must_be_forgotten']is True and install['complete_caller_semantics_recovered']is False
    assert owner['allocation_bytes']==5184 and owner['app_offset']==16 and owner['app_bytes']==5168 and owner['bytes9_through15_unknown']is True and owner['final_holder_counts_not_predicted']is True
    legal=next(n for n in ast.walk(ast.parse(model))if isinstance(n,ast.FunctionDef)and n.name=='legal_full_app');assert ast.literal_eval(next(n for n in legal.body if isinstance(n,ast.Return)).value)is False
    tick=texts[83825]
    for token in(b'i32.load offset=8',b'i32.const 16',b'i32.add',b'f64.const 0x1.f4p+9',b'f64.div',b'call 880'):assert token in tick
    assert b'call 867'in texts[122123]
    correction=DIRECTORY/'source-closure-correction.json';assert sha(correction)=='9a473472c5612ecddac91ff298c08cdf219be339924ea2aa085cadd3b5b9d48c'
    old=ROOT/'evidence/app-state0135-static-check-20261101T115726.290244Z'
    for name in('inputs.json','independent-expected.json','constructor-window.wat.txt'):assert sha(old/name)==sha(DIRECTORY/name)
    assert receipt['original_function_executed']is False and receipt['original_module_instantiated']is False and receipt['app_complete_or_legal']is False
    after={n:sha(ROOT/n)for n in before};assert before==after
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('app-state0135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    for n,h in before.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    (out/'constructor-window.wat.txt').write_text(window)
    for name,idx,lo,hi in(('owner',4253,8938,8987),('tick-closure',4253,9293,9373),('game-move880',880,15850,15864),('game-move1371',1371,11306,11326)):
        fragment=b'\n'.join(texts[idx].splitlines()[lo-1:hi])+b'\n';(out/f'{name}-{idx}-{lo}-{hi}.wat').write_bytes(fragment)
    (out/'83825.wat').write_bytes(tick);(out/'122123.wat').write_bytes(texts[122123]);details=out/'independent-byte-write-traces.json';details.write_text(json.dumps(rows,indent=2)+'\n')
    result=dict(status='passed_scoped_static_read_only_review',version='0.135.1',build='0898d5e3',receipt=str(receipt_path.relative_to(ROOT)),receipt_sha256=RECEIPT_SHA,
        production_sha256=MODEL_SHA,author_source_closure=10,review_source_sha256_before=before,review_source_sha256_after=after,
        original_sha256=SOURCE_SHA,functions=functions,static_data=dict(table=tableproof,server=serverproof,frame_vtable=vtproof),
        static_cases=32,known_bytes_checked=known,None_bytes_checked=unknown,known_without_livecopies=730,None_without_livecopies=4438,
        known_with_three_explicit_livecopies=1182,None_with_livecopies=3986,
        seed4936_select_conditions_observed=sorted({v for row in rows for v in row['select_conditions']}),
        interpreter=dict(independent_byte_memory=True,app_base=0x70000,scratch_base=0x90000,different_addresses_from_author=True,
            unknown_unmapped_reads_remain_None=True,static_zero_only_in_explicitly_decoded_immutable_ranges=True,
            loads_stores_use_actual_width_and_unaligned_offsets=True,memory_copy_takes_temporary_snapshot=True,
            original_branches_or_calls_not_executed=True),
        game_move_contract=install,owner_layout_contract=owner,tick_environment_rc_offset=8,tick_rc_app_offset=16,tick_interval_milliseconds=25,
        legal_full_app=False,reviewer_imported_production=False,new_original_calls=0,new_original_cases=0,
        source_closure_correction=dict(old_count=7,new_count=10,path=str(correction.relative_to(ROOT)),sha256=sha(correction),three_input_expected_window_artifacts_identical=True),
        actual_constructor_capture_comparison=dict(status='separate_not_reviewed_here',included_in_static32cases=False),
        limitations=['This independentlyreplays32straightlineWATcases,notneworiginal4253/880orfullAppacceptance.',
            'Settings/loadedstate/preferences,pointers/hashentropyremainexplicitinputs;knownbytesarenotindependentproducerproof.',
            'All32declaredseed4936selectconditionsare0;alternatebranchhasstaticexpressionreasoningonly,notcasecoveragehere.',
            'Gameinstallationisonlyamovecontract;24129,oldGamedestruction/sourceforget/fullcallersemanitcsstillunimplemented.',
            'Pointerdecoderrequiresactualguardedvtableandvalidmemoryprovider;arithmeticdecodealoneisnotApplegality/ownershipproof.'],
        artifacts={p.name:sha(p)for p in out.iterdir()if p.is_file()})
    target=out/'review.json';target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(target),static_cases=32,new_original_calls=0)))


if __name__=='__main__':main()
