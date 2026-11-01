#!/usr/bin/env python3
"""Build byte-matched continuous933/934 instruction slices, NOT full functions.

Custom bounded wrappers initialize locals and scratch memory. Every retained
slice is found byte-for-byte in the identity-checked original WASM body. There
are no callees/stubs/imports/start/data/table, and the game is never instantiated.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
from wasm_index import ORIGINAL_SHA, body_ranges, sha
from build_radius_oracle import read_leb

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'evidence/wasm-index-20261031T213003.825753Z/index.sqlite'
WAT_SHA = '02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c'
PIN = {933: ('8f3936de6295d0250b32ab3abf1a3bb7f6b913a2b3067f26f6e0561dd3128e5f',
             'e3f34bbb48729849c3d8feb3aed7ee9710e0550ec0e0e78dc45e636335221d26'),
       934: ('0da442c86897761d461c11007b5fdb4cbafb27a1ba1f923a379592c832b67175',
             '41c6ec557bded46c1c3f51ca048ae950058d053690498fc764dda27ac3242609')}
# Non-self-overlapping, stack-neutral delimiter. A repeated-nop marker can
# overlap an instruction ending in0x01 (notably fc01 trunc_sat_f32_u).
MARK = b'\x41\xe7\x8a\x8d\x09\x1a'
MARK_WAT = 'i32.const 19088743\ndrop'


def parse_module(data):
    p = 8
    sections, bodies = [], []
    while p < len(data):
        kind = data[p]
        size, start = read_leb(data, p + 1)
        end = start + size
        if end > len(data):
            raise ValueError('Section out of bounds')
        sections.append(kind)
        if kind == 10:
            n, q = read_leb(data, start)
            for _ in range(n):
                size, begin = read_leb(data, q)
                q = begin + size
                bodies.append(data[begin:q])
            if q != end:
                raise ValueError('Code section boundary mismatch')
        p = end
    if p != len(data) or sections != [1, 3, 5, 7, 10] or len(bodies) != 8:
        raise ValueError('Unexpected sections/function count; imports/start/data/table forbidden')
    return sections, bodies


def instruction_offsets(body, wat_lines):
    """Decode every original instruction and bind each WAT line to its byte offset.

    Searching a short opcode byte string alone can find an immediate belonging
    to a different instruction (fc01 also occurs inside i32.const252).
    """
    names = {0:'unreachable',2:'block',3:'loop',4:'if',5:'else',11:'end',12:'br',13:'br_if',
      14:'br_table',16:'call',26:'drop',27:'select',32:'local.get',33:'local.set',34:'local.tee',
      35:'global.get',36:'global.set',40:'i32.load',41:'i64.load',42:'f32.load',43:'f64.load',
      45:'i32.load8_u',47:'i32.load16_u',49:'i64.load8_u',51:'i64.load16_u',53:'i64.load32_u',
      54:'i32.store',55:'i64.store',56:'f32.store',57:'f64.store',58:'i32.store8',59:'i32.store16',
      65:'i32.const',66:'i64.const',67:'f32.const',68:'f64.const',69:'i32.eqz',70:'i32.eq',
      71:'i32.ne',72:'i32.lt_s',73:'i32.lt_u',75:'i32.gt_u',76:'i32.le_s',77:'i32.le_u',
      79:'i32.ge_u',80:'i64.eqz',81:'i64.eq',82:'i64.ne',91:'f32.eq',92:'f32.ne',93:'f32.lt',
      94:'f32.gt',95:'f32.le',96:'f32.ge',106:'i32.add',107:'i32.sub',108:'i32.mul',112:'i32.rem_u',
      113:'i32.and',114:'i32.or',115:'i32.xor',116:'i32.shl',117:'i32.shr_s',118:'i32.shr_u',
      119:'i32.rotl',126:'i64.mul',131:'i64.and',132:'i64.or',133:'i64.xor',134:'i64.shl',136:'i64.shr_u',
      141:'f32.ceil',142:'f32.floor',143:'f32.trunc',145:'f32.sqrt',146:'f32.add',147:'f32.sub',
      148:'f32.mul',149:'f32.div',150:'f32.min',151:'f32.max',160:'f64.add',167:'i32.wrap_i64',
      173:'i64.extend_i32_u',179:'f32.convert_i32_u',184:'f64.convert_i32_u',187:'f64.promote_f32',
      188:'i32.reinterpret_f32'}
    def skip(p):
        for _ in range(10):
            byte=body[p];p+=1
            if byte<128:return p
        raise ValueError('Unterminated original LEB')
    groups,p=read_leb(body,0)
    for _ in range(groups):
        _,p=read_leb(body,p);p+=1
    decoded=[]
    while p<len(body):
        start=p;op=body[p];p+=1
        if op==252:
            sub,p=read_leb(body,p)
            if sub==1:name='i32.trunc_sat_f32_u'
            elif sub==10:name='memory.copy';p=skip(skip(p))
            else:raise ValueError('Unexpected extended original instruction')
        else:
            if op not in names:raise ValueError(f'Unknown original opcode{op}')
            name=names[op]
            if op in (2,3,4,12,13,16,32,33,34,35,36,65,66):p=skip(p)
            elif op==14:
                count,p=read_leb(body,p)
                for _ in range(count+1):p=skip(p)
            elif 40<=op<=62:p=skip(skip(p))
            elif op==67:p+=4
            elif op==68:p+=8
        decoded.append((start,p,name))
    source=[line.strip().split()[0].rstrip(')') for line in wat_lines[2:]]
    if [x[2] for x in decoded] != source+['end']:
        raise ValueError('Original WAT/instruction byte alignment differs')
    return {line:decoded[line-3] for line in range(3,len(wat_lines)+1)}


def build():
    source = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    binary = source.read_bytes()
    if hashlib.sha256(binary).hexdigest() != ORIGINAL_SHA:
        raise ValueError('Original identity differs')
    ranges = body_ranges(binary)
    con = sqlite3.connect(f'file:{INDEX}?mode=ro', uri=True)
    con.execute('PRAGMA query_only=ON')
    meta = {k: json.loads(v) for k, v in con.execute('SELECT key,value FROM meta')}
    fullwat = Path(meta['wat_path'])
    if meta['wat_sha256'] != WAT_SHA or sha(fullwat) != WAT_SHA:
        raise ValueError('Full original WAT identity differs')
    lines, original_bodies, original_instructions = {}, {}, {}
    with fullwat.open('rb') as stream:
        for idx in PIN:
            a, b = con.execute('SELECT wat_start,wat_end FROM functions WHERE idx=?', (idx,)).fetchone()
            stream.seek(a)
            wat = stream.read(b - a)
            begin, end, _ = ranges[idx]
            body = binary[begin:end]
            if sha_bytes(body) != PIN[idx][0] or sha_bytes(wat) != PIN[idx][1]:
                raise ValueError('Full original function identity differs')
            lines[idx] = wat.decode().splitlines()
            original_bodies[idx] = body
            original_instructions[idx] = instruction_offsets(body, lines[idx])
    con.close()
    plans = [
        ('modifiers', 933, '', [(8, 1022)], 'end\nlocal.get 31\ni32.reinterpret_f32'),
        ('category_guard', 933, 'i32.const 8192\nlocal.set 10\nblock\nblock\nblock', [(1228, 1239)], 'end\ni32.const 1\nlocal.set 30\nend\nend\nlocal.get 30'),
        ('cap', 933, 'i32.const 8224\nlocal.set 12\nlocal.get 2\nlocal.set 31',
         [(1241, 1265)], 'i32.reinterpret_f32'),
        ('hp', 933, 'i32.const 8192\nlocal.set 18\nlocal.get 2\nlocal.set 31',
         [(1303, 1337), (1446, 1455)], 'local.get 33\ni32.reinterpret_f32'),
        ('death', 933, 'i32.const 8536\nlocal.set 11\ni32.const 8608\nlocal.set 7\n'
         'i32.const 16384\nlocal.set 8\nlocal.get 2\nlocal.set 37',
         [(4627, 4672)], 'i32.const 0'),
        ('base', 934, 'i32.const 8192\nlocal.set 8\ni32.const 16384\nlocal.set 3',
         [(440, 507)], 'local.get 33\ni32.reinterpret_f32'),
        ('critical', 934, 'local.get 0\nf32.load offset=2100\nlocal.set 33',
         [(730, 764), (767, 789)], 'drop\nlocal.get 0\nlocal.get 1\ni32.store offset=2104\n'
         'local.get 32\ni32.reinterpret_f32'),
        ('wire', 933, 'local.get 2\nlocal.set 34', [(3102, 3113), (3148, 3148), (3292, 3292)], ''),
    ]
    funcs = []
    for name, idx, pre, spans, post in plans:
        signature = '(param i32 i64 f32 i32 i32 i32 i32)' if idx == 933 else '(param i32 i32)'
        chunks = ['\n'.join(lines[idx][a-1:b]) for a,b in spans]
        for chunk in chunks:
            if re.search(r'\b(call|global\.|memory.grow|table\.)', chunk):
                raise ValueError('External references forbidden in a retained slice')
        func = f'(func (export "{name}") {signature} (result i32)\n{lines[idx][1]}\n{pre}\n'
        func += '\n'.join(MARK_WAT + '\n' + c + '\n' + MARK_WAT for c in chunks)
        funcs.append(func + '\n' + post + '\n)')
    output = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('combat-oracle-%Y%m%dT%H%M%S.%fZ')
    output.mkdir(parents=True)
    watfile = output / 'combat-slices.wat'
    wasmfile = output / 'combat-slices.wasm'
    watfile.write_text('(module\n(memory (export "memory") 32 32)\n' + '\n'.join(funcs) + '\n)\n')
    wabt = ROOT / '.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin'
    provenance = json.loads((ROOT / '.toolchain/rea-wasm-profile/installed-provenance.json').read_text())
    for tool in ('wat2wasm','wasm-validate'):
        if sha(wabt / tool) != (provenance['tools'][tool]['sha256'] if tool in provenance['tools'] else '69117d2b10c1818cf6da921f96ab4e3c50e45a05a848d6c4c1788375aec4d250'):
            raise ValueError('WABT tool identity differs')
    subprocess.run([str(wabt / 'wat2wasm'), str(watfile), '-o', str(wasmfile)], check=True, timeout=30)
    subprocess.run([str(wabt / 'wasm-validate'), str(wasmfile)], check=True, timeout=30)
    sections, bodies = parse_module(wasmfile.read_bytes())
    matches = []
    for (name, idx, _, spans, _), body in zip(plans, bodies):
        pieces = body.split(MARK)
        if len(pieces) != 2 * len(spans) + 1:
            raise ValueError('Slice marker count differs')
        for (a,b), chunk in zip(spans, pieces[1::2]):
            if name == 'wire' and (a, b) == (3292, 3292) and chunk != b'\xfc\x01':
                raise ValueError('trunc_sat_f32_u must retain both opcode bytes')
            offset = original_instructions[idx][a][0]
            end = original_instructions[idx][b][1]
            if not chunk or original_bodies[idx][offset:end] != chunk:
                raise ValueError(f'{name}:{a}..{b} is not byte-identical at the original instruction boundaries')
            matches.append({'export': name, 'original_function': idx, 'wat_lines': [a,b],
                            'original_body_relative_offset': offset, 'original_file_start': ranges[idx][0]+offset,
                            'original_file_end': ranges[idx][0]+end,
                            'instruction_boundaries_checked': True, 'bytes': len(chunk),
                            'sha256': sha_bytes(chunk), 'byte_identical': True})
    if sha(source) != ORIGINAL_SHA or sha(fullwat) != WAT_SHA:
        raise ValueError('Original artifacts changed during build')
    manifest = {'version':'0.126.0','build':'3e72472a','original_wasm_sha256': ORIGINAL_SHA,
                'complete_wat_sha256':WAT_SHA,'module_file':wasmfile.name,'module_sha256':sha(wasmfile),
                'module_bytes':wasmfile.stat().st_size,'sections':sections,'slices':matches,
                'memory':{'minimum_pages':32,'maximum_pages':32,'exported':True},
                'imports':[],'stub_callees':[],'start':None,'data_segments':[],
                'original_full_933_executed':False,'original_full_934_executed':False,
                'method':'byte-identical contiguous instruction slices with custom initialization/termination wrappers',
                'full_game_started':False,'network_used':False,'user_saves_accessed':False}
    (output / 'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return output, manifest


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


if __name__ == '__main__':
    output, manifest = build()
    print(json.dumps({'run_directory':str(output),'module_bytes':manifest['module_bytes'],
                      'byte_identical_slices':len(manifest['slices'])}))
