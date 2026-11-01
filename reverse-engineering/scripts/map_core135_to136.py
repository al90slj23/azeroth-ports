#!/usr/bin/env python3
"""Bounded static135->136 core correspondence; never execute either target.

Exact body+signature matches take priority. Normalized WAT matches are only
structural candidates: function/call indices and declared static data addresses
can move during compilation. They do not transfer old behavior acceptance.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import re
import sqlite3
import sys
import time

sys.dont_write_bytecode = True
from wasm135_profile import Reader
from wasm_index import body_ranges

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
NEW = ROOT / 'originals/official-acquisition-20261101T142725.754244Z/latest-wenilla_bg.wasm'
OLD_SHA = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
NEW_SHA = '48c3bce7d690b3be02973bde89903c385e21ef16deca23539dcef60a1eb2eef3'
OLD_PROFILE = ROOT / 'evidence/wasm0135-profile-20261101T031028.877964Z'
TARGETS = ((1560,'constructor'), (1089,'opening'), (6730,'cached_world_construct'),
    (880,'application_tick'), (922,'cast'), (1076,'owned_tick'), (914,'damage'),
    (921,'unit_tick'), (947,'spawn_tick'), (2376,'special_tick'),
    (2922,'account_companion_selection'), (91941,'allocator'))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def load(path, expected, defined):
    raw = path.read_bytes(); assert hashlib.sha256(raw).hexdigest() == expected
    top = Reader(raw,8); sections = {}
    while top.pos < top.end:
        kind,size = top.byte(),top.uint(); sections[kind]=(top.pos,top.pos+size);top.raw(size)
    t = Reader(raw,*sections[1]); types=[]
    for _ in range(t.uint()):
        assert t.byte()==0x60; types.append((t.raw(t.uint()),t.raw(t.uint())))
    t.finish(); t=Reader(raw,*sections[2]); imports=[]
    for _ in range(t.uint()):
        t.name();t.name();assert t.byte()==0;imports.append(t.uint())
    t.finish();t=Reader(raw,*sections[3]);decl=[t.uint() for _ in range(t.uint())];t.finish()
    ranges=body_ranges(raw);assert len(imports)==878 and len(decl)==len(ranges)==defined
    address_ranges=[];t=Reader(raw,*sections[11])
    for _ in range(t.uint()):
        flags=t.uint(); assert flags in (0,1,2); address=None
        if flags != 1:
            if flags==2:t.uint()
            assert t.byte()==0x41;address=t.sint()&0xffffffff;assert t.byte()==0x0b
        size=t.uint();t.raw(size)
        if address is not None:address_ranges.append((address,address+size))
    t.finish()
    # This is an explicitly documented broad static-address envelope. A
    # normalized candidate is not evidence that any changed immediate is safe.
    static_bounds=(min(a for a,b in address_ranges),max(b for a,b in address_ranges))
    signatures={i:types[decl[i-len(imports)]] for i in ranges}
    hashes={i:hashlib.sha256(raw[a:b]).hexdigest() for i,(a,b,n) in ranges.items()}
    return dict(raw=raw,types=types,ranges=ranges,signatures=signatures,hashes=hashes,
                static_bounds=static_bounds)


def normalize(source, model, static_addresses=False):
    lines=[];lo,hi=model['static_bounds']
    def address(value):return lo<=value<hi
    for raw in source.splitlines():
        line=raw.strip()
        line=re.sub(r'^\(func \(;\d+;\) \(type \d+\)', '(func (type SIGNATURE)',line)
        line=re.sub(r'^(call|return_call) \d+(\)*)$',r'\1 CALLEE\2',line)
        def type_index(match):
            a,b=model['types'][int(match[1])]
            return '(type '+a.hex()+'->'+b.hex()+')'
        line=re.sub(r'\(type (\d+)\)',type_index,line)
        if static_addresses:
            m=re.fullmatch(r'i32.const (-?\d+)(\)*)',line)
            if m and address(int(m[1])&0xffffffff):line='i32.const STATIC_ADDRESS'+m[2]
            m=re.fullmatch(r'i64.const (-?\d+)(\)*)',line)
            if m:
                value=int(m[1])&((1<<64)-1);low=value&0xffffffff;high=value>>32
                if address(low) or address(high):
                    line='i64.const '+('STATIC' if address(high) else str(high))+':'+('STATIC' if address(low) else str(low))+m[2]
            line=re.sub(r'offset=(\d+)',lambda m:'offset=STATIC_ADDRESS' if address(int(m[1])) else m[0],line)
        lines.append(line)
    return '\n'.join(lines)


def profile(directory, expected):
    directory=directory.resolve(); manifest=json.loads((directory/'manifest.json').read_text())
    assert manifest['original_sha256']==expected and manifest['identities_preserved'] is True
    wat=Path(manifest['wat_path']);assert sha(wat)==manifest['wat_sha256']
    database=directory/'index.sqlite';assert sha(database)==manifest['database_sha256']
    con=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
    return manifest,wat,con


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--new-profile',type=Path,required=True)
    p.add_argument('--deadline-seconds',type=int,default=180);args=p.parse_args()
    assert 10<=args.deadline_seconds<=300
    began=time.monotonic();deadline=began+args.deadline_seconds
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('core0135-to0136-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    files=(Path(__file__).resolve(),ROOT/'scripts/wasm135_profile.py',ROOT/'scripts/wasm_index.py')
    before={str(path.relative_to(ROOT)):sha(path) for path in files}
    (out/'run-state.json').write_text(json.dumps(dict(status='running',deadline_seconds=args.deadline_seconds,
        target_executed=False))+'\n')
    old=load(OLD,OLD_SHA,175317);new=load(NEW,NEW_SHA,175319)
    om,ow,oc=profile(OLD_PROFILE,OLD_SHA);nm,nw,nc=profile(args.new_profile,NEW_SHA)
    lookup=defaultdict(list)
    for index in new['ranges']:lookup[(new['signatures'][index],new['hashes'][index])].append(index)
    new_locations={row['idx']:dict(row)for row in nc.execute('select *from functions')}
    result=[]; normalizations={}
    with ow.open('rb') as oldstream,nw.open('rb') as newstream:
        for old_index,role in TARGETS:
            if time.monotonic()>deadline:raise TimeoutError('Static migration deadline exceeded')
            row=dict(oc.execute('select *from functions where idx=?',(old_index,)).fetchone())
            assert (row['body_start'],row['body_end'],row['body_bytes'])==old['ranges'][old_index]
            oldstream.seek(row['wat_start']);source=oldstream.read(row['wat_end']-row['wat_start']).decode()
            (out/f'135-{old_index}.wat').write_text(source)
            sig=old['signatures'][old_index];digest=old['hashes'][old_index]
            exact=lookup[(sig,digest)];call_matches=[];static_matches=[]
            size=old['ranges'][old_index][2]
            candidates=[i for i,(_,_,n)in new['ranges'].items()
                if new['signatures'][i]==sig and max(1,size*7//10)<=n<=size*13//10]
            if len(candidates)>8192:raise ValueError('Explicit structural candidate budget exceeded')
            wanted_calls=normalize(source,old);wanted_static=normalize(source,old,True)
            # Counts of consecutive normalized instruction triples retain
            # ordered local context and support a bounded diagnostic shortlist.
            want_lines=wanted_static.splitlines();want_grams=Counter(zip(want_lines,want_lines[1:],want_lines[2:]))
            shortlist=[]
            for index in candidates:
                if time.monotonic()>deadline:raise TimeoutError('Static candidate scan deadline exceeded')
                loc=new_locations[index];newstream.seek(loc['wat_start'])
                candidate=newstream.read(loc['wat_end']-loc['wat_start']).decode()
                normalized_calls=normalize(candidate,new)
                normalized_static=normalize(candidate,new,True)
                if normalized_calls==wanted_calls:call_matches.append(index)
                if normalized_static==wanted_static:static_matches.append(index)
                lines=normalized_static.splitlines();grams=Counter(zip(lines,lines[1:],lines[2:]))
                overlap=sum((want_grams&grams).values());denominator=sum(want_grams.values())+sum(grams.values())
                similarity=2*overlap/denominator if denominator else 1
                shortlist.append((similarity,index))
            shortlist.sort(reverse=True)
            chosen=exact or call_matches or static_matches
            method='exact_body_and_signature' if exact else 'calls_normalized_wat' if call_matches else 'calls_static_addresses_normalized_wat' if static_matches else 'diagnostic_similarity_only'
            recorded=chosen if chosen else [index for score,index in shortlist[:3]]
            for index in recorded:
                loc=new_locations[index];newstream.seek(loc['wat_start'])
                (out/f'136-{index}.wat').write_bytes(newstream.read(loc['wat_end']-loc['wat_start']))
            result.append(dict(role=role,old_index=old_index,old_body_sha256=digest,
                old_body_bytes=size,signature=dict(parameters_hex=sig[0].hex(),results_hex=sig[1].hex()),
                exact_candidates=exact,calls_normalized_candidates=call_matches,
                calls_static_normalized_candidates=static_matches,structural_scan_candidates=len(candidates),
                selected_candidates=chosen,match_method=method,ambiguous=len(chosen)>1,
                semantic_acceptance_transferred=False,
                candidates=[dict(new_index=index,new_body_sha256=new['hashes'][index],
                    new_body_bytes=new['ranges'][index][2],wat_location=new_locations[index])for index in recorded],
                diagnostic_top3=[dict(new_index=index,ordered_trigram_similarity=score)for score,index in shortlist[:3]]))
            print(json.dumps(dict(old_index=old_index,role=role,method=method,candidates=chosen,
                diagnostic_top3=[index for score,index in shortlist[:3]])),flush=True)
    oc.close();nc.close()
    after={str(path.relative_to(ROOT)):sha(path)for path in files};assert before==after
    assert sha(OLD)==OLD_SHA and sha(NEW)==NEW_SHA
    report=dict(kind='static_core135_to136_correspondence_not_new_acceptance',
        old_version='0.135.1',old_build='0898d5e3',old_sha256=OLD_SHA,new_version='0.136.0',new_build='fe24fb74c',new_sha256=NEW_SHA,
        old_profile=str(OLD_PROFILE),new_profile=str(args.new_profile.resolve()),
        old_profile_manifest_sha256=sha(OLD_PROFILE/'manifest.json'),new_profile_manifest_sha256=sha(args.new_profile/'manifest.json'),
        entries=result,source_sha256_before=before,source_sha256_after=after,
        normalization=dict(header='Erase function/type identity; retain full parameter/result/local declarations.',
            calls='Erase direct call/return_call indices; call_indirect type resolved to signature.',
            static='Erase i32/i64 immediate halves and memory offsets inside the explicit data-segment envelope only.',
            old_static_address_envelope=list(old['static_bounds']),new_static_address_envelope=list(new['static_bounds']),
            other_operands='Retain field offsets outside data envelope, float literals, small constants, op order, branches and locals.'),
        target_executed=False,new_original_calls=0,new_original_cases=0,old_acceptance_transferred=False,
        elapsed_seconds=time.monotonic()-began,limitations=[
            'A unique normalized structure is a migration candidate, not proof that new referenced data/callees are semantically equivalent.',
            'Raw body SHA differences alone do not show a gameplay rule change.',
            'Normalized address envelope can include nonaddress integers; every changed immediate requires separate review.',
            'Similarity-only matches stay diagnostic; no unique binding or behavior claim follows from a high score.',
            'All old135 fixtures/builders/evidence remain fixed;136 needs distinct source guards, declarations and future controlled tests.'])
    target=out/'mapping.json';target.write_text(json.dumps(report,indent=2)+'\n')
    (out/'run-state.json').write_text(json.dumps(dict(status='complete',elapsed_seconds=report['elapsed_seconds'],target_executed=False))+'\n')
    print(json.dumps(dict(directory=str(out),mapping_sha256=sha(target),entries=len(result),target_executed=False)))


if __name__=='__main__':main()
