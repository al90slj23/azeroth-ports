#!/usr/bin/env python3
"""Bounded read-only139 context observations, never independent predictions."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,struct
ROOT=Path(__file__).resolve().parents[1]
LAYOUTS={'NPC':(1784,1788,1792,432),'companions':(2108,2112,2116,88),'pickups':(1868,1872,1876,56),'special':(1916,1920,1924,40),'windows':(1964,1968,1972,8),'boundaries':(2120,2124,2128,8)}
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 before=sha(Path(__file__));ap=argparse.ArgumentParser();ap.add_argument('--batch',type=Path,required=True);ap.add_argument('--receipt-sha256',required=True);args=ap.parse_args();BATCH=args.batch;RECEIPT_SHA=args.receipt_sha256
 assert sha(BATCH/'receipt.json')==RECEIPT_SHA;receipt=json.loads((BATCH/'receipt.json').read_text());assert sha(BATCH/'runtime.json')==receipt['artifacts']['runtime.json'];runtime=json.loads((BATCH/'runtime.json').read_text());assert receipt['version']=='0.139.0'
 snapshots=[x for x in runtime['result']['snapshots']if x.get('memory_artifact')];assert len(snapshots)==2
 INPUTS=[(x['memory_artifact']['file'],x['memory_artifact']['sha256'],x)for x in snapshots]
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('entry-world139-v2-inspection-%Y%m%dT%H%M%S.%fZ');out.mkdir();rows=[]
 for name,h,meta in INPUTS:
  APP,GAME,WORLD=meta['App'],meta['G'],meta['world_rc_pointer']
  p=BATCH/name;assert sha(p)==h;raw=p.read_bytes();assert len(raw)<=268435456 and len(raw)%65536==0
  def read(a,n):assert 0<=a<=a+n<=len(raw);return raw[a:a+n]
  def u(a):return struct.unpack('<I',read(a,4))[0]
  def q(a):return struct.unpack('<Q',read(a,8))[0]
  def vector(layout):
   co,po,no,stride=layout;c,p,n=u(GAME+co),u(GAME+po),u(GAME+no);assert n<=c<=4096
   return dict(capacity=c,pointer=p,count=n,stride=stride,storage_hex=[read(p+j*stride,stride).hex()for j in range(c)])
  vectors={k:vector(v)for k,v in LAYOUTS.items()};npcs=[]
  for j in range(vectors['NPC']['count']):
   p=vectors['NPC']['pointer']+j*432;d=u(p+284);ptr,n=u(d+16),u(d+20);assert n<=1024
   npcs.append(dict(index=j,guid=str(q(p+112)),definition_pointer=d,definition72_hex=read(d,72).hex(),definition_name_utf8_hex=read(ptr,n).hex(),definition_name=read(ptr,n).decode(),entry=u(d+24),HP288_bits=u(p+288),classification424=read(p+424,1)[0],new416=u(p+416),new420=u(p+420),tail427_431_observed_hex=read(p+427,5).hex()))
  def queue(co,po,no,stride,packet):
   c,p,n=u(GAME+co),u(GAME+po),u(GAME+no);assert n<=c<=4096;entries=[]
   for j in range(n):
    a=p+j*stride;cap,ptr,length=u(a),u(a+4),u(a+8);assert length<=cap<=1048576
    e=dict(capacity=cap,pointer=ptr,length=length,payload_hex=read(ptr,length).hex(),metadata_hex=read(a,stride).hex())
    if packet:e['opcode']=struct.unpack('<H',read(a+12,2))[0]
    entries.append(e)
   return dict(capacity=c,pointer=p,count=n,entries=entries,metadata_backing_hex=read(p,c*stride).hex())
  assert u(APP+5116)==u(GAME+2348)==WORLD
  rows.append(dict(input_file=name,input_sha256=h,input_bytes=len(raw),App=APP,G=GAME,worldRc=WORLD,phase2587=read(GAME+2587,1)[0],counter2408=u(GAME+2408),rng_words=[u(GAME+1720+4*j)for j in range(4)],player_xyz=[u(GAME+1416+4*j)for j in range(3)],
   raw_Game2592_hex=read(GAME,2592).hex(),raw_App5168_hex=read(APP,5168).hex(),raw_worldRc124_hex=read(WORLD,124).hex(),selected376_hex=read(APP+3376,376).hex(),account368_hex=read(APP+4160,368).hex(),vectors=vectors,NPC_observations=npcs,
   packets=queue(1880,1884,1888,16,True),notifications=queue(1892,1896,1900,12,False)))
 result=dict(version='0.139.0',build='f79c5e2b4',kind='read_only_original_context_observations_not_model_outputs',receipt_sha256=RECEIPT_SHA,script_sha256=before,selection_output=runtime['result']['selection_output'],rows=rows,target_executions=0,production_model_executions=0,
  limitations=['All bytes/headers/names here are observations, not independent predictions.','Definitionname is the fallback declaration UTF8, not a proof ofresolvedlocale display.','Inactive/padding observations must not populate unknown model cells.','Research App/selectedprofile boundary is retained from original capture.'])
 p=out/'observations.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');assert before==sha(Path(__file__))
 print(json.dumps(dict(directory=str(out),sha256=sha(p),stages=[dict(phase=r['phase2587'],counts={k:x['count']for k,x in r['vectors'].items()},NPC_names=[x['definition_name']for x in r['NPC_observations']],packet_count=r['packets']['count'],notification_count=r['notifications']['count'])for r in rows])),flush=True)
if __name__=='__main__':main()
