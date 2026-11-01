#!/usr/bin/env python3
"""Static byte-backed six-racial922 source/callback and unwritten-field trace."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,sqlite3
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'


def main():
 raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
 db=sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro',uri=True);out=ROOT/'evidence'/('racial-cast135-trace-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'));out.mkdir();rows=[]
 with(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
  for idx in(922,1512,1202,29983,44446,4600):
   a,b,begin,end=db.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(idx,)).fetchone();wat.seek(a);text=wat.read(b-a);(out/f'{idx}.wat').write_bytes(text)
   rows.append(dict(function=idx,wat_start=a,wat_end=b,body_start=begin,body_end=end,body_sha256=hashlib.sha256(raw[begin:end]).hexdigest(),wat_sha256=hashlib.sha256(text).hexdigest(),header=text.splitlines()[0].decode()))
 proof=dict(original_sha256=SOURCE_SHA,original_executed=False,functions=rows,
  rules=['922 passes realG1256 80B racial record through its execution-kind9 branch; direct cast does not inspect or reset remaining cooldown.',
   'Effect8/9 first requires27562 query to find a valid enemy within30. Value=owned76*definition4; duration=maxNumeric(.1,((definition68*1.4)*owned28)*owned68).',
   'Effect8/9: cast message, remove same-spell ownerGUID0 records stably, append live32B, actual1512, actual1202. Other owners remain.',
   'Effect7: any same-spell live record blocks including expired/nonzero-owner; otherwise shield update, message, append,1202 without1512.',
   'Effect12: require currentHP<=.35*maximumHP and no active kind12. Append without deleting expired same-spell entries;1202 without1512.',
   'busy488 or context908&1 gates only third attempt ledgerG732/G736. First two ledgersG672/G676 andG684/G688 still append and cast itself proceeds.'],
  unwritten_words={'922 new kind7/8/9 live+16':'Copied from unwritten stack scratch. Canonical zero in independent record with explicit unspecified offset16; never silently treated as original zero.',
   '922 new kind12 live+12/+16':'Both copied from definition4/8 and explicitly zero for these two racials.',
   '4600 spell1020 live+12/+16':'Both remain unwritten. Owner0,kind12,spell1020,expiry now+1,trailing28=0 are explicit. Inactive type12 magnitude words must not be interpreted.'},
  pending=['1202 aura/display keyed fields and serialized messages','World callback producers and non-six-racial execution/effect branches','Full constructor/start and8157/1076 scheduling are separate research scopes'])
 (out/'trace.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'directory':str(out),'functions':len(rows),'original_executed':False}))


if __name__=='__main__':main()
