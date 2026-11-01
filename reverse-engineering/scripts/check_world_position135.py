#!/usr/bin/env python3
"""Expected-first full8751/13516 differential over explicit world inputs."""
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import argparse, json, os, signal, struct, subprocess, sys, time
from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA
from build_upgrade134_oracle import sha
from build_world_snapshot135_oracle import build_snapshot135
from source_closure135 import core_sources

sys.dont_write_bytecode = True
FILES = tuple(dict.fromkeys(('scripts/check_world_position135.py', 'scripts/run_world_position135_oracle.mjs',
    'scripts/build_world_snapshot135_oracle.py', 'scripts/world_snapshot135_host.mjs',
    'scripts/build_full135_oracle.py', 'scripts/build_upgrade134_oracle.py', 'scripts/source_closure135.py',
    'reconstruction/resource_spec/__init__.py', 'reconstruction/resource_spec/world_query135.py',
    'reconstruction/resource_spec/terrain135.py', 'reconstruction/resource_spec/entry_resources135.py',
    'reconstruction/resource_spec/dbc.py') + core_sources(ROOT, 'world_position135.py', 'initial_state135.py')))
IMPORTED = {n: sha(ROOT/n) for n in FILES}
sys.path.insert(0, str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.world_position135 import (WorldPositionInput135, DistanceMap135,
    sample_spawn_position, sample_random_position)
from core_spec.spawn_position135_data import ZONE_GEOMETRY
from core_spec.initial_state135 import seed_rng_words
from resource_spec.world_query135 import WorldQueries135, NavGrid135, decode_world_snapshot
from resource_spec.terrain135 import HeightRaster135

SNAPSHOT = ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/after_real_world6730.memory'
SNAPSHOT_SHA = 'f651042520491d22e9910b1c01b34eaf90c73e004a4cd60ce310428186d9291a'
G, WORLD = 14554176, 26204808
NODE = ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
INPUT_KEYS = ('id','group','kind','input','world')


def controlled_world(raw):
    def raster(value):
        return None if value is None else HeightRaster135(tuple(value['values_bits']), tuple(value['origin_xy_bits']), value['width'])
    nav = raw['nav']
    nav = None if nav is None else NavGrid135(bytes.fromhex(nav['values_hex']), tuple(nav['origin_xy_bits']), nav['width'])
    return WorldQueries135((), raster(raw['primary']), raster(raw['secondary']), nav,
        raw['fallback_height_bits'], raw['flat_height_bits'])


def input_state(raw):
    value = dict(raw)
    for name in ('player_xyz','velocity_xy','rng_words'): value[name] = tuple(value[name])
    path = value['distance_map']
    value['distance_map'] = None if path is None else DistanceMap135(tuple(path['values_u16']), path['field24'])
    return WorldPositionInput135(**value)


def corpus(world, pilot):
    rows = []
    cx, cy, _ = ZONE_GEOMETRY[0]
    player = (cx,cy,world.height(cx,cy).value_bits)
    def add(group, kind='spawn', *, description=None, seed=1, xyz=player, velocity=(0,0),
            low=26, high=36, bias=.5, distance_map=None):
        state = WorldPositionInput135(0,xyz,velocity,f.from_float(low),f.from_float(high),f.from_float(bias),seed_rng_words(seed),distance_map)
        geometry = world if description is None else controlled_world(description)
        result = (sample_spawn_position if kind=='spawn' else sample_random_position)(state,geometry)
        rows.append(dict(id=len(rows),group=group,kind=kind,input=asdict(state),world=description,
            expected=dict(position_bits=result.position_bits,rng_words=result.rng_words),diagnostic=asdict(result)))
    add('real-world-still')
    add('real-world-random','random',low=18,high=50)
    if pilot:return json.loads(json.dumps(rows))
    for seed in (0,2,3,7,31,255,65535,0x123456789abcdef):
        add('real-world-still',seed=seed)
        add('real-world-random','random',seed=seed,low=18,high=50)
        for vx,vy in ((7,0),(-5,4),(3,-8)):
            add('real-world-moving-bias',seed=seed,velocity=(f.from_float(vx),f.from_float(vy)))
    for dx,dy in ((-110,0),(110,0),(0,-100),(0,110)):
        x,y=f.add(cx,f.from_float(dx)),f.add(cy,f.from_float(dy));h=world.height(x,y)
        if h.found:
            for seed in (0,17):
                add('real-world-edge-retry',seed=seed,xyz=(x,y,h.value_bits))
                add('real-world-edge-random','random',seed=seed,xyz=(x,y,h.value_bits),low=18,high=50)
    def flat(navbyte=None,width=80):
        nav = None if navbyte is None else dict(values_hex=bytes([navbyte]*(width*width)).hex(),
            origin_xy_bits=(f.add(cx,f.from_float(-40)),f.add(cy,f.from_float(-40))),width=width)
        return dict(nav=nav,primary=None,secondary=None,fallback_height_bits=f.from_float(99),flat_height_bits=0)
    for byte in (None,0,1,2,255):
        desc=flat(byte)
        for kind in ('spawn','random'):
            add('controlled-nav-byte',kind,description=desc,xyz=(cx,cy,0),seed=1)
        if byte is not None:
            for field in (400,401):
                for cost in (0,65535,500):
                    add('controlled-distance-map',description=desc,xyz=(cx,cy,0),seed=3,
                        distance_map=DistanceMap135((cost,)*(80*80),field))
    for kind in ('spawn','random'):
        add('low-radius-fallback',kind,description=flat(1),xyz=(cx,cy,0),low=3,high=8)
    # 13th13516 trial must retain random XY when nearest23181 supplies only Z.
    # All-zero words are a valid degenerate state; create the fixture directly.
    for with_nearest in (False,True):
        desc=flat(1)
        primary=dict(width=9,origin_xy_bits=(f.add(cx,f.from_float(25)),f.add(cy,f.from_float(-2))),values_bits=[0x7fc00000]*81)
        if with_nearest:primary['values_bits'][4*9+3]=f.from_float(77)
        desc.update(flat_height_bits=None,primary=primary)
        state=WorldPositionInput135(0,(cx,cy,0),(0,0),f.from_float(26),f.from_float(36),f.from_float(.5),(0,0,0,0))
        result=sample_random_position(state,controlled_world(desc))
        rows.append(dict(id=len(rows),group='controlled-nearest-only-z'if with_nearest else'controlled-world-fallback-z',kind='random',
            input=asdict(state),world=desc,expected=dict(position_bits=result.position_bits,rng_words=result.rng_words),diagnostic=asdict(result)))
    return json.loads(json.dumps(rows))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args()
    before={n:sha(ROOT/n)for n in FILES};assert before==IMPORTED
    assert sha(SNAPSHOT)==SNAPSHOT_SHA and sha(NODE)==NODE_SHA
    geometry=decode_world_snapshot(SNAPSHOT.read_bytes(),WORLD)
    rows=corpus(geometry,args.phase=='pilot')
    out,manifest=build_snapshot135(['spawn_position','random_position'])
    fixture=out/'world-position135-fixtures.json';fixture.write_text(json.dumps(rows,separators=(',',':'))+'\n')
    inputs=out/'world-position135-inputs.json';inputs.write_text(json.dumps([{k:c[k]for k in INPUT_KEYS}for c in rows],separators=(',',':'))+'\n')
    config=out/'world-position135-config.json';config.write_text(json.dumps(dict(snapshot_path=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,
        game_pointer=G,world_pointer=WORLD,input_path=str(inputs),input_sha256=sha(inputs)))+'\n')
    for name,h in before.items():
        p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
    frozen={p.name:sha(p)for p in(fixture,inputs,config,out/'manifest.json',out/manifest['module_file'])}
    command=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_world_position135_oracle.mjs'),str(out),str(config)]
    results=out/'world-position135-results.jsonl';stderr=out/'world-position135-stderr.log';start=time.monotonic()
    with results.open('w')as stdout,stderr.open('w')as err:
        child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError(f'Owned60s timeout:{out}')
    actual=[json.loads(line)for line in results.read_text().splitlines()]
    failures=[]
    for c,a in zip(rows,actual):
        assert c['id']==a['id']
        if c['expected']!=a['projection']:failures.append(dict(id=c['id'],group=c['group'],expected=c['expected'],actual=a['projection']))
    assert code==0 and len(actual)==len(rows),(code,out)
    mismatch=out/'world-position135-mismatches.json';mismatch.write_text(json.dumps(failures,indent=2)+'\n')
    assert before=={n:sha(ROOT/n)for n in FILES}
    assert frozen=={p.name:sha(p)for p in(fixture,inputs,config,out/'manifest.json',out/manifest['module_file'])}
    runtime=out/'world-position135-runtime.json'
    receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(rows),differences=len(failures),
        groups=dict(Counter(c['group']for c in rows)),source_sha256_before=before,source_sha256_after=before,
        snapshot_sha256=SNAPSHOT_SHA,snapshot_bytes=SNAPSHOT.stat().st_size,original_sha256=SOURCE_SHA,
        expected_before_original=True,input_contains_expected=False,input_exact_keys=list(INPUT_KEYS),
        artifacts={p.name:sha(p)for p in(fixture,inputs,config,results,stderr,mismatch,runtime,out/'manifest.json',out/manifest['module_file'])},
        runtime=json.loads(runtime.read_text()),process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,deadline_seconds=60),
        limitations=['Snapshot-derived explicit world input,not independently producedworld or anewbootstrap.',
            'Full8751/13516 XYZ/RNG andall2592G mutation domain compared;only declared fixture setup patches precede original.',
            'Controlled geometry/path inputs are component fixtures,not naturally observedworldstates.',
            'Finite positions/ranges and existing trig domain;malformedgrid/path bounds traps remain separate.',
            'No entities,full1089/880/saves/UI/multiplayer or independentcompletegame acceptance.'])
    target=out/'world-position135-comparison.json';target.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),receipt_sha256=sha(target),cases=len(rows),differences=len(failures),first_failures=failures[:5])))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
