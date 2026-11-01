#!/usr/bin/env python3
"""Private full921 fixture; preserve original code, add read-only stack export."""
import hashlib,json,sqlite3
from build_distance_map135_oracle import build_distance_map135
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA

def sha(p):
 with p.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def build_demo_ai135():
 out,manifest=build_distance_map135();original=SOURCE.read_bytes();assert hashlib.sha256(original).hexdigest()==SOURCE_SHA
 profile=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z';static=[]
 with sqlite3.connect((profile/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(profile/'official-0.135.1-full.wat').open('rb')as wat:
  db.execute('pragma query_only=on');db.row_factory=sqlite3.Row
  for index in(921,4543,15511,13814,1073,27375):
   row=dict(db.execute('select * from functions where idx=?',(index,)).fetchone());assert row['wat_end']-row['wat_start']<=524288;wat.seek(row['wat_start']);text=wat.read(row['wat_end']-row['wat_start']);(out/f'demo-ai-{index}.wat').write_bytes(text);row.update(wat_sha256=hashlib.sha256(text).hexdigest(),body_sha256=hashlib.sha256(original[row['body_start']:row['body_end']]).hexdigest());static.append(row)
 manifest.update(actual_build='90898d5e3',historical_build_alias='0898d5e3',demo_ai_static_functions=static,private_role_scope='Complete921, original1073 contact consumer and late4543; all callees unchanged',full_WAT_read=False)
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return out,manifest
if __name__=='__main__':
 out,m=build_demo_ai135();print(json.dumps(dict(directory=str(out),module_sha256=m['module_sha256'])))
