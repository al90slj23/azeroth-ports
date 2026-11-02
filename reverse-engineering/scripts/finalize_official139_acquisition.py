#!/usr/bin/env python3
"""Complete139 acquisition after bounded HTTP gzip negotiation; never execute.

The failed uncompressed60s receipt/partial stay immutable. The successful
HTTP200 --compressed transfer is verified, named canonically, and paired with
fresh after-manifest/HTML checks. No existing package/save/fixed input changes.
"""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,re,sys
from acquire_official_snapshot import download,official_url
ROOT=Path(__file__).resolve().parents[1]
VERSION='0.139.0';STAMP='f339dd20e0fe'
EXE_SHA='0e8e314df4d78ab211b1bef5c48d78d713ed64260894af342f998d298d74d274'
WASM_SHA='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
FAILED_SHA='975c5b3d72ac55f617f3bd7390d943212d62b0a12e6bdbeb66847fa3019360e1'
def sha(p):
 with p.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def load(p):return json.loads(p.read_text())
def stamp(p):
 m=re.search(r'''(?:src|href)=["']([^"']*rogue\.js\?v=([^"'&]+))''',p.read_text());assert m;return m[2]
def main():
 assert len(sys.argv)==2;directory=Path(sys.argv[1]).resolve();assert directory.is_relative_to((ROOT/'originals').resolve())and str(directory).startswith('/Volumes/RuiRui4TB/')
 assert sha(directory/'release-acquisition.json')==FAILED_SHA
 assert not(directory/'release-acquisition-resumed.json').exists()
 producer=(Path(__file__).resolve(),ROOT/'scripts/acquire_official_snapshot.py');before={str(p.relative_to(ROOT)):sha(p)for p in producer}
 snapshot=directory/'resume-source-snapshot';snapshot.mkdir(exist_ok=False)
 for p in producer:(snapshot/p.name).write_bytes(p.read_bytes())
 result=dict(kind='frozen_official139_acquisition_resumed_with_standard_HTTP_gzip',expected_version=VERSION,consumed_build=None,
  started_at_utc=datetime.now(timezone.utc).isoformat(),prior_failed_receipt_sha256=FAILED_SHA,
  prior_failed_receipt_preserved=True,source_sha256_before=before,target_executed=False,wasm_instantiated=False,
  user_saves_accessed=False,installed_packages_replaced=False,fixed_inputs_replaced=False)
 try:
  native=load(directory/'windows-acquisition.json');manifest=load(directory/'windows-latest.json')
  assert native['version']==manifest['version']==VERSION and native['exe_bytes']==manifest['size']==150595584 and native['exe_sha256']==manifest['sha256']==EXE_SHA
  assert native['gzip_crc_isize_passed']and sha(directory/native['exe_relative_path'])==EXE_SHA
  assert sha(directory/f'AzerothSurvivors-{VERSION}.exe.gz')==native['compressed_sha256']
  for part in native['parts']:assert sha(directory/part['filename'])==part['sha256']and(directory/part['filename']).stat().st_size==part['bytes']
  attempt=load(directory/'wasm-compressed-transport.attempt.json');assert attempt['exit_code']==0 and attempt['decoded_bytes']==92511151 and attempt['decoded_sha256']==WASM_SHA
  status,url,transfer=attempt['stdout'].strip().splitlines();assert status=='200'and official_url(url)==f'https://wow.aethus.pl/wenilla_bg.wasm?v={STAMP}'and int(transfer)==26200711
  headers=(directory/'wasm-compressed-transport.headers').read_text().lower();assert 'content-encoding: gzip'in headers and 'x-decoded-length: 92511151'in headers
  partial=directory/'wasm-compressed-transport.decoded.part';assert sha(partial)==WASM_SHA and partial.stat().st_size==92511151
  target=directory/'latest-wenilla_bg.wasm';assert not target.exists();partial.rename(target)
  raw=target.read_bytes();assert raw.startswith(b'\0asm\1\0\0\0');anchor=raw.find(b'Made by Aethus');assert anchor>=0 and raw.find(b'Made by Aethus',anchor+1)<0 and VERSION.encode()in raw[anchor:anchor+240]
  # This adjacent branding context is only discovery. Actual ptr/length
  # consumer identity is a separate static instruction check, not inferred.
  wasm=dict(url=url,effective_url=url,status=200,bytes=len(raw),sha256=WASM_SHA,filename=target.name,
   headers_file='wasm-compressed-transport.headers',headers_sha256=sha(directory/'wasm-compressed-transport.headers'),
   transfer_bytes=int(transfer),content_encoding='gzip',decoded_by='curl --compressed',
   successful_attempt_file='wasm-compressed-transport.attempt.json',successful_attempt_sha256=sha(directory/'wasm-compressed-transport.attempt.json'))
  save(directory/'latest-wenilla_bg.wasm.http.json',wasm)
  index=load(directory/'official-index.html.http.json');assert sha(directory/'official-index.html')==index['sha256']and stamp(directory/'official-index.html')==STAMP
  scripts={}
  for name in('rogue.js','boot.js','wenilla.js'):
   p=directory/('official-'+name);record=load(p.with_name(p.name+'.http.json'));assert record['status']==200 and sha(p)==record['sha256']and p.stat().st_size==record['bytes']and record['url']==f'https://wow.aethus.pl/{name}?v={STAMP}';scripts[name]=record
  assert not(directory/'official-index-after.html').exists()and not(directory/'windows-latest-after.json').exists()
  ending=download(directory,'official-index-after.html','https://wow.aethus.pl/',max_bytes=5_000_000)
  ending_manifest=download(directory,'windows-latest-after.json','https://wow.aethus.pl/exe/latest.json',max_bytes=100_000)
  after=load(directory/'windows-latest-after.json');after_stamp=stamp(directory/'official-index-after.html')
  assert after==manifest and after_stamp==STAMP and sha(directory/'official-index-after.html')==index['sha256']
  web=dict(stamp=STAMP,stamp_after=after_stamp,page_stamp_stable_during_acquisition=True,index=index,index_after=ending,scripts=scripts,wasm=wasm,
   branding_discovery=dict(file_offset=anchor,context_hex=raw[anchor:anchor+240].hex(),expected_version_present=True,consumed_build_identity_proved=False),
   official_independent_wasm_digest_published=False,sha256_origin='Computed locally from saved complete HTTPS decoded bytes',application_start_called=False,module_instantiated=False)
  save(directory/'web-acquisition.json',web)
  result.update(status='coherent_bytes_acquired_build_identity_pending',native=native,web=web,ending_manifest=ending_manifest,native_manifest_equal_before_after=True,raw_html_equal_before_after=True,
   failed_uncompressed_partial_preserved=dict(path='latest-wenilla_bg.wasm.part',bytes=(directory/'latest-wenilla_bg.wasm.part').stat().st_size,sha256=sha(directory/'latest-wenilla_bg.wasm.part'),used_for_final_assembly=False),
   HTTP_gzip_complete=True,range_requests_used=False,EXE_executed=False)
 except BaseException as error:result.update(status='failed_preserved',error=repr(error));raise
 finally:
  result.update(finished_at_utc=datetime.now(timezone.utc).isoformat(),source_sha256_after={str(p.relative_to(ROOT)):sha(p)for p in producer})
  result['sources_unchanged']=result['source_sha256_before']==result['source_sha256_after'];assert sha(directory/'release-acquisition.json')==FAILED_SHA
  save(directory/'release-acquisition-resumed.json',result)
  print(json.dumps(dict(directory=str(directory),status=result['status'],receipt_sha256=sha(directory/'release-acquisition-resumed.json'),wasm_sha256=WASM_SHA)),flush=True)
 assert result['sources_unchanged']
if __name__=='__main__':main()
