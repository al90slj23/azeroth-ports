#!/usr/bin/env python3
"""Extract fixed135 ability/class declarations from actual instruction bounds.

Pure bounded binary/DBC-style image routines are reused from134. No target is
instantiated and no old address is shifted to guess a new declaration pointer.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from extract_catalogue134 import parse_binary, reconstruct, extract, compare, sha, save, require

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
PROFILE = ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
WAT = PROFILE/'official-0.135.1-full.wat'
WAT_SHA = '15bccec81235752573d903d098911612d8add22cc51956d03afb8fb17382a7f2'
DB = PROFILE/'index.sqlite'
DB_SHA = 'b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
OLD_SOURCE = ROOT/'originals/official-acquisition-20261031T235700.049192Z/latest-wenilla_bg.wasm'
OLD_SHA = '2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52'
OLD_REPORT = ROOT/'reports/2026-11-01-catalogue0134.json'


def main():
    identities = {SOURCE:SOURCE_SHA,WAT:WAT_SHA,DB:DB_SHA,OLD_SOURCE:OLD_SHA}
    require(all(sha(p)==v for p,v in identities.items()),'Pinned input differs')
    frozen = {str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),ROOT/'scripts/extract_catalogue134.py',OLD_REPORT)}
    binary = SOURCE.read_bytes(); profile = parse_binary(binary)
    require((profile['function_imports'],profile['defined_functions'],len(profile['segments']))==(878,175317,28471),'New profile differs')
    out = ROOT/'evidence'/datetime.now(timezone.utc).strftime('catalogue0135-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    con = sqlite3.connect(DB.resolve().as_uri()+'?mode=ro',uri=True)
    texts, functions, guards = {},[],[]
    with WAT.open('rb') as stream:
        for index in (1011,1072,1480):
            ws,we,line,bs,be = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end FROM functions WHERE idx=?',(index,)).fetchone()
            require(profile['bodies'][index]==(bs,be),'Binary/index range differs')
            stream.seek(ws);text=stream.read(we-ws)
            require(text.startswith(f'  (func (;{index};) '.encode()),'Function header differs')
            texts[index]='\n'.join(x.strip() for x in text.decode().splitlines())
            (out/f'function-{index}.wat').write_bytes(text)
            functions.append(dict(index=index,wat_start=ws,wat_end=we,wat_line=line,body_start=bs,body_end=be,
                                  wat_sha256=hashlib.sha256(text).hexdigest(),body_sha256=hashlib.sha256(binary[bs:be]).hexdigest()))
    con.close()
    def guard(index,pattern,label):
        found=list(re.finditer(pattern,texts[index]));require(len(found)==1,'Guard differs: '+label)
        m=found[0];guards.append(dict(index=index,label=label,instructions=m[0].splitlines()));return m
    loop=guard(1480,r'local.get 9\ni32.const (\d+)\ni32.add\nlocal.tee 9\ni32.const (\d+)\ni32.ne','ability stride/bound')
    stride,total=map(int,loop.groups())
    base=int(guard(1480,r'local.get 9\ni32.const (\d+)\ni32.add\nlocal.tee 6\ni32.store offset=304','ability base')[1])
    require(stride==88 and total==10032,'Observed ability layout differs')
    guard(1072,rf'local.get 1\ni32.const {stride}\ni32.add\nlocal.tee 1\ni32.const {total}\ni32.ne','selected-card bound independently confirms')
    guard(1072,rf'local.get 1\ni32.const {base}\ni32.add\nlocal.tee 4\ni32.store offset=200','selected-card base independently confirms')
    cb=int(guard(1011,r'i32.const (\d+)\nlocal.set 2\nglobal.get 0\ni32.const 16\ni32.sub\nlocal.tee 5\nglobal.set 0\nblock  ;; label = @10','class start')[1])
    cl=guard(1011,r'br_if 1 \(;@13;\)\nlocal.get 2\ni32.const (\d+)\ni32.add\nlocal.tee 2\ni32.const (\d+)\ni32.ne\nbr_if 0 \(;@14;\)','class stride/end')
    cs,ce=map(int,cl.groups());require(cs==88 and (ce-cb)%cs==0,'Class layout differs')
    memory=reconstruct(binary,profile)
    current=extract(memory,profile['segments'],dict(memory_start=base,stride=stride,count=total//stride),dict(memory_start=cb,stride=cs,count=(ce-cb)//cs,memory_end_exclusive=ce))
    old_report=json.loads(OLD_REPORT.read_text());require(old_report['version']=='0.134.0' and old_report['original_wasm_sha256']==OLD_SHA,'Baseline report differs')
    ob=OLD_SOURCE.read_bytes();op=parse_binary(ob);om=reconstruct(ob,op)
    old=extract(om,op['segments'],{k:old_report['ability_table'][k]for k in('memory_start','stride','count')},{k:old_report['class_table'][k]for k in('memory_start','stride','count')})
    require(all([x['record_sha256']for x in old[k]]==[x['record_sha256']for x in old_report[k]] for k in('abilities','classes')),'Old declaration bytes differ')
    delta=compare(old,current)
    # The pure comparison helper retains historical labels; this invocation is134->135.
    delta.update(baseline_version='0.134.0',current_version='0.135.1')
    save(out/'catalogue.json',current);save(out/'delta-from-0134.json',delta)
    require(all(sha(p)==v for p,v in identities.items()) and all(sha(ROOT/n)==v for n,v in frozen.items()),'Input/source drift')
    result=dict(date='2026-11-01',version='0.135.1',build='0898d5e3',original_wasm_sha256=SOURCE_SHA,
                wat_sha256=WAT_SHA,index_sha256=DB_SHA,complete_functions=functions,instruction_guards=guards,
                source_sha256=frozen,**current,delta_from_0134=delta,evidence_directory=str(out.relative_to(ROOT)),
                target_executed=False,old_raw_records_reconfirmed=True,
                limitations=['Initial static declarations, not all ability/kit behavior or runtime mutations.','Old134 result counts are not135 acceptance; physical pointers are extracted independently.'])
    save(out/'manifest.json',result);result['local_manifest_sha256']=sha(out/'manifest.json')
    save(ROOT/'reports/2026-11-01-catalogue0135.json',result)
    (ROOT/'reports/2026-11-01-catalogue0135.md').write_text(f'''# 官方0.135.1能力与职业目录\n\n固定0.135.1 / 0898d5e3的原始初始data映像重新提取 **{len(current['abilities'])}能力、{len(current['classes'])}职业**。新完整1480/1072同时确认能力base{base}、stride{stride}、总{total}B；1011确认职业base{cb}、stride{cs}、end{ce}。所有字符串/升级kind列表/kit都按新指针读取，未按旧地址统一平移。\n\n相邻JSON保留完整88B记录、原始位、指针来源及与固定0.134.0的逐字段比较。静态声明相同不代表所有效果/天赋/解锁或运行时producer已实现；实际数值与选择另由135原件差分验收。证据 `{out.relative_to(ROOT)}`；没有实例化WASM、联网、访问用户存档或修改安装游戏。\n''')
    print(json.dumps(dict(directory=str(out),ability_base=base,class_base=cb,abilities=len(current['abilities']),classes=len(current['classes']),delta=delta),ensure_ascii=False))


if __name__=='__main__':main()
