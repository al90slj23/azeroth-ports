#!/usr/bin/env python3
"""Freeze the official0.134 death -> XP pickup ->4630 chain, statically only.

No WASM module is instantiated. Large WAT is sought by a read-only index. The
fixture below is a recipe for later controlled probes, never runtime evidence.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import struct
import time

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCY = ROOT / 'scripts/extract_catalogue134.py'
DEPENDENCY_SHA = '4e465095731c6abc9775ce8445fdd6b96c11982300ec33be1c1b4bda0b8b709a'
MANIFEST_SHA = '952e2cd4c1fdb0bbf62cf44d6cf4f265ae15120a1572facaad23b43ff4fc51b9'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


if sha(DEPENDENCY) != DEPENDENCY_SHA:
    raise ValueError('Pinned static reader dependency differs')
from extract_catalogue134 import (Reader, parse_binary, reconstruct, require, digest,
                                  save, strict_json, SOURCE, SOURCE_SHA, PROFILE,
                                  WAT, WAT_SHA, DB, DB_SHA)

ROLES = {914: 'enemy damage and death entry', 1417: 'pickup allocation or merge',
         2862: 'pickup attraction and collection', 4630: 'XP and level transition',
         31731: 'ordered pickup remove and despawn messages',
         21779: 'attract all idle XP pickups', 35879: 'unit display-name resolution',
         58020: 'unit interpolated position', 38322: 'region ID string to index',
         49502: '2D distance helper', 29630: 'world height query',
         23181: 'nearest valid height search', 18670: 'alternate terrain height query',
         46294: 'terrain point helper', 10823: 'XP visual message construction',
         1820: 'non-XP visual object creation', 65336: '56B pickup vector reserve',
         56191: 'vector reallocation', 13196: 'reallocation or new allocation helper',
         85718: 'f32 round', 3735: 'keyed state insertion',
         50797: 'message finalization', 23469: 'keyed state lookup',
         65323: '16B message vector reserve', 106890: 'internal allocation'}

# Entire reviewed regions are retained in evidence, without flooding the report.
WINDOWS = [(914, 5104, 5552, 'death lookup position freeze and source tags'),
           (914, 5728, 5802, 'death statistics and auxiliary effect gates'),
           (914, 6819, 7261, 'U244 boss route including fixed XP and attraction'),
           (914, 7262, 7670, 'U64 special route and optional reward RNG'),
           (914, 7664, 7955, 'normal definition XP rounding currency and kind2 reward'),
           (1417, 8, 103, 'region clamp and world geometry'),
           (1417, 115, 414, 'kind0 cap and nearest idle XP merge'),
           (1417, 2438, 2558, 'XP message then actual 56B record append'),
           (2862, 1, 274, 'claimed GUID vector construction'),
           (2862, 323, 636, 'six-second claims radius and attraction timing'),
           (2862, 785, 910, 'kind-specific collection gates'),
           (2862, 1015, 1130, 'save amount remove then kind0 XP dispatch'),
           (2862, 1394, 1497, 'network XP queue mode1 multiplier and4630'),
           (31731, 1, 192, 'ordered remove and message/destructor side effects'),
           (21779, 1, 284, 'all-XP attraction with .15 minimum delay')]


def signatures(binary, indices, import_count):
    r, sections = Reader(binary, 8), {}
    while r.pos < r.end:
        kind, size = r.byte(), r.leb()
        begin = r.pos
        r.raw(size)
        if kind:
            sections[kind] = (begin, r.pos)
    r = Reader(binary, *sections[1])
    types = []
    for _ in range(r.leb()):
        require(r.byte() == 0x60, 'Unsupported function type')
        types.append((r.raw(r.leb()), r.raw(r.leb())))
    r.finished()
    r = Reader(binary, *sections[3])
    tids = [r.leb() for _ in range(r.leb())]
    r.finished()
    names = {0x7f:'i32', 0x7e:'i64', 0x7d:'f32', 0x7c:'f64', 0x6f:'externref'}
    return {i: {'type_index':tids[i-import_count],
                'parameters':[names[x] for x in types[tids[i-import_count]][0]],
                'results':[names[x] for x in types[tids[i-import_count]][1]]} for i in indices}


def main():
    started = time.monotonic()
    pins = {SOURCE:SOURCE_SHA, WAT:WAT_SHA, DB:DB_SHA, DEPENDENCY:DEPENDENCY_SHA,
            PROFILE/'manifest.json':MANIFEST_SHA}
    require(all(sha(p) == h for p,h in pins.items()), 'Frozen input identity differs')
    manifest = strict_json((PROFILE/'manifest.json').read_text())
    require(manifest['target_version']=='0.134.0' and manifest['embedded_build']=='983346a7'
            and manifest['original_sha256']==SOURCE_SHA, 'Wrong original version/build')
    binary = SOURCE.read_bytes()
    require(digest(binary)==SOURCE_SHA, 'Original readback differs')
    profile = parse_binary(binary)
    require(profile['function_imports']==878 and profile['defined_functions']==175316,
            'Original function counts differ')
    sigs = signatures(binary, ROLES, profile['function_imports'])
    require(sigs[1417]['parameters']==['i32']*4 and sigs[2862]['parameters']==['i32'],
            'Pickup signatures differ')
    out = ROOT/'evidence'/datetime.now(timezone.utc).strftime('death-xp0134-chain-%Y%m%dT%H%M%S.%fZ')
    out.mkdir(parents=True, exist_ok=False)
    c = sqlite3.connect(DB.resolve().as_uri()+'?mode=ro', uri=True)
    funcs, lines, edges, guards = {}, {}, [], []
    try:
        meta = {k:strict_json(v) for k,v in c.execute('SELECT key,value FROM meta')}
        require(meta['original_sha256']==SOURCE_SHA and meta['wat_sha256']==WAT_SHA
                and meta['terminal_parentheses_supported'] is True, 'Index provenance differs')
        with WAT.open('rb') as stream:
            for i,role in ROLES.items():
                row = c.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes FROM functions WHERE idx=?',(i,)).fetchone()
                require(row is not None and tuple(row[3:5])==profile['bodies'][i]
                        and row[5]==row[4]-row[3], 'Index/binary range differs')
                stream.seek(row[0]); wat = stream.read(row[1]-row[0])
                require(re.findall(rb'^  \(func \(;(\d+);\)',wat,re.M)==[str(i).encode()], 'Not a complete function')
                body = binary[row[3]:row[4]]
                (out/f'function-{i}.wat').write_bytes(wat)
                (out/f'function-{i}.body.bin').write_bytes(body)
                lines[i] = [x.strip() for x in wat.decode().splitlines()]
                callers = c.execute('SELECT count(DISTINCT caller) FROM calls WHERE callee=?',(i,)).fetchone()[0]
                funcs[i] = {'function_index':i,'descriptive_role':role,**sigs[i],
                    'signature_wat':wat.splitlines()[0].decode(),'wat_start':row[0],'wat_end':row[1],
                    'wat_line':row[2],'wat_bytes':len(wat),'wat_sha256':digest(wat),
                    'body_start':row[3],'body_end':row[4],'body_bytes':row[5],'body_sha256':digest(body),
                    'direct_caller_count':callers,
                    'direct_callers_sample':[x[0] for x in c.execute('SELECT DISTINCT caller FROM calls WHERE callee=? ORDER BY caller LIMIT 16',(i,))],
                    'direct_callers_sample_complete':callers<=16}
        def g(i,label,text):
            seq = text.split('|')
            pos = [n for n in range(len(lines[i])-len(seq)+1) if lines[i][n:n+len(seq)]==seq]
            require(bool(pos), 'Reviewed guard differs: '+label)
            guards.append({'function_index':i,'label':label,'function_lines':[n+1 for n in pos],
                           'full_wat_lines':[funcs[i]['wat_line']+n for n in pos], 'instructions':seq})
        g(914,'active phase1','local.get 0|i32.load8_u offset=2579|i32.const 1|i32.ne|br_if 0 (;@2;)')
        g(914,'death branch HP<=0','local.get 43|f32.const 0x0p+0 (;=0;)|f32.le|i32.eqz|if  ;; label = @4|i32.const -1|local.set 14|br 1 (;@3;)')
        g(914,'source U244 payload256','local.get 10|i32.const 180|i32.sub|i32.load|i32.const -1|i32.ne|if  ;; label = @4|local.get 10|i32.const 168|i32.sub|i32.load|local.set 16|end')
        g(914,'source U64 and payload92','local.get 10|i32.const 360|i32.sub|i32.load|local.tee 24|i32.const -1|i32.ne|if  ;; label = @4|local.get 10|i32.const 332|i32.sub|i32.load|local.set 17|end')
        g(914,'ordinary definition284','local.get 10|i32.const 140|i32.sub|i32.load|local.set 20')
        g(914,'boss increments kill counter1096','local.get 0|local.get 0|i32.load offset=1096|i32.const 1|i32.add|i32.store offset=1096')
        g(914,'boss actual XP kind0 call1417','local.get 0|i32.const 0|local.get 0|i32.load offset=1096|i32.const 20|i32.mul|i32.const 60|i32.add|local.get 8|i32.const 944|i32.add|call 1417')
        g(914,'ordinary flag68 before XP56','local.get 20|i32.load8_u offset=68|br_if 0 (;@6;)|local.get 0|local.get 20|f32.load offset=60|local.get 0|f32.load offset=2412|f32.add|f32.store offset=2412|local.get 20|i32.load8_u offset=68|br_if 0 (;@6;)|local.get 20|i32.load offset=56')
        g(914,'stochastic XP1.65 first truncation','f32.convert_i32_u|f32.const 0x1.a66666p+0 (;=1.65;)|f32.mul|local.tee 34|i32.trunc_sat_f32_u|local.get 34|local.get 34|f32.trunc|f32.sub')
        g(914,'XP fraction strict greater than random','f32.const 0x1p-24 (;=5.96046e-08;)|f32.mul|f32.gt|i32.add|br 1 (;@5;)')
        g(914,'ordinary nonzero amount kind0 call1417','local.tee 6|if  ;; label = @5|local.get 0|i32.const 0|local.get 6|local.get 8|i32.const 944|i32.add|call 1417|end')
        g(914,'currency chance flag68 threshold','f32.const 0x1p-24 (;=5.96046e-08;)|f32.mul|f32.const 0x1p+0 (;=1;)|f32.const 0x1.51eb86p-3 (;=0.165;)|local.get 11|select|f32.lt|if  ;; label = @5')
        g(1417,'region selector and table stride','local.get 0|i32.load offset=184|local.get 0|i32.load offset=188|call 38322|i32.const 152|i32.mul')
        g(1417,'kind0 cap45','local.get 6|i32.const 45|i32.lt_u|br_if 0 (;@13;)')
        g(1417,'merge amount wraps with no record append','local.get 6|local.get 6|i32.load offset=12|local.get 2|i32.add|i32.store offset=12|br 10 (;@1;)')
        g(1417,'XP counter2400 and terrain source','local.get 0|local.get 0|i32.load offset=2400|i32.const 1|i32.add|local.tee 3|i32.store offset=2400|local.get 5|local.get 0|i32.load offset=2340|local.tee 1|i32.const 8|i32.add')
        g(1417,'XP GUID masks24 bits','local.get 3|i32.const 16777215|i32.and|i64.extend_i32_u|i64.const -1067352960675086336|i64.or|local.set 14')
        g(1417,'reserve actual56B record vector','local.get 0|i32.load offset=1868|local.tee 3|local.get 0|i32.load offset=1860|i32.eq|if  ;; label = @2|local.get 0|i32.const 1860|i32.add|call 65336|end|local.get 0|i32.load offset=1864|local.get 3|i32.const 56|i32.mul|i32.add|local.tee 1')
        g(1417,'XP record amount kind marker and count','local.get 1|local.get 2|i32.store offset=12|local.get 1|i32.const 0|i32.store offset=8|local.get 1|i32.const 0|i32.store|local.get 0|local.get 3|i32.const 1|i32.add|i32.store offset=1868')
        g(1417,'XP empty auxiliary vec and visual9001','local.get 1|i64.const 38659000631296|i64.store offset=32|local.get 1|i64.const 34359738368|i64.store offset=24')
        g(2862,'age strictly over six seconds','local.get 22|local.get 5|f32.load offset=52|f32.sub|f32.const 0x1.8p+2 (;=6;)|f32.gt|i32.eqz|br_if 0 (;@3;)')
        g(2862,'only idle XP attracts','local.get 5|i32.load offset=8|br_if 0 (;@3;)|local.get 5|i32.load|br_if 0 (;@3;)')
        g(2862,'marker1 then attraction arrival time','local.get 5|i32.const 1|i32.store|local.get 5|local.get 22|f32.const 0x1.eb851ep-4 (;=0.12;)')
        g(2862,'XP collection nonzero marker and arrival<=now','local.get 1|i32.load|i32.eqz|br_if 2 (;@3;)|local.get 1|i32.const 4|i32.add|f32.load|local.get 22|f32.le|i32.eqz|br_if 2 (;@3;)')
        g(2862,'amount preserved before ordered removal and dispatch','local.get 4|i32.load offset=12|local.set 4|local.get 0|local.get 1|call 31731|local.get 3|i32.const 1|i32.sub|br_table 3 (;@15;) 1 (;@17;) 4 (;@14;) 4 (;@14;) 4 (;@14;) 5 (;@13;) 2 (;@16;)')
        g(2862,'actual mode1 XP divisor member2532','local.get 0|i32.load offset=2532|i32.const 1|i32.sub|f32.convert_i32_u|f32.mul|f32.const 0x1.3f7ceep-2 (;=0.312;)|f32.mul|f32.const 0x1p+0 (;=1;)|f32.add|f32.div|local.set 22')
        g(2862,'round minimum1 and4630','local.get 0|f32.const 0x1p+0 (;=1;)|local.get 22|local.get 0|f32.load offset=1388|local.get 4|f32.convert_i32_u|f32.mul|f32.mul|call 85718|local.tee 22|local.get 22|local.get 22|f32.ne|select|local.tee 22|f32.const 0x1p+0 (;=1;)|local.get 22|f32.const 0x1p+0 (;=1;)|f32.gt|select|i32.trunc_sat_f32_u|call 4630')
        g(31731,'ordered removal uses memory.copy','local.get 2|local.get 2|i32.const 56|i32.add|local.get 6|memory.copy')
        g(29630,'flat world gate relative world+8','local.get 1|i32.load8_u offset=112|i32.eqz|if  ;; label = @3')
        g(29630,'flat world height and validity','local.get 1|f32.load offset=108|local.set 4|i32.const 1|local.set 8|br 1 (;@1;)')
        g(65336,'grow pickup vector at least4 doubled align8 stride56','i32.const 4|local.get 2|i32.const 1|i32.shl|local.tee 2|local.get 2|i32.const 4|i32.le_u|select|local.tee 2|i32.const 8|i32.const 56|call 56191')
        require(not any(f'offset={i}' in '\n'.join(lines[1417]) for i in (1712,1716,1720,1724)), 'Pickup builder unexpectedly references RNG state')
        for caller,callee in ((914,1417),(914,21779),(914,35879),(1417,38322),(1417,49502),
                              (1417,29630),(1417,23181),(1417,10823),(1417,65336),
                              (65336,56191),(56191,106890),(56191,13196),(2862,31731),(2862,4630),
                              (2862,85718),(29630,18670),(18670,46294)):
            sites = [{'wat_offset':a,'wat_line':b,'instruction':k} for a,b,k in c.execute('SELECT wat_offset,wat_line,instruction FROM calls WHERE caller=? AND callee=? ORDER BY wat_line',(caller,callee))]
            require(bool(sites),'Missing reviewed direct edge')
            edges.append({'caller':caller,'callee':callee,'sites':sites})
    finally:
        c.close()
    windows = []
    for i,begin,end,label in WINDOWS:
        require(1<=begin<=end<=len(lines[i]), 'Reviewed window exceeds complete function')
        raw = ('\n'.join(lines[i][begin-1:end])+'\n').encode()
        name = f'guard-{i}-{begin}-{end}.wat.txt'
        (out/name).write_bytes(raw)
        windows.append({'function_index':i,'label':label,'function_lines':[begin,end],
                        'full_wat_lines':[funcs[i]['wat_line']+begin-1,funcs[i]['wat_line']+end-1],
                        'path':name,'bytes':len(raw),'sha256':digest(raw)})
    memory = reconstruct(binary,profile)
    records = []
    for address,label in ((5411616,'Kobold Vermin normal definition'),(5412264,'Kobold Taskmaster flagged definition'),(5414404,'Hogger U244-route definition')):
        raw = bytes(memory[address:address+72]); (out/f'static-definition-{address}.bin').write_bytes(raw)
        records.append({'address':address,'descriptive_role':label,'bytes':72,'sha256':digest(raw),
                        'u32_words':list(struct.unpack('<18I',raw))})
    region = bytes(memory[5452152:5452152+152]); (out/'region0-5452152.bin').write_bytes(region)
    center = list(struct.unpack_from('<ff',region,12)); radius = struct.unpack_from('<f',region,28)[0]
    require(center==[-9396.0,-633.0] and radius==120.0, 'Default region geometry differs')
    layout = {'G':{'region_id_pointer':184,'region_id_length':188,'xp_multiplier_f32':1388,
        'pickup_radius_f32':1384,'player_x_f32':1504,'player_y_f32':1508,'player_z_bits':1512,
        'level_u32':1520,'xp_u32':1524,'rng_words_u32':[1712,1716,1720,1724],
        'unit_pointer':1780,'unit_count':1784,'unit_stride':424,
        'pickup_capacity':1860,'pickup_pointer':1864,'pickup_count':1868,
        'message_capacity':1872,'message_pointer':1876,'message_count':1880,
        'special_unit_pointer':1912,'special_unit_count':1916,'pending_reward_pointer':1960,'pending_reward_count':1964,
        'world_pointer':2340,'now_f32':2344,'pending_levelup':2368,'xp_spawn_counter':2400,
        'message_sequence':2404,'definition60_accumulator_f32':2412,'local_peer_id':2520,'member_count':2532,
        'mode_u8':2574,'phase_u8':2579,'claim_pointer':2104,'claim_count':2108,'claim_stride':88,
        'xp_network_queue_capacity':2136,'xp_network_queue_pointer':2140,'xp_network_queue_count':2144},
        'Unit':{'marker_u32':0,'death_time_f32':4,'tag40':40,'tag64':64,'tag64_payload_index':92,
        'guid_u64':112,'tag244':244,'tag244_payload_definition':256,'ordinary_definition':284,
        'hp_f32':288,'max_hp_f32':292,'position_start_xyz':[316,320,324],
        'position_end_xyz':[328,332,336],'movement_start_f32':340,'movement_duration_f32':344,
        'flag416_u8':416},
        'Pickup56':{'marker_u32':0,'arrival_time_f32':4,'kind_u32':8,'amount_u32':12,
        'guid_u64':16,'aux_capacity':24,'aux_pointer':28,'aux_count':32,'visual_id':36,
        'x_f32':40,'y_f32':44,'height_f32':48,'spawn_time_f32':52},
        'OrdinaryDefinition72':{'base_xp_u32':56,'accumulated_scalar_f32':60,'flag68_u8':68},
        'World':{'allocation_proposal_bytes':128,'fallback_height_f32':116,'flat_height_gate_u8':120,
                 'nearest_height_tag_i32':56}}
    semantics = {
      'normal_death_xp':{'gate':'U244 payload pointer==0, U64==-1, U284!=0; earlier death branch reached',
        'flag68_zero':'q=f32(f32.u32(def.u32(56))*f32(1.65)); amount=wrap_u32(trunc_sat_u32(q)+(f32(q-trunc_f32(q))>rng24)); consumes one RNG draw even for base0',
        'flag68_nonzero':'amount=def.u32(56); no XP-rounding RNG draw',
        'nonzero_amount':'1417(G,0,amount,death_position_ptr)',
        'following_currency':'always one direct RNG draw; threshold flag68?1:0.165; success kind1 amount flag68?15:bounded(3)+2; multiply u32 output by3 in u64, reject low32>0xbfffffff, return high32+2; sampler consumes >=1 extra draws when flag68=0; nested1820 visual-object RNG is outside this direct914 draw projection',
        'following_flagged_reward':'flag68!=0 also invokes1417 kind2 after world height lookup',
        'rng_family':'direct instruction recurrence matches xoshiro128++ on four u32 words; no seed generation accepted',
        'rng24':'f32.u32((rotl32(wrap_u32(s0+s3),7)+s0 mod2^32)>>8)*2^-24',
        'rng_update':['t=s1<<9 mod2^32','s2^=s0','s3^=s1','s1^=s2','s0^=s3','s2^=t','s3=rotl32(s3,11)'],
        'full914_rng_count':'not universally two: other death effects, item callbacks and later recursive914 may execute; only branch-local direct draws established'},
      'tag244_route':{'identification':'U244!=-1 yields U256 pointer; sample static U256 Hogger makes boss descriptive role concrete',
        'xp':'increment wrap G1096, then amount=wrap_u32(60+20*G1096);1417(G,0,amount,deathPos)',
        'other':'kind1 reward, optional scheduled kind6,21779 attracts all idle XP; mode1 queues boss-death state; full boss side effects retained only'},
      'tag64_route':{'gate':'tag244 payload pointer==0 && U64!=-1',
        'xp':'no direct kind0 creation in reviewed route; calls21779 to attract existing XP',
        'other':'increment G1092;kind1=wrap_u32(25+5*G1092), optional kind6 with RNG<.5; mode-specific counter2380/2552',
        'naming':'message mentions lair and other guardians; a universal elite/pet semantic is not established'},
      'pet_and_elite_scope':{'tag40':'not a universal XP rejection gate in reviewed final source-selection block; ordinary U284 nonzero could still reach XP',
        'flag416':'tracked for kill/effect branches; ordinary XP amount block reads definition68 rather than Unit416',
        'unknown':'No complete semantic classification of all ordinary elite, pet, summoned, guardian and boss constructors; fixture must report raw tags and definition pointers'},
      'builder1417':{'parameters':['G','kind_u32','amount_u32','xyz_pointer'],
        'kind0':'kind-1 unsigned br_table default arm; kind0 expected, other unrecognized kinds also take default',
        'cap':'for canonical markers0/1, idle kind0 count<45 appends; >=45 searches nearest idle kind0 and adds wrapping amount in place; raw count sums kind0?(marker XOR1):0, so noncanonical markers require original instructions; do not assume one new record per death',
        'geometry':'region38322(G184,G188); center5452164/5452168+152*i; radial clamp max(1,radius-2), radius5452180+152*i; height via world geometry',
        'guid':'0xf130002329000000 OR (wrap_u32(++G2400)&0xffffff)',
        'new_record':'marker0,kind0,amount,GUID,aux(cap0,ptr8,count0),visual9001,xy/height,spawnTime=now',
        'arrival_field':'new append does not initialize+4; marker0 makes it unread until attraction writes it',
        'rng':'1417 has no direct accesses to RNG words; kind0 path avoids1820, uses serialization10823'},
      'attract2862':{'distance':'ordered f32 sqrt((pickup.x-player.x)^2+(pickup.y-player.y)^2); height ignored',
        'only_idle_xp':'kind0 && marker0',
        'ordinary_radius':'distance<=G.f32(1384) attracts',
        'age_override':'age=now-spawnTime strictly>6 plus no matching claim GUID; locally constructed claim set contains GUIDs whose 88B claim has marker1 and matching+8 GUID',
        'arrival':'marker=1;arrival=f32(now+max_nan_safe(.12, distance/(age_override?32:24)))',
        'sequence':'attraction first pass emits movement messages; collection second pass still requires stored arrival<=same entry now',
        '21779':'attract-all helper uses max_nan_safe(.15,distance/40), no radius/age filter'},
      'collect2862':{'kind0':'marker!=0 && arrival<=now; no fresh distance or phase guard',
        'order':'queue indices in forward vector order, process indices backwards; read kind and amount,31731 ordered removal before dispatch',
        'remove':'memory.copy shifts following56B records down; decrementscount; may emit object despawn messages and free aux vector',
        'xp':'R85718(f32(f32(G1388*f32.u32(amount))*modeMultiplier)); NaN=>1,min1,trunc_sat_u32;4630(G,result)',
        'mode0':'multiplier1 and no XP network queue',
        'nonzero_mode':'append (G2520,baseAmount)8B record toG2136/2140/2144 beforeXP',
        'mode1':'multiplier=f32(1/(1+(((regionIndex<3?.7:1)*f32.u32(wrap_u32(G2532-1)))*.312))) with actual f32 instruction ordering retained',
        'other_nonzero_modes':'queue still appended; multiplier stays1',
        '4630':'separate progression trace covers XP1524,level1520,pending2368,120 natural cap and choice guard'}
    }
    fixture = {'status':'static proposal only; not executed or accepted','entry_chain':['914(G,GUID,damage,spell,school,crit,extra)','2862(G) at death now','2862(G) at stored pickup arrival'],
        'initial_G_bytes_proposal':8192,'initial_world_bytes_proposal':128,
        'entry_phase':1,'selectors':[1,1],'world':'G2340=V;V.u8(120)=1;V.f32(116)=0;V.i32(56)=-1',
        'region':'empty region ID length0 selects region0; player and both Unit position triplets should be(-9396,-633,0)',
        'ordinary_unit':'424B;GUID1;HP/maxHP100;U40=U64=U244=-1;U284=5411616;marker0;duration344=0;phase1;time10',
        'pickup':'initializeG1860/1864/1868 empty or allocate real56B capacity; radius1384>=0; xp_multiplier1388=1',
        'rng':'supply four nonzero-seed words and compare full state; choose no-currency seed for first narrow fixture or preserve currency1820 side effects',
        'selection':'use level120 for narrow pipeline fixture, or set phase3 only after914 and before2862 to skip real2159 guard; natural phase1 selection is separate acceptance',
        'auxiliary_initialization':['G2340 world','G1780/1784 units','G1860/1864/1868 pickups','G1872/1876/1880 messages','G1652/1656/1660 owned','G2020/2024 items','G2044/2048 modifiers','G2104/2108 claims','G2136/2140/2144 networkXP','G2468/2472 keyed state'],
        'observe_after_914':['Unit marker/HP/deathTime/position','G1868 and complete56B pickup bytes (exclude uninitialized+4 until attraction)','G2400','G1712..1724 RNG','G1880 messages','G2412 definition60 accumulator'],
        'observe_after_first2862':['pickup marker1','pickup+4 arrival time','pickup count retained','XP not yet collected when arrival>now'],
        'observe_at_arrival':['pickup ordered removal','G1524 XP','G1520 level','G2368 pending','G2579 phase','RNG unchanged by narrow kind0 builder/collector path'],
        'needed_corpus':['normal flag68 0 vs1 and baseXP0/1/large','exact fractional-random boundary','currency fail/pass and bounded rejection','44/45idle merge boundary and nearest tie','moving death interpolation','radius exact/below/above','age6/exactly-over6 and claim presence','arrival exact/below/NaN; huge now where f32(now+.12)==now','mode0/1/other, member_count0/1/2, region<3/>=3','U244 boss, U64 special and no-definition/pet tags'],
        'uncovered':'No original target run, full host import inventory, allocation budget, record bytes or seed acceptance. Later source-specific probe must establish these.'}
    identity = {'source_sha256':SOURCE_SHA,'profile_manifest_sha256':MANIFEST_SHA,'wat_sha256':WAT_SHA,
        'database_sha256':DB_SHA,'static_reader_sha256':DEPENDENCY_SHA,'trace_tool_sha256':sha(Path(__file__))}
    result = {'target_version':'0.134.0','build':'983346a7','status':'static trace complete',
        'input_identity':identity,'evidence_directory':str(out),'database_read_only':True,
        'complete_functions':list(funcs.values()),'direct_edges':edges,'instruction_guards':guards,
        'continuous_windows':windows,'state_layout':layout,'semantics':semantics,
        'static_definitions':records,'default_region':{'address':5452152,'bytes':152,'sha256':digest(region),'center':center,'radius':radius},
        'fixture_proposal':fixture,'target_executed':False,'runtime_oracle_cases':0,
        'network_used':False,'app_or_save_writes':False,'elapsed_seconds':round(time.monotonic()-started,3),
        'limitations':['This is static source evidence, not execution acceptance.',
          'All raw tag constructors are not classified; pet/elite semantic labels remain partial.',
          'Full914 death callbacks, recursion, item effects, visual messages and non-XP loot are retained or identified, not independently implemented.',
          'Direct RNG recurrence is recovered; universal full914 RNG advancement is not claimed.',
          'Full region terrain behavior, mode synchronization and entry-frame scheduling are not independently specified.']}
    require(all(sha(p)==h for p,h in pins.items()), 'Frozen input changed during trace')
    save(out/'manifest.json',result)
    report = ROOT/'reports/2026-11-01-death-xp0134-chain.json'
    save(report,result)
    for item in funcs.values():
        i = item['function_index']
        require(sha(out/f'function-{i}.wat')==item['wat_sha256'] and sha(out/f'function-{i}.body.bin')==item['body_sha256'], 'Function evidence readback differs')
    print(json.dumps({'evidence_directory':str(out),'functions':len(funcs),'guards':len(guards),
        'continuous_windows':len(windows),'report':str(report),'manifest_sha256':sha(out/'manifest.json'),
        'target_executed':False,'runtime_oracle_cases':0},ensure_ascii=False))


if __name__ == '__main__':
    main()
