#!/usr/bin/env python3
"""Postcapture read-only physical2123 audit; no model/original execution."""
from collections import Counter
from pathlib import Path
import hashlib,json,struct
ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'evidence/player-update139-oracle-20261102T103206.417048Z'
COMP='4c2e613cd691eb84086d08fadb082d84ab57e86497031f90fa5a5e4682b13526'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
u=lambda b,o=0:struct.unpack_from('<I',b,o)[0]


def main():
    assert sha(CASE/'comparison.json')==COMP
    comp=json.loads((CASE/'comparison.json').read_text());expected=json.loads((CASE/'expected.json').read_text());actual=[json.loads(s)for s in(CASE/'actual.jsonl').read_text().splitlines()];assert len(expected)==len(actual)==5
    for n,h in comp['artifacts'].items():assert sha(CASE/n)==h
    for n,h in comp['sources_before'].items():assert sha(ROOT/n)==h
    counts=Counter();frames=[];allowed=set(range(664,688))|set(range(724,736))
    for offset in(1264,1540,1628,1712,1888,2004):allowed.update(range(offset,offset+4))
    assert len(allowed)==60
    for e,a in zip(expected,actual,strict=True):
        assert e['id']==a['id']
        for j,(diag,raw)in enumerate(zip(e['diagnostics'],a['player_stages'],strict=True)):
            before,after=raw['before'],raw['after'];bs=[bytes.fromhex(h)for h in before['live']['storage']];ass=[bytes.fromhex(h)for h in after['live']['storage']]
            assert before['live']['capacity']==after['live']['capacity']==4 and len(bs)==len(ass)==4
            kept=diag['retained_source_indices'];n=before['live']['count'];rows=list(bs)
            assert all(0<=i<n for i in kept)
            for k,i in enumerate(kept):rows[k]=bs[i]
            perception=any(v[0]=='perception'and v[1]==1 for v in diag['events']);written=None
            if perception:
                assert not diag['expired_spells'] and all(not(u(r,20)==20600 and int.from_bytes(r[:8],'little')==0)for r in bs[:n])
                written=len(kept);assert after['live']['count']==len(kept)+1
                assert u(ass[written],8)==8 and u(ass[written],20)==20600 and u(ass[written],28)==0
                counts['perception_append_records']+=1;counts['unknown_written_scratch16_bytes']+=4
            else:assert after['live']['count']==len(kept)
            for k,(want,seen)in enumerate(zip(rows,ass,strict=True)):
                if k==written:continue
                assert want==seen,(e['id'],j,'physical32_copy_or_stale_tail',k);counts['physical_live_bytes_strictly_conserved_or_copied']+=32
            if diag['expired_spells']:
                counts['expiry_frames']+=1
                for k,i in enumerate(kept):assert ass[k]==bs[i];counts['full32_retained_copies']+=1
            if not diag['expiry_sync1173_called']and not perception:
                assert before['aura']==after['aura'];counts['Aura_full_payload_bytes_conserved_without1173']+=768
            bg=before['capture']['background'];assert bg==after['capture']['background']
            counts['background_full_physical_bytes_conserved']+=sum(len(bytes.fromhex(h))for key in('units','pickups','special','windows','boundaries')for h in bg[key]['storage'])
            pre=bytes.fromhex(before['capture']['raw_game2592_hex']);post=bytes.fromhex(after['capture']['raw_game2592_hex']);assert len(pre)==len(post)==2592
            changed=[i for i,(x,y)in enumerate(zip(pre,post))if x!=y];assert set(changed)<=allowed,(e['id'],j,'outside_current_default_write_footprint',changed)
            for i,(x,y)in enumerate(zip(pre,post)):
                if i not in allowed:assert x==y;counts['Game_bytes_conserved_outside60B_footprint']+=1
            assert all(u(post,o)==u(pre,o)for o in(1704,1708,2000,2008))
            frames.append(dict(id=e['id'],stage=j,perception_append=perception,expired_spells=diag['expired_spells'],retained_source_indices=kept,changed_Game_bytes=changed))
    assert counts['perception_append_records']==5 and counts['unknown_written_scratch16_bytes']==20 and counts['expiry_frames']==6
    assert counts['physical_live_bytes_strictly_conserved_or_copied']==19680 and counts['Game_bytes_conserved_outside60B_footprint']==392460
    assert counts['Aura_full_payload_bytes_conserved_without1173']==110592 and counts['background_full_physical_bytes_conserved']==491040
    report=dict(kind='postcapture_readonly_physical_conservation_audit_not_new_original_or_model_execution',comparison_sha256=COMP,actual_sha256=sha(CASE/'actual.jsonl'),expected_diagnostics_sha256=sha(CASE/'expected.json'),script_sha256=sha(Path(__file__)),source_before_hashes_unchanged=True,counts=dict(counts),current_default_Game_possible_write_bytes=sorted(allowed),allocator_addresses_predicted=False,unknown_scratch16_completed=False,frames=frames,limitations=['Uses frozen model retained-index/event diagnostics to crosscheck actual whole32B copy and unchanged staleTail;not a second independent gameplay reference.','60BGamefootprint is scoped to currentquiet/default/fullHP matrix;3setheaders/racialtimer/damage1540/warriortimer/livecount/packetcount/Aurapointer.','All other observed Game bytes and all physical background strictly conserved;this doesnotindependently initialize their values.','1173 allocates new48x16 backing;inactivepayload None not treatedasunchanged acrossactual1173;20byteswrittenfromunknownscratch16remainunknown.'])
    p=CASE/'postcapture-physical-audit.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(path=str(p),sha256=sha(p),counts=dict(counts))))


if __name__=='__main__':main()
