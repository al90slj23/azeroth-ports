#!/usr/bin/env python3
"""Bounded static proof of shared416 correction production/acknowledgement."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sqlite3

ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
SOURCE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb')as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    before=sha(Path(__file__));assert sha(SOURCE)==SOURCE_SHA
    con=sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro',uri=True);con.row_factory=sqlite3.Row
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('player-correction135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    functions={}
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as wat,SOURCE.open('rb')as wasm:
        for index in(968,2328,915):
            row=dict(con.execute('select * from functions where idx=?',(index,)).fetchone())
            wat.seek(row['wat_start']);text=wat.read(row['wat_end']-row['wat_start']);lines=text.decode().splitlines()
            assert lines[0].startswith(f'  (func (;{index};)')
            wasm.seek(row['body_start']);body=wasm.read(row['body_end']-row['body_start'])
            (out/f'{index}.wat').write_bytes(text)
            windows={}
            for label,a,b in {968:(('packed_guid_prefix',179,215),('guid_end_to_ack',481,517),('sequence_u32',9087,9156),('remote_ack',9544,9562),('local_ack',9643,9661)),
                2328:(('pending_gate',18,68),('pending_produced',2425,2550)),
                915:(('relocate_pending_store',1080,1174),)}[index]:
                windows[label]=[dict(line=j+1,instruction=lines[j].strip())for j in range(a,b)]
            direct=[]
            for j,line in enumerate(lines):
                instruction=line.strip()
                if instruction.endswith('offset=416')or instruction.endswith('offset=432')or instruction.endswith('offset=436'):
                    direct.append(dict(line=j+1,instruction=instruction))
            functions[str(index)]=dict(**row,wat_sha256=hashlib.sha256(text).hexdigest(),body_sha256=hashlib.sha256(body).hexdigest(),windows=windows,direct_correction_accesses=direct)
    assert all('load offset=416'not in x['instruction']for x in functions['915']['direct_correction_accesses'])
    proof=dict(version='0.135.1',build='90898d5e3',original_wasm_sha256=SOURCE_SHA,source_sha256=before,
        original_executed=False,sqlite_mode='ro',profile_full_scan=False,functions=functions,
        rules=dict(ack_opcode=199,ack_prefix='packedGUID consumed;default local route does not compare it to playerGUID in the acknowledged-state segment',
            ack_body='u32LE sequence immediately after packedGUID;remainingbody not used by this clear segment',
            ack_clear='if G416==1 and u32(ackSequence)>=u32(G432):storeG416=0',
            ack_remote='Same predicate after2080 player swap;full17726 andswapback remain separate mode/owner effects',
            movement_clear='If G416!=0 and !(distanceSquaredXY>9 and GameNow-G436<3),storeG416=0 before normal movement checks',
            movement_retains='If pending distanceSquared>9 and GameNow-G436<3,return0 without stateclear or position update',
            effect915='Only stores416=1 in delayedtag36 player relocation;does not testorclear416;empty915hasno416guard',
            produced_payload='G420/424/428=correctedXYZ,G432=oldActionSequence,G436=GameNow;both2328 and915 send199',
            inactive='1560 initializes only416tag0;420..436inactivepayload remainsunknown unless actualproducer writes it'),
        not_proved=['No new full199 dynamicdifferential','No complete rawinput producer ornaturalApp acceptance',
            'No permission todeleteheadlessguard without preservingmotionowner andnewwholechain verification',
            'No evidence that every915 delayed/effectfamilyisreconstructed'])
    path=out/'proof.json';path.write_text(json.dumps(proof,indent=2)+'\n');assert sha(Path(__file__))==before
    print(json.dumps(dict(directory=str(out),proof_sha256=sha(path),original_executed=False)))


if __name__=='__main__':main()
