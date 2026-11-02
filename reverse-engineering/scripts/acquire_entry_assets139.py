#!/usr/bin/env python3
"""Finite public official139 context resource acquisition, no game execution.

Historical request paths are candidates only. Every admitted resource is newly
downloaded from the official current static service; no old bytes are reused.
No supplied path or response is executed. All outputs stay in a new4T folder.
"""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse,hashlib,json,os,re,signal,subprocess,threading,time
from urllib.parse import quote,urlsplit

ROOT=Path(__file__).resolve().parents[1]
REFERENCE=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/actual-assets-inventory.json'
REFERENCE_SHA='cc31b6efd90b7bacb040b142eb72b72d7baf83c418f87258a60b3755196bc84c'
ORIGINAL=ROOT/'originals/official-release-20261102T011227.335145Z'
STAMP='f339dd20e0fe'
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False

def main():
    before=sha(Path(__file__));assert sha(REFERENCE)==REFERENCE_SHA
    ap=argparse.ArgumentParser();ap.add_argument('--resume',type=Path);args=ap.parse_args();prior={};prior_receipts=[];retained_all={}
    def collect_prior(path):
        obj=json.loads(path.read_text());assert obj['version']=='0.139.0'and obj['stamp']==STAMP and obj['old_resource_bytes_reused']is False
        if obj.get('prior_fresh139_receipt'):collect_prior(Path(obj['prior_fresh139_receipt']))
        prior_receipts.append(dict(path=str(path),sha256=sha(path)))
        for row in obj['requests']:
            if row.get('exit_code')==0 and row.get('http_status')==200 and row['name'].startswith('data/'):
                data=path.parent/'files'/row['name'];assert sha(data)==row['sha256']and data.stat().st_size==row['bytes']
                retained_all[row['name']]=dict(row,file=str(data))
    if args.resume:
        collect_prior(args.resume)
        prior=json.loads(args.resume.read_text());assert prior['version']=='0.139.0'and prior['stamp']==STAMP
        for x in prior['requests']:
            if x.get('exit_code')==0 and x.get('http_status')==200 and x['name'].startswith('data/'):
                p=args.resume.parent/'files'/x['name'];assert sha(p)==x['sha256']and p.stat().st_size==x['bytes']
        assert prior['old_resource_bytes_reused']is False
    out=ROOT/'originals'/datetime.now(timezone.utc).strftime('entry-assets139-%Y%m%dT%H%M%S.%fZ');out.mkdir();(out/'files').mkdir();(out/'http').mkdir()
    deadline=time.monotonic()+180;lock=threading.Lock();ledger=[];total=0
    def fetch(name,url):
        nonlocal total
        assert urlsplit(url).scheme=='https'and urlsplit(url).netloc=='wow.aethus.pl'and not urlsplit(url).fragment
        assert all(part not in ('','..','.')for part in name.split('/'))and '\\'not in name and not any(ord(ch)<32 for ch in name)
        target=out/'files'/name;target.parent.mkdir(parents=True,exist_ok=True);tag=hashlib.sha256(name.encode()).hexdigest()[:20];headers=out/'http'/(tag+'.headers');meta=out/'http'/(tag+'.meta');err=out/'http'/(tag+'.stderr')
        if time.monotonic()>=deadline:return dict(name=name,url=url,status='not_started_global180s_budget')
        command=['/usr/bin/curl','--silent','--show-error','--fail','--location','--proto','=https','--proto-redir','=https','--compressed','--connect-timeout','10','--max-time','35','--max-filesize','16777216','--dump-header',str(headers),'--output',str(target),'--write-out','%{http_code}\n%{url_effective}\n%{size_download}\n%{time_total}\n',url]
        started=time.monotonic()
        with meta.open('wb')as so,err.open('wb')as se:
            p=subprocess.Popen(command,stdout=so,stderr=se,start_new_session=True)
            try:code=p.wait(timeout=min(36,max(.1,deadline-time.monotonic())))
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();code=p.returncode
        lines=meta.read_text().splitlines();row=dict(name=name,url=url,exit_code=code,pid=p.pid,pgid=p.pid,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True),seconds=time.monotonic()-started,
            http_status=int(lines[0])if lines and lines[0].isdigit()else None,effective_url=lines[1]if len(lines)>1 else None,
            bytes=target.stat().st_size if target.exists()else 0,sha256=sha(target)if target.exists()else None,headers_sha256=sha(headers)if headers.exists()else None,
            partial_retained=bool(code),target_executed=False)
        assert row['pid_missing']and row['pgid_missing']
        with lock:
            total+=row['bytes'];assert total<=268435456
            ledger.append(row);save(out/'http-progress.json',dict(completed=len(ledger),decoded_bytes=total,requests=ledger))
        return row
    status='failed_preserved';error=None;rows=[]
    try:
        before_html=fetch('metadata-before.html','https://wow.aethus.pl/');before_meta=fetch('metadata-before.json','https://wow.aethus.pl/exe/latest.json')
        assert before_html['exit_code']==before_meta['exit_code']==0
        assert json.loads((out/'files/metadata-before.json').read_text())['version']=='0.139.0'
        assert STAMP in(out/'files/metadata-before.html').read_text()
        index=fetch('data/__index','https://wow.aethus.pl/data/__index?'+STAMP)
        aux=fetch('snippets/benilla-app-e11f90d5572a787b/inline0.js','https://wow.aethus.pl/snippets/benilla-app-e11f90d5572a787b/inline0.js?'+STAMP)
        assert index['exit_code']==aux['exit_code']==0
        names=json.loads((out/'files/data/__index').read_text());assert isinstance(names,list)and all(type(x)is str for x in names)
        names={x.replace('\\','/').lower()for x in names}
        candidates=sorted({x['path']for x in json.loads(REFERENCE.read_text())['requests']if x['status']==200})
        retained=dict(retained_all)
        if prior:
            assert (out/'files/metadata-before.json').read_bytes()==(args.resume.parent/'files/metadata-before.json').read_bytes()
            assert index['sha256']==next(x['sha256']for x in prior['requests']if x['name']=='data/__index')
        assert len(candidates)<=600 and all(x in names for x in candidates)
        with ThreadPoolExecutor(max_workers=4)as pool:
            tasks=[pool.submit(fetch,'data/'+name,'https://wow.aethus.pl/data/'+'/'.join(quote(s,safe='')for s in name.split('/')))for name in candidates if 'data/'+name not in retained]
            for f in as_completed(tasks):rows.append(f.result())
        after_html=fetch('metadata-after.html','https://wow.aethus.pl/');after_meta=fetch('metadata-after.json','https://wow.aethus.pl/exe/latest.json')
        assert after_html['exit_code']==after_meta['exit_code']==0
        assert (out/'files/metadata-before.json').read_bytes()==(out/'files/metadata-after.json').read_bytes()
        assert STAMP in(out/'files/metadata-after.html').read_text()
        assert all(x.get('exit_code')==0 and x.get('http_status')==200 for x in rows)
        resource_map={n:x for n,x in retained.items()if n!='data/__index'}
        resource_map.update({x['name']:dict(x,file=str(out/'files'/x['name']))for x in ledger if x.get('exit_code')==0 and x['name'].startswith('data/')})
        assert all('data/'+x in resource_map for x in candidates)
        save(out/'resource-map.json',resource_map)
        status='fresh_official139_candidate_resource_set_acquired'
    except Exception as e:error=repr(e)
    receipt=dict(kind='fresh_official139_context_resource_candidates_not_context_execution',status=status,error=error,version='0.139.0',stamp=STAMP,
        source_sha256_before=before,source_sha256_after=sha(Path(__file__)),reference_candidate_paths=str(REFERENCE.relative_to(ROOT)),reference_sha256=REFERENCE_SHA,
        old_resource_bytes_reused=False,old_snapshot_loaded=False,target_executions=0,App_produced=False,worldRc_produced=False,locale_produced=False,
        global_deadline_seconds=180,concurrency=4,per_request_deadline_seconds=35,per_file_decoded_cap=16777216,total_decoded_cap=268435456,decoded_bytes=total,
        prior_fresh139_chain=prior_receipts,prior_fresh139_receipt=str(args.resume)if args.resume else None,prior_fresh139_receipt_sha256=sha(args.resume)if args.resume else None,
        resource_map_sha256=sha(out/'resource-map.json')if(out/'resource-map.json').exists()else None,
        requests=sorted(ledger,key=lambda x:x['name']),candidate_rows=sorted(rows,key=lambda x:x['name']),
        limitations=['Only fresh public resource bytes andmatchingstamp metadata are frozen. Actual139 request set/context and resource parsing must be proved separately.','Historical paths determine candidate requests only; old assets/snapshot/acceptance are never loaded.'])
    save(out/'receipt.json',receipt);assert before==sha(Path(__file__))
    print(json.dumps(dict(directory=str(out),status=status,error=error,receipt_sha256=sha(out/'receipt.json'),requests=len(ledger),bytes=total)),flush=True)
    if error:raise SystemExit(1)

if __name__=='__main__':main()
