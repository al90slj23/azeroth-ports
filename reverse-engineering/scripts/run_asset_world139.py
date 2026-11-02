#!/usr/bin/env python3
"""Independent139 raw assets -> canonical world, never original/runtime IO."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,struct,sys,time

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'reconstruction')]
from production_closure135 import production_sources135


def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def external(path):
    path=Path(path).resolve()
    if not path.is_relative_to(Path('/Volumes/RuiRui4TB')):raise ValueError('4T input/output required')
    return path


class Assets139:
    def __init__(self,manifest):
        self.manifest=external(manifest);self.manifest_sha256=sha(self.manifest)
        rows=json.loads(self.manifest.read_text());self.assets={};self.loaded={};self.requests=[];self.decoded_bytes=0
        if not isinstance(rows,dict)or not 1<=len(rows)<=1024:raise ValueError('Explicit bounded resource map required')
        for name,row in rows.items():
            if not name.startswith('data/')or name.startswith('data/__index'):continue
            parts=name[5:].replace('\\','/').split('/')
            if any(p in('','.','..')for p in parts):raise ValueError('Asset path components')
            key='\\'.join(parts).encode('utf8')
            if key!=key.lower():raise ValueError('Current resource-map names must be canonical ASCII-lowercase')
            path=external(ROOT.parent/row['file'])
            if path.suffix.lower()in('.memory','.wasm','.wat','.exe','.bin'):
                raise ValueError('Original code/memory/preparsed input is not an asset')
            if row['http_status']!=200 or row['exit_code']!=0 or not 0<=row['bytes']<=16*1024*1024:
                raise ValueError('Successful bounded raw asset required')
            if key in self.assets:raise ValueError('Duplicate canonical asset')
            self.assets[key]=(path,row['bytes'],row['sha256'])
        if len(self.assets)!=453:raise ValueError('This139 raw bundle must declare453 actual assets')

    def __call__(self,name):
        if type(name)is not bytes:raise TypeError('UTF8 asset-name bytes required')
        name.decode('utf8');key=bytes(92 if x==47 else x+32 if 65<=x<=90 else x for x in name)
        self.requests.append(key.decode('utf8'))
        if key not in self.assets:raise KeyError(key)
        if key not in self.loaded:
            path,n,h=self.assets[key]
            if self.decoded_bytes+n>256*1024*1024:raise ValueError('Raw asset256MiB budget')
            value=path.read_bytes()
            if len(value)!=n or hashlib.sha256(value).hexdigest()!=h:raise ValueError('Raw asset identity changed')
            self.loaded[key]=value;self.decoded_bytes+=n
        return self.loaded[key]


def write_world(world,out):
    terrain=bytearray(struct.pack('<I',len(world.tiles)))
    for tile in world.tiles:
        terrain.extend(struct.pack('<5I',*tile.bounds_bits,len(tile.chunks)))
        for chunk in tile.chunks:
            terrain.extend(struct.pack('<HI',chunk.holes,len(chunk.vertices)))
            for vertex in chunk.vertices:terrain.extend(struct.pack('<3I',*vertex))
    files={'terrain':('terrain-query.bin',bytes(terrain)),
        'navigation':('navigation.bin',world.nav.values),
        'secondary':('secondary-height.u32le',b''.join(struct.pack('<I',x)for x in world.secondary.values_bits))}
    artifacts={}
    for name,(filename,data)in files.items():
        p=out/filename;p.write_bytes(data);artifacts[name]=dict(file=filename,bytes=len(data),sha256=sha(p))
    artifacts['navigation'].update(origin_xy_bits=world.nav.origin_xy_bits,width=world.nav.width)
    artifacts['secondary'].update(origin_xy_bits=world.secondary.origin_xy_bits,width=world.secondary.width)
    return artifacts


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--asset-map',required=True,type=Path);p.add_argument('--acquisition-receipt',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    began=time.monotonic();out=external(a.output);out.mkdir(parents=True,exist_ok=False)
    files=tuple(sorted(set(('scripts/run_asset_world139.py','scripts/production_closure135.py')+
        production_sources135(ROOT,'resource_spec.world139'))))
    before={n:sha(ROOT/n)for n in files}
    for n,h in before.items():
        q=out/'source-snapshot'/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/n).read_bytes());assert sha(q)==h
    provider=Assets139(a.asset_map)
    acquisition=external(a.acquisition_receipt);acquisition_sha=sha(acquisition);record=json.loads(acquisition.read_text())
    if record['version']!='0.139.0'or record['stamp']!='f339dd20e0fe'or record['resource_map_sha256']!=provider.manifest_sha256 or record['old_resource_bytes_reused']is not False:
        raise ValueError('Coherent fresh139 asset acquisition receipt required')
    allowed_assets={value[0]for value in provider.assets.values()};allowed_sources={(ROOT/n).resolve()for n in files}
    allowed_cache={(x.parent/'__pycache__')for x in allowed_sources};audit=[];forbidden=[]
    def hook(event,args):
        if event!='open'or not isinstance(args[0],(str,bytes,os.PathLike)):return
        path=Path(os.fsdecode(args[0])).resolve();mode=args[1];flags=args[2]
        reading=(isinstance(mode,str)and'r'in mode)or(mode is None and isinstance(flags,int)and flags&3==os.O_RDONLY)
        if not reading:return
        if path.is_relative_to(ROOT):
            admitted=path in allowed_assets or path in allowed_sources or path in(provider.manifest,acquisition)or path.is_relative_to(out)or(path.suffix=='.pyc'and path.parent in allowed_cache)
            audit.append(dict(path=str(path),allowed=admitted))
            if not admitted:forbidden.append(str(path));raise RuntimeError('Independent world read outside declared inputs: '+str(path))
        if path.suffix.lower()in('.memory','.wasm','.wat','.exe'):
            forbidden.append(str(path));raise RuntimeError('Original input denied')
    sys.addaudithook(hook)
    from resource_spec.world139 import build_world139,CENTER139,FALLBACK139,RADIUS139
    progress=[]
    def tick(value):progress.append(value)
    built=build_world139(provider,progress=tick);world=built.world
    assert world.primary is None and world.secondary is not None and world.nav is not None and world.flat_height_bits is None
    artifacts=write_world(world,out)
    loaded_after={name.decode():sha(provider.assets[name][0])for name in provider.loaded}
    after={n:sha(ROOT/n)for n in files};assert before==after and not forbidden
    assert sha(provider.manifest)==provider.manifest_sha256 and sha(acquisition)==acquisition_sha
    assert all(loaded_after[n.decode()]==provider.assets[n][2]for n in provider.loaded)
    save(out/'python-open-audit.json',dict(kind='Python_audit_hook_not_OS_syscall_audit',events=audit,forbidden=forbidden))
    save(out/'progress.json',progress)
    receipt=dict(kind='independent139_raw_assets_to_canonical_world',version='0.139.0',actual_build='f79c5e2b4',
        asset_map=str(provider.manifest),asset_map_sha256=provider.manifest_sha256,declared_assets=len(provider.assets),loaded_assets=len(provider.loaded),raw_asset_bytes=provider.decoded_bytes,
        asset_acquisition_receipt=str(acquisition),asset_acquisition_receipt_sha256=acquisition_sha,
        asset_requests=provider.requests,loaded_asset_sha256_after=loaded_after,assets_unchanged=True,source_sha256_before=before,source_sha256_after=after,
        source_files=len(files),world_artifacts=artifacts,query_scalars=dict(center_xy_bits=CENTER139,radius_bits=RADIUS139,fallback_height_bits=FALLBACK139,primary_present=False,flat_present=False),
        geometry_stats=built.stats,selected_counts={k:len(v)for k,v in built.selected.items()},
        python_read_audit=str(out/'python-open-audit.json'),python_read_audit_sha256=sha(out/'python-open-audit.json'),
        original_program_executed=False,original_memory_read=False,preparsed_world_input_read=False,original_queries_executed=0,old_acceptance_transferred=False,
        elapsed_seconds=time.monotonic()-began,limitations=['Elwynn no-primary nonflat path only.','Pure resource algorithms with legacy135 names are shared;139 acceptance requires separate139 comparison.','Python audit hook and frozen source/provider evidence,not an OS-wide syscall proof.','WorldRc heap/cache ownership,other maps,App/opening/render/gameplay are not implemented by this producer.'])
    save(out/'receipt.json',receipt)
    print(json.dumps(dict(directory=str(out),receipt_sha256=sha(out/'receipt.json'),loaded_assets=len(provider.loaded),raw_asset_bytes=provider.decoded_bytes,world_artifacts=artifacts,original_calls=0)),flush=True)


if __name__=='__main__':main()
