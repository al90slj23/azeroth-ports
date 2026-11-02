#!/usr/bin/env python3
"""Different-author read-only139 raw-world/current-query audit;0 target calls.

Only stdlib and a previously independent, stdlib-only mathematical reviewer
execute. No author producer, model, builder, checker or runner is imported.
The old mathematical reference is rebound to complete139 WAT and current139
canonical inputs; no old runtime input, expected value or actual is consumed.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import argparse,ast,hashlib,json,math,os,re,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_player_motion135 as M
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/world-query139-oracle-20261102T034447.093808Z'
MODEL=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model'
OBS=ROOT/'evidence/asset-world139-observation-check-20261102T032808.223945Z'
STATIC=ROOT/'evidence/world139-static-20261102T032207.619660Z'
V2=ROOT/'evidence/entry-world139-v2-probe-20261102T030946.739944Z'
WASM=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
WASM_SHA='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
SNAP_SHA='ed3a755752ddf9907712b408f7ef042f5a9407d684d0aa6afd3f0a394bbd7ce2'
PIN='9e197108372b96a29397c0e3c4f5ba312e182a3cd4ab2872d986bf6119c494ef'
HANDOFF_SHA='51de826f41c2e8dcc10ecfc2e088f26ea526f095e2f88d94d2ae4bdf7fd7e42f'
M_SHA='8a339b74435adbc4abcf5aff7f3a25a24d5f8495653e42135f06aa94230de2b2'
PAIRS=((29631,29912),(18670,18742),(46295,47025),(5795,5787),(23181,23333))
PANIC={(29631,81):(5512528,5762524),(29631,193):(5508976,5762404),(23181,203):(5512672,5762668)}
F=M.F;B=M.B;add=M.add;sub=M.sub;mul=M.mul;div=M.div;sha=M.sha;load=M.load;save=M.save;digest=M.digest

def guard_imports():
    assert sha(Path(M.__file__))==M_SHA
    assert not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    # An audit event rejects accidental author-code execution even if a later
    # edit adds an import. Source bytes remain readable for static inspection.
    allowed={Path(__file__).resolve(),Path(M.__file__).resolve()}
    forbidden=[]
    def hook(event,args):
        if event=='exec':
            p=Path(args[0].co_filename).resolve()
            if p.is_relative_to(ROOT)and p not in allowed:forbidden.append(str(p));raise RuntimeError('Author/research executable code rejected: '+str(p))
    sys.addaudithook(hook);return forbidden

def source_guard(folder,record):
    sources=record['source_sha256_before'];assert sources==record['source_sha256_after']
    for name,h in sources.items():assert sha(ROOT/name)==h==sha(folder/'source-snapshot'/name),name
    edges=M.source_edges(folder/'source-snapshot',set(sources))
    return sources,edges

def parsed_module(raw):
    sections=M.sections(raw);by={r[0]:r for r in sections};assert 8 not in by
    n,p=M.leb(raw,by[1][2]);types=[]
    for _ in range(n):
        assert raw[p]==0x60;p+=1;n,p=M.leb(raw,p);a=raw[p:p+n].hex();p+=n;n,p=M.leb(raw,p);b=raw[p:p+n].hex();p+=n;types.append((a,b))
    assert p==by[1][3];n,p=M.leb(raw,by[2][2]);imports=[]
    for _ in range(n):
        size,p=M.leb(raw,p);module=raw[p:p+size].decode();p+=size;size,p=M.leb(raw,p);name=raw[p:p+size].decode();p+=size;kind=raw[p];p+=1;idx,p=M.leb(raw,p);assert kind==0;imports.append((module,name,idx))
    assert len(imports)==882 and p==by[2][3];n,p=M.leb(raw,by[3][2]);decl=[]
    for _ in range(n):idx,p=M.leb(raw,p);decl.append(idx)
    assert p==by[3][3];n,p=M.leb(raw,by[10][2]);ranges={}
    for index in range(882,882+n):size,p=M.leb(raw,p);ranges[index]=(p,p+size);p+=size
    assert p==by[10][3]and n==len(decl)
    return sections,types,imports,decl,ranges

def static_admission(out):
    original=WASM.read_bytes();assert digest(original)==WASM_SHA
    sections,types,imports,decl,ranges=parsed_module(original);trace=load(STATIC/'trace.json');assert sha(STATIC/'trace.json')=='7a66273b70a4a5c215092a0981a1652d67786576087510933f05adc810b11d16'
    roles=load(RUN/'manifest.json');changed=(RUN/roles['module_file']).read_bytes();assert digest(changed)==roles['module_sha256'];fresh=M.sections(changed)
    assert len(sections)==len(fresh)and[tuple(x)[0]for x in sections]==[x[0]for x in fresh]
    for a,b in zip(sections,fresh):
        if a[0]!=7:assert original[a[1]:a[3]]==changed[b[1]:b[3]]
    oldEx=M.exports(original,next(r for r in sections if r[0]==7));newEx=M.exports(changed,next(r for r in fresh if r[0]==7))
    additions=[(row['export'],0,row['index'])for row in roles['roles'].values()]+[(roles['stack_export'],3,0)];assert newEx==oldEx+additions
    assert ('__wbindgen_malloc',0,93344)in oldEx and types[decl[93344-882]]==('7f7f','7f')
    assert [(m,n)for m,n,_ in imports]==[(r['module'],r['name'])for r in roles['original_imports']]
    globalSec=next(r for r in sections if r[0]==6);assert original[globalSec[2]:globalSec[3]].hex()=='017f01418080c0000b'
    read=M.static_reader(original);zone=read(5871348,152);assert zone.hex()==trace['source_zone152']['raw_hex'];assert struct.unpack_from('<I',zone,96)[0]==0
    center=struct.unpack_from('<2I',zone,104);fallback=struct.unpack_from('<I',zone,112)[0];radius=struct.unpack_from('<I',zone,120)[0]
    assert(center,fallback,radius)==((3323121664,3290316800),0x42880000,0x42f00000)
    pairs=[];calls=dict(PAIRS)|{80663:81897}
    oldSource=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm';assert sha(oldSource)=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
    oldRaw=oldSource.read_bytes();_,_,_,_,oldRanges=parsed_old(oldRaw)
    for old,new in PAIRS:
        texts={}
        for version,index,raw,rs in((135,old,oldRaw,oldRanges),(139,new,original,ranges)):
            record=trace['functions'][str(version)+':'+str(index)];a,b=rs[index];assert(a,b)==(record['body_start'],record['body_end'])and digest(raw[a:b])==record['body_sha256']
            path=STATIC/f'{version}-{index}.wat';wat=path.read_bytes();assert digest(wat)==record['wat_sha256'];profile=ROOT/('evidence/wasm0139-profile-20261102T012426.951871Z'if version==139 else'evidence/wasm0135-profile-20261101T031028.877964Z')
            with sqlite3.connect((profile/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:
                db.execute('pragma query_only=on');wa,wb,ba,bb=db.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(index,)).fetchone()
            assert(a,b)==(ba,bb)
            with(profile/f'official-0.{version}.{"0"if version==139 else"1"}-full.wat').open('rb')as stream:stream.seek(wa);assert stream.read(wb-wa)==wat
            texts[version]=wat.decode().splitlines()
            if version==139:
                assert types[decl[index-882]]==('7f7f7d7d','')if index in(29912,18742,23333)else types[decl[index-882]]==('7f7f7f7f','')if index==47025 else types[decl[index-882]]==('7f7f7f','')
        a,b=texts[135],texts[139];assert len(a)==len(b);changes=[]
        for line,(x,y)in enumerate(zip(a,b),1):
            if x==y:continue
            if line==1:assert re.sub(r'\(;\d+;\) \(type \d+\)','FUNCTION TYPE',x)==re.sub(r'\(;\d+;\) \(type \d+\)','FUNCTION TYPE',y);reason='function/type'
            elif re.fullmatch(r'\s*call \d+',x):assert int(y.split()[-1])==calls[int(x.split()[-1])];reason='boundcallee'
            else:
                p,q=PANIC[old,line];assert x.strip()==f'i32.const {p}'and y.strip()==f'i32.const {q}'and a[line].strip()=='call 80663'and b[line].strip()=='call 81897';reason='panic-location'
            changes.append(dict(line=line,reason=reason))
        pairs.append(dict(old_static_index=old,current139_index=new,lines=len(a),only_permitted_changes=changes))
    assert sum(c['reason']=='panic-location'for p in pairs for c in p['only_permitted_changes'])==3
    save(out/'static-admission.json',dict(pairs=pairs,zone152_sha256=digest(zone),current_original_sha256=WASM_SHA,export_only=True,imports=882,old_actual_or_expected_read=False))
    return dict(center=center,fallback=fallback,radius=radius),roles

def parsed_old(raw):
    # The old module is read only as a static binary/WAT binding. Import count
    # differs; this independent parser does not use an old result/profile model.
    ss=M.sections(raw);by={r[0]:r for r in ss};n,p=M.leb(raw,by[10][2]);ranges={}
    for i in range(878,878+n):size,p=M.leb(raw,p);ranges[i]=(p,p+size);p+=size
    assert p==by[10][3];return ss,None,None,None,ranges

def chunks(raw):
    at=0
    while at<len(raw):
        assert at+8<=len(raw);tag,n=struct.unpack_from('<4sI',raw,at);assert at+8+n<=len(raw);yield tag,raw[at+8:at+8+n];at+=8+n
    assert at==len(raw)

def raw_terrain(raw):
    result=[]
    def snap(w):
        a=float.fromhex('0x1.0aaaaaaaaaaabp+14');step=float.fromhex('0x1.0aaaaaaaaaaabp+2');q=(a-F(w))/step;r=math.trunc(q+math.copysign(float.fromhex('0x1.fffffffffffffp-2'),q));return B(a-float(r)*step)
    for tag,p in chunks(raw):
        if tag!=b'KNCM':continue
        assert len(p)>=128;offset=struct.unpack_from('<I',p,20)[0];choices=[i for i in(offset,offset-8)if 0<=i<=len(p)-8 and p[i:i+4]==b'TVCM'];assert len(choices)==1;at=choices[0];assert struct.unpack_from('<I',p,at+4)[0]==580
        heights=struct.unpack_from('<145I',p,at+8);origin=struct.unpack_from('<3I',p,104);holes=struct.unpack_from('<H',p,60)[0];vertices=[]
        for row in range(9):
            rowstep=mul(B(row),0x40855555);x=snap(sub(origin[0],rowstep))
            for col in range(9):vertices.append((x,snap(sub(origin[1],mul(B(col),0x40855555))),add(origin[2],heights[len(vertices)])))
            if row<8:
                x=sub(origin[0],add(rowstep,0x40055555))
                for col in range(8):vertices.append((x,sub(origin[1],add(mul(B(col),0x40855555),0x40055555)),add(origin[2],heights[len(vertices)])))
        assert len(vertices)==145;result.append((tuple(vertices),holes))
    assert len(result)==256;vertices=[v for rows,_ in result for v in rows];bounds=tuple(B(fn(F(v[axis])for v in vertices))for fn,axis in((min,0),(min,1),(max,0),(max,1)))
    return tuple(result),bounds

def canonical_terrain(tiles):
    data=bytearray(struct.pack('<I',len(tiles)))
    for tile,bounds in tiles:
        data.extend(struct.pack('<5I',*bounds,len(tile)))
        for vertices,holes in tile:
            data.extend(struct.pack('<HI',holes,len(vertices)))
            for v in vertices:data.extend(struct.pack('<3I',*v))
    return bytes(data)

def producer_audit(config,out):
    receipt=load(MODEL/'receipt.json');assert sha(MODEL/'receipt.json')=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48';sources,edges=source_guard(MODEL,receipt);assert len(sources)==18
    process=load(MODEL.parent/'process-terminal.json');assert process['exit_code']==0 and process['pid_missing']and process['pgid_missing']and process['seconds']<process['deadline_seconds']==300
    assert receipt['original_program_executed']is False and receipt['original_memory_read']is False and receipt['preparsed_world_input_read']is False and receipt['original_queries_executed']==0
    inventory=Path(receipt['asset_map']);assert sha(inventory)==receipt['asset_map_sha256'];rows=load(inventory);assets={}
    for name,row in rows.items():
        if not name.startswith('data/')or name.startswith('data/__index'):continue
        key=name[5:].replace('/','\\');assets[key]=row
    assert len(assets)==453;loaded=receipt['loaded_asset_sha256_after'];assert len(loaded)==451 and set(receipt['asset_requests'])==set(loaded)
    decoded=0;rawTerrain=[]
    for key,h in loaded.items():
        row=assets[key];path=(ROOT.parent/row['file']).resolve();assert path.is_relative_to(Path('/Volumes/RuiRui4TB'))and path.suffix.lower()not in('.wasm','.wat','.memory','.exe','.bin')
        assert row['exit_code']==0 and row['http_status']==200 and row['target_executed']is False and row['pid_missing']and row['pgid_missing'];assert row['url'].startswith('https://wow.aethus.pl/data/')
        assert h==row['sha256']==sha(path)and path.stat().st_size==row['bytes'];decoded+=row['bytes']
    assert decoded==receipt['raw_asset_bytes']==67281330
    assert receipt['query_scalars']==dict(center_xy_bits=list(config['center']),radius_bits=config['radius'],fallback_height_bits=config['fallback'],primary_present=False,flat_present=False)
    acquisition=Path(receipt['asset_acquisition_receipt']);assert sha(acquisition)==receipt['asset_acquisition_receipt_sha256'];a=load(acquisition)
    assert a['version']=='0.139.0'and a['stamp']=='f339dd20e0fe'and a['old_resource_bytes_reused']is False and a['old_snapshot_loaded']is False and a['resource_map_sha256']==receipt['asset_map_sha256']
    first=receipt['asset_requests'][0];assert first=='world\\maps\\azeroth\\azeroth.wdt';wdt=(ROOT.parent/assets[first]['file']).read_bytes();main=[v for tag,v in chunks(wdt)if tag==b'NIAM'];assert len(main)==1 and len(main[0])==32768
    tx,ty=(min(63,max(0,int(F(div(sub(0x46855555,w),0x44055555)))))for w in config['center']);planned=[]
    for x in range(tx-1,tx+2):
        for y in range(ty-1,ty+2):
            if 0<=x<64 and 0<=y<64 and main[0][8*(x*64+y)]&1:planned.append(f'world\\maps\\azeroth\\azeroth_{y}_{x}.adt')
    assert receipt['asset_requests'][1:10]==planned and len(planned)==9
    for name in planned:rawTerrain.append(raw_terrain((ROOT.parent/assets[name]['file']).read_bytes()))
    terrain=canonical_terrain(rawTerrain);expected=(MODEL/receipt['world_artifacts']['terrain']['file']).read_bytes();assert terrain==expected
    audit=load(Path(receipt['python_read_audit']));assert sha(Path(receipt['python_read_audit']))==receipt['python_read_audit_sha256']and audit['kind']=='Python_audit_hook_not_OS_syscall_audit'and not audit['forbidden'];assert all(r['allowed']for r in audit['events'])
    assetPaths={(ROOT.parent/assets[name]['file']).resolve()for name in loaded};seen=set()
    for row in audit['events']:
        path=Path(row['path']).resolve();assert path.suffix.lower()not in('.memory','.wasm','.wat','.exe')
        if path in assetPaths:seen.add(path)
    assert seen==assetPaths
    files={}
    for name,row in receipt['world_artifacts'].items():
        path=MODEL/row['file'];assert path.stat().st_size==row['bytes']and sha(path)==row['sha256'];files[name]=path.read_bytes()
    extent=add(config['radius'],B(20));assert tuple(sub(x,extent)for x in config['center'])==tuple(receipt['world_artifacts']['navigation']['origin_xy_bits'])
    assert math.ceil(F(add(extent,extent)))==receipt['world_artifacts']['navigation']['width']==280
    assert receipt['world_artifacts']['secondary']['width']==560 and len(files['navigation'])==78400 and len(files['secondary'])==1254400
    summary=dict(model_receipt_sha256=sha(MODEL/'receipt.json'),sources=18,source_edges=len(edges),loaded_assets=451,declared_assets=453,raw_bytes=decoded,Python_audit_events=len(audit['events']),Python_not_OS_audit=True,terrain_independently_reparsed_bytes=len(terrain),terrain_sha256=digest(terrain),nav_secondary_geometry_pipeline_reimplemented=False,nav_secondary_forward_producer_source_and_audit_checked=True,process=process,new_original_calls=0)
    save(out/'producer-audit.json',summary);return receipt,files,rawTerrain,summary

def observed_world(files,out):
    review=ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json';assert sha(review)=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1';gate=load(review);assert gate['legal_context_gate_passed']is True and gate['corrected_2945_output']['legal_output_allocation']is True
    assert sha(V2/'receipt.json')=='36372f365f9831045a0dab80f1948f445ceda653992a145a03bc051255813eb8';memory=(V2/'after_real_world6786.memory').read_bytes();assert digest(memory)==SNAP_SHA and len(memory)==111804416
    ranges=[]
    def take(p,n,label):
        assert 0<=p<=p+n<=len(memory);raw=memory[p:p+n];ranges.append(dict(label=label,offset=p,bytes=n,sha256=digest(raw)));return raw
    words=struct.unpack('<31I',take(20544696,124,'worldRc124'));assert 0<words[4]<=words[2]<=512 and words[4]==words[7]<=words[5]
    descriptors=take(words[3],words[4]*36,'tiles36');bounds=take(words[6],words[7]*16,'bounds16');tiles=[]
    for i in range(words[4]):
        cap,p,n=struct.unpack_from('<3I',descriptors,i*36);assert n==256 and n<=cap<=1024;raw=take(p,n*264,f'tile{i}.chunks264');chunks_=[]
        for j in range(n):
            vc,vp,vn=struct.unpack_from('<3I',raw,j*264);assert vn==145 and vn<=vc<=65536;v=take(vp,vn*12,f'tile{i}.chunk{j}.vertices');chunks_.append((tuple(struct.iter_unpack('<3I',v)),struct.unpack_from('<H',raw,j*264+260)[0]))
        tiles.append((tuple(chunks_),struct.unpack_from('<4I',bounds,i*16)))
    actual={'terrain':canonical_terrain(tiles)}
    assert words[14]==0xffffffff and words[23]!=0xffffffff and words[30]&255==0 and words[29]==B(68)
    for name,ci,pi,ni,oi,wi,stride in(('navigation',8,9,10,11,13,1),('secondary',23,24,25,26,28,4)):
        assert 0<words[ni]<=words[ci]and words[ni]==words[wi]**2;actual[name]=take(words[pi],words[ni]*stride,name)
        assert words[wi]==(280 if name=='navigation'else 560)and words[oi:oi+2]==(3323265024,3292610560)
    for name,data in actual.items():assert data==files[name],name
    assert ranges==load(OBS/'source-ranges.json')and digest((OBS/'source-ranges.json').read_bytes())=='ddfbd9aa7c80d54a25446f33955f474feeebaf3305d416cfffd216b7d065ae02'
    assert len(ranges)==2318 and sum(r['bytes']for r in ranges)==5950608
    obs=load(OBS/'comparison.json');assert sha(OBS/'comparison.json')=='1921a6fc5aa6320e389d5ec4b42c7e2c8ebffc9fc119e625c7e66a5ba3fceba8'and obs['original_executions']==obs['new_original_cases']==0
    save(out/'snapshot-range-audit.json',dict(canonical_bytes=sum(map(len,actual.values())),ranges=2318,range_bytes=5950608,all_bytes_exact=True,snapshot_sha256=SNAP_SHA,old_invalid_context_used=False,new_original_calls=0,artifacts={name:digest(value)for name,value in actual.items()}))
    return words

def nearest(c):
    r=c['raster'];width=r['width'];data=r['values_bits'];ox,oy=r['origin_xy_bits'];dx,dy=sub(c['x_bits'],ox),sub(c['y_bits'],oy);cx,cy=math.floor(F(add(dx,dx))),math.floor(F(add(dy,dy)))
    for radius in range(21):
        candidates=[]
        for dy in range(-radius,radius+1):
            for dx in range(-radius,radius+1):
                x,y=cx+dx,cy+dy
                if max(abs(dx),abs(dy))!=radius or not(0<=x<width and 0<=y<width):continue
                index=y*width+x
                if index>=len(data):return dict(id=c['id'],kind='nearest',entry_status='bounds_trap',output16_hex='a5'*16)
                if not math.isnan(F(data[index])):candidates.append((dx*dx+dy*dy,dy,dx,x,y,data[index]))
        if candidates:
            _,_,_,x,y,h=min(candidates);xyz=[add(ox,mul(add(B(x),B(.5)),B(.5))),add(oy,mul(add(B(y),B(.5)),B(.5))),h]
            return dict(id=c['id'],kind='nearest',entry_status='returned',output16_hex=struct.pack('<4I',1,*xyz).hex(),output=dict(found=True,xyz_words=xyz))
    return dict(id=c['id'],kind='nearest',entry_status='returned',output16_hex=struct.pack('<I',0).hex()+'a5'*12,output=dict(found=False,xyz_words=[0xa5a5a5a5]*3))

def query_audit(receipt,files,tiles,out):
    assert sha(RUN/'comparison.json')==PIN;sources,edges=source_guard(RUN,receipt);assert len(sources)==20 and len(edges)==38
    for name,key in(('inputs.json','input_sha256'),('expected.json','expected_sha256'),('actual.jsonl','actual_sha256'),('manifest.json','manifest_sha256')):assert sha(RUN/name)==receipt[key]
    cfg=load(RUN/'config.json');assert cfg['world_rc']==20544696 and cfg['snapshot_sha256']==SNAP_SHA and cfg['input_sha256']==receipt['input_sha256']
    world=M.World.__new__(M.World);world.tiles=tiles;world.fallback=B(68);world.cache={};world.queries=Counter();world.secondary=(tuple(x[0]for x in struct.iter_unpack('<I',files['secondary'])),3323265024,3292610560,560)
    inputs=load(RUN/'inputs.json');expected=load(RUN/'expected.json');actual=[json.loads(x)for x in(RUN/'actual.jsonl').read_text().splitlines()];assert len(inputs)==len(expected)==len(actual)==3368;counts=Counter();allcalls=[]
    for c,e,a in zip(inputs,expected,actual,strict=True):
        assert c['id']==e['id']==a['id'];counts[c['group']]+=1
        if c['kind']=='nearest':
            ref=nearest(c);allcalls.append('nearest_height');counts['nearest']+=1;counts['bounds_abort']+=ref['entry_status']=='bounds_trap';counts['nearest_found']+=ref.get('output',{}).get('found',False)
        else:
            t=world.terrain(c['x_bits'],c['y_bits']);w=world.height(c['x_bits'],c['y_bits']);output={}
            for role,value,missing in(('terrain_height',t,add(c['x_bits'],0xbd8f5c29)),('world_height',w,0)):
                value_bits=value if value is not None else missing;output[role]=dict(found=value is not None,value_bits=value_bits,output16_hex=struct.pack('<II',int(value is not None),value_bits).hex()+'a5'*8);allcalls.append(role)
            ref=dict(id=c['id'],kind='height',entry_status='returned',output=output);counts['height']+=1;counts['terrain_miss']+=t is None;counts['world_miss']+=w is None;counts['secondary_lift']+=t is not None and w is not None and F(w)>F(t)
        assert ref==e,(c['id'],'expected',ref,e);assert ref==a,(c['id'],'actual',ref,a);counts['full16_output_bytes']+=16*(2 if c['kind']=='height'else 1)
    runtime=load(RUN/'runtime.json');assert runtime==receipt['runtime'];assert len(allcalls)==runtime['full_query_calls']==6671 and len(runtime['entry_calls'])==6671
    manifest=load(RUN/'manifest.json');assert runtime['module_sha256']==manifest['module_sha256']and runtime['input_sha256']==receipt['input_sha256']and runtime['range_sha256']==cfg['source_ranges_sha256']
    assert [x['role']for x in runtime['entry_calls']]==allcalls;bad=[(i,x)for i,x in enumerate(runtime['entry_calls'])if not x['returned']];assert len(bad)==1 and bad[0][0]==7 and bad[0][1]['after']==1048448
    for x in runtime['entry_calls']:assert x['before']==1048576 and(x['after']==1048576 if x['returned']else x['after']==1048448)
    assert runtime['fresh_instances']==2 and runtime['host_calls']==0 and runtime['denied_imports']==882 and runtime['bounds_traps']==1 and runtime['stack_guards']==runtime['full_query_calls']+runtime['allocations']==6803
    assert runtime['snapshot_sha256']==SNAP_SHA and runtime['source_sha256']==WASM_SHA and runtime['peak_memory_bytes']==111804416
    assert runtime['world_checks']==[dict(instance=i,ranges=2318,unchanged=True)for i in(1,1,2,2)]
    terminal=load(RUN/'process-terminal.json');assert terminal==receipt['process']and terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<terminal['deadline_seconds']==120
    owned=load(RUN/'owned-process.json');command=owned['command'];assert owned['pid']==owned['pgid']==terminal['pid']and owned['deadline_seconds']==120
    assert command==[str(ROOT/'.toolchain/runtime/node_modules/node/bin/node'),'--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_world_query139_oracle.mjs'),str(RUN),str(RUN/'config.json')]
    assert sha(Path(command[0]))=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
    save(out/'query-audit.json',dict(cases=3368,entries=6671,normal_returns=6670,expected_abort=1,counts=dict(counts),process=terminal,all_expected_and_actual_independently_exact=True,poison16_checked=True,source_closure=20,edges=38,read_only_ranges_rechecked=2318,new_original_calls=0))
    return dict(counts)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path);args=parser.parse_args();out=args.output.resolve();assert out.is_relative_to(ROOT/'evidence');out.mkdir();began=time.monotonic();forbidden=guard_imports()
    assert sha(RUN/'task-handoff.json')==HANDOFF_SHA;handoff=load(RUN/'task-handoff.json');author={}
    for name,row in handoff['files'].items():assert sha(ROOT/name)==row['sha256']and(ROOT/name).stat().st_size==row['bytes'];author[name]=row['sha256']
    for p in(Path(__file__),Path(M.__file__)):q=out/'reviewer-source'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
    cfg,manifest=static_admission(out);model,files,tiles,producer=producer_audit(cfg,out);observed_world(files,out);r=load(RUN/'comparison.json');counts=query_audit(r,files,tiles,out)
    assert not forbidden and all(sha(ROOT/n)==h for n,h in author.items());assert not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    result=dict(status='pass_current139_bounded_raw_world_and_query_projection',author_files=author,author_handoff_sha256=HANDOFF_SHA,author_comparison_sha256=PIN,reviewer_source_sha256=sha(Path(__file__)),independent_math_reference=dict(path=str(Path(M.__file__).relative_to(ROOT)),sha256=M_SHA,current139_whole_WAT_rebound=True,old_runtime_inputs_or_results_read=False),producer=producer,query_counts=counts,canonical_world_bytes=5355768,snapshot_ranges=2318,snapshot_range_bytes=5950608,original_query_attempts_rechecked=6671,normal_returns_rechecked=6670,expected_abort_rechecked=1,new_original_calls=0,author_model_or_driver_executions=0,author_code_exec_audit_forbidden=forbidden,old_invalid_context_accepted=False,elapsed_seconds=time.monotonic()-began,limitations=['Raw9ADT terrain independently reconstructed; nav/secondary full mesh/raster pipeline is not implemented a second time in this review. Their frozen forward producer/source/Python audit and all canonical v2 bytes are checked.','Python audit is not an OS-wide syscall audit.','Only current139 Elwynn no-primary/nonflat world and explicit nearest raster fixtures; no wholeRc/cache/JS/App/worldbootstrap/render/gameplay acceptance.','Panic diagnostic location contents are not compared; controlled abort output and stack contract are checked.','No135/138 passed case is transferred; old mathematical reference is checked against current139 complete WAT.','0 complete game/native/full880 executions.'])
    save(out/'review.json',result);print(json.dumps(dict(directory=str(out.relative_to(ROOT)),review_sha256=sha(out/'review.json'),status=result['status'],cases=3368,original_calls=0,seconds=result['elapsed_seconds'])))
if __name__=='__main__':main()
