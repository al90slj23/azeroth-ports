#!/usr/bin/env python3
"""Read-only review of the completed750 capture and a separately sealed reread.

No original, model, builder, or checker is executed. The declared frozen CAS
decoder is a transport dependency. NPC Aura169 recognition below is independent
of opening_npc_aura135; previous cast and AI reviews are separate dependencies.
"""
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
from functools import lru_cache
import argparse, ast, hashlib, importlib.util, json, struct, sys, time, zlib

sys.dont_write_bytecode = True
import review_opening_combat135_650 as base
import review_demo_shout135 as cast_review
from review_combat137 import exports

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / 'evidence/opening-combat0135-oracle-20261101T210558.218894Z'
S = base.semantic
F, B, add, sub, mul, word = base.F, base.B, base.add, base.sub, base.mul, base.word
ORIGINAL_SHA = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
OLD_DECODER_SHA = 'f9ace95818b6384ad2663d293a07d036efc0aac52c8cd75fdabb3ec82065cd2c'
SNAPSHOT_SHA = '23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf'
NODE_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def guid(row):
    return struct.unpack_from('<Q', row, 112)[0]


def rows(raw):
    vector = raw['vectors']['units']
    return [bytes.fromhex(x) for x in vector['storage'][:vector['count']]]


def owners(raw):
    result = {guid(row): row for row in rows(raw)}
    assert len(result) == raw['vectors']['units']['count']
    return result


@lru_cache(maxsize=32768)
def npc_aura(opcode, payload):
    """Parse a generic single values block, then test its three-key geometry.

    This neither imports the production classifier nor uses predicted GUIDs or
    a whitelist of spell values to decide which packets should be compared.
    Malformed/non-Aura wire shapes are outside this classifier's narrow domain.
    """
    if opcode != 169:
        return None
    data = bytes.fromhex(payload)
    if len(data) < 8 or data[:6] != struct.pack('<IBB', 1, 0, 0):
        return None
    cursor = 7
    owner = 0
    for shift in range(8):
        if data[6] & (1 << shift):
            if cursor >= len(data):
                return None
            owner |= data[cursor] << (8 * shift)
            cursor += 1
    if owner >> 48 != 0xf130 or cursor >= len(data):
        return None
    blocks = data[cursor]
    cursor += 1
    if not 1 <= blocks <= 8 or cursor + blocks * 4 > len(data):
        return None
    masks = struct.unpack_from('<' + 'I' * blocks, data, cursor)
    cursor += blocks * 4
    keys = [32 * i + bit for i, mask in enumerate(masks)
            for bit in range(32) if mask & (1 << bit)]
    if len(keys) != 3 or cursor + 4 * len(keys) != len(data):
        return None
    fields = dict(zip(keys, struct.unpack_from('<3I', data, cursor)))
    candidate = [key - 79 for key in keys if 79 <= key < 95]
    if len(candidate) != 1:
        return None
    slot = candidate[0]
    if set(keys) != {79 + slot, 99 + slot // 8, 121 + slot // 4}:
        return None
    return dict(guid=str(owner), slot=slot, fields=fields, payload169_hex=payload)


def projection_aura(raw):
    return [dict(guid=item['guid'], slot=item['slot'], payload169_hex=item['payload169_hex'])
            for packet in raw['packets']['active']
            if (item := npc_aura(packet['opcode'], packet['payload_hex'])) is not None]


def aura_negatives():
    owner = 0xf13000000100002a
    fields = [(79, 1160), (99, 2), (121, 0)]
    packet = cast_review.aura_packet(owner, fields)
    assert npc_aura(169, packet)['fields'] == dict(fields)
    # All16 slots and arbitrary values prove shape recognition is not tied to
    # Demo spell1160 or only the observed first slot.
    positives = 0
    for slot in range(16):
        f = [(79 + slot, 0x12345678), (99 + slot // 8, 0xabcdef01), (121 + slot // 4, 7)]
        p = cast_review.aura_packet(owner, f)
        assert npc_aura(169, p)['slot'] == slot and npc_aura(169, p)['fields'] == dict(f)
        positives += 1
    probes = [('wrong_opcode', 150, packet), ('truncated', 169, packet[:-2]),
              ('extra_tail', 169, packet + '00'),
              ('wrong_GUID_class', 169, cast_review.aura_packet(0xf11000000100002a, fields)),
              ('wrong_slot_group', 169, cast_review.aura_packet(owner, [(79, 1160), (100, 2), (121, 0)])),
              ('wrong_quartet', 169, cast_review.aura_packet(owner, [(79, 1160), (99, 2), (122, 0)])),
              ('extra_key', 169, cast_review.aura_packet(owner, fields + [(5, 1)])),
              ('wrong_block_kind', 169, (bytes.fromhex(packet)[:5] + b'\2' + bytes.fromhex(packet)[6:]).hex()),
              ('wrong_count', 169, (b'\2' + bytes.fromhex(packet)[1:]).hex())]
    for label, opcode, value in probes:
        assert npc_aura(opcode, value) is None, label
    return dict(positive_slots=positives, rejected=[x[0] for x in probes],
                scope='Auditor parser selfchecks only; zero new original/model cases.')


def gzip_identity(path):
    inflater = zlib.decompressobj(31)
    digest, compressed = hashlib.sha256(), hashlib.sha256()
    size = file_size = count = maximum = 0
    pending = b''
    with Path(path).open('rb') as stream:
        while chunk := stream.read(65536):
            compressed.update(chunk); file_size += len(chunk)
            assert file_size <= 268435456
            while chunk:
                part = inflater.decompress(chunk, 2097153)
                chunk = inflater.unconsumed_tail
                digest.update(part); size += len(part); pending += part
                assert size <= 1073741824
                while (end := pending.find(b'\n')) >= 0:
                    length = end + 1
                    assert length <= 2097152
                    maximum = max(maximum, length); count += 1
                    pending = pending[length:]
                assert len(pending) <= 2097152
                if inflater.eof:
                    assert not inflater.unused_data and not chunk and not stream.read(1)
                    break
            if inflater.eof:
                break
    assert inflater.eof and not pending
    return dict(records=count, bytes=size, sha256=digest.hexdigest(),
                file_sha256=compressed.hexdigest(), file_bytes=file_size,
                maximum_record_bytes=maximum, single_member=True)


class DemoTracker:
    """Original-only GUID-bound transition audit, independent of model output.

    The reviewer authored the AI implementation, so this is an integration
    check and reuse of the other author's AI review, not an independent second
    reconstruction of that implementation. Cast merge/geometry/Aura checks use
    this reviewer's separately authored cast audit, not production routines.
    """
    def __init__(self, definition):
        self.definition = definition
        self.selected = None
        self.countdown = []
        self.casts = []
        self.expirations = []
        self.deaths = []
        self.removals = []
        self.contacts = []
        self.counts = Counter()
        self.added = []
        self.casted = set()

    @staticmethod
    def state(row):
        return dict(words128_140=[word(row, o) for o in (128, 132, 136, 140)],
                    spell360=word(row, 360), duration364_bits=word(row, 364),
                    aura_slots168=[word(row, o) for o in range(168, 232, 4)],
                    ability_count240=word(row, 240))

    def observe(self, before, raw, action):
        if raw['record_kind'] != 'stage':
            return
        stage, now = raw['kind'], raw['projection']['now_bits']
        old, current = owners(before), owners(raw)
        delta = raw['new_packets']['appended']
        added = [item for p in delta if (item := npc_aura(p['opcode'], p['payload_hex'])) is not None]
        expected_added = []
        cast_this_phase = False
        effect_owners = set()
        if stage == 'select':
            new_owned = [bytes.fromhex(x) for x in raw['projection']['owned_records_hex']]
            previous_owned = [bytes.fromhex(x) for x in before['projection']['owned_records_hex']]
            new_demo = [x for x in new_owned if word(x, 0) == 5467868]
            if new_demo and not any(word(x, 0) == 5467868 for x in previous_owned):
                assert self.selected is None and len(new_demo) == 1
                row = new_demo[0]
                assert word(row, 4) == 1 and word(row, 8) == B(.5)
                card = before['projection']['candidates'][action['index']]
                assert card['ability_id'] == 'demo_shout'
                self.selected = dict(frame=raw['frame'], completed_frames_before_selection=raw['frame'],
                    stage_index=raw['stage_index'], action_index=raw['action_index'], card=card,
                    owned80_hex=row.hex(), tier=word(row, 4), initial_countdown_bits=word(row, 8))
        if stage == 'player' and self.selected:
            previous_owned = [bytes.fromhex(x) for x in before['projection']['owned_records_hex']]
            new_owned = [bytes.fromhex(x) for x in raw['projection']['owned_records_hex']]
            old_demo = next(x for x in previous_owned if word(x, 0) == 5467868)
            new_demo = next(x for x in new_owned if word(x, 0) == 5467868)
            assert old_demo[:8] + old_demo[12:] == new_demo[:8] + new_demo[12:]
            remaining = sub(word(old_demo, 8), action['dt_bits'])
            tick = dict(frame=raw['frame'], completed_frame_number=raw['frame'] + 1,
                        stage_index=raw['stage_index'], before_bits=word(old_demo, 8),
                        subtract_dt_bits=action['dt_bits'], subtracted_bits=remaining,
                        after_bits=word(new_demo, 8))
            self.countdown.append(tick)
            if F(remaining) > 0:
                assert word(new_demo, 8) == remaining
            else:
                cast_this_phase = True
                definition, derived = self.definition, before['projection']['derived_bits']
                radius = mul(mul(word(definition, 60), mul(word(old_demo, 24), word(old_demo, 64))), derived['1580'])
                assert F(radius) <= 70
                # Prove the outer player snapshot is also the Demo entry
                # target view in this capture, rather than filtering away
                # possible earlier-cleave or later-basic deaths post hoc.
                other_timers=[dict(definition_pointer=word(row,0),before_bits=word(row,8),
                    subtracted_bits=sub(word(row,8),action['dt_bits']))for row in previous_owned if word(row,0)!=5467868]
                assert all(F(row['subtracted_bits'])>0 for row in other_timers)
                basic=bytes.fromhex(before['projection']['racial_record_hex'])
                basic_remaining=sub(word(basic,8),action['dt_bits'])
                prelude_remaining=sub(before['projection']['timer1628_bits'],action['dt_bits'])
                assert F(basic_remaining)>0 and F(prelude_remaining)>0
                candidates = cast_review.targets(list(old.values()), before['projection']['player_xyz'][:2], radius, now)
                selected = candidates
                assert all(word(current[owner],0)==0 and F(word(current[owner],288))>0 for _,owner in selected)
                # Every922 target consumes one critical draw even when chance
                # is zero. Match the exact whole-stage RNG advance as another
                # check that no prior learned/prelude/basic cast intervened.
                rng_words=tuple(before['projection']['rng_words'])
                for _ in selected:_,rng_words=base.next_rng(rng_words)
                assert list(rng_words)==raw['projection']['rng_words']
                cooldown = mul(mul(mul(mul(word(definition, 52), 0x3fb33333), word(old_demo, 16)), word(old_demo, 56)), derived['1544'])
                cooldown = cooldown if F(cooldown) > .25 else B(.25)
                assert word(new_demo, 8) == (cooldown if candidates else 0x3e4ccccd)
                strength = mul(0x3eb33333, word(old_demo, 76))
                strength = strength if F(strength) < F(0x3f666666) else 0x3f666666
                duration = mul(B(6), word(old_demo, 68))
                witness = dict(frame=raw['frame'], completed_frame_number=raw['frame'] + 1,
                    stage_index=raw['stage_index'], now_bits=now, player_ticks_since_selection=len(self.countdown),
                    radius_bits=radius, strength_bits=strength, duration_bits=duration,
                    deadline_bits=add(now, duration), targets=[str(owner) for _, owner in selected],
                    query_target_count=len(candidates), affected_target_count=len(selected), cooldown_bits=word(new_demo, 8),
                    other_owned_countdowns=other_timers,basic_subtracted_bits=basic_remaining,
                    class1_prelude_subtracted_bits=prelude_remaining,
                    all_other_cast_timers_positive=True,all_query_targets_nonfatal=True,
                    exact_whole_player_RNG_draws=len(selected))
                for index, owner in selected:
                    effect_owners.add(owner)
                    a, b = old[owner], current[owner]
                    expected = cast_review.merge21455([word(a, o) for o in (128,132,136,140)], strength, add(now,duration), now)
                    assert [word(b,o)for o in(128,132,136,140)] == expected
                    if F(expected[0]) == F(strength) and F(expected[1]) == F(add(now,duration)):
                        assert word(b,364) == duration
                    assert word(a,360) == 0 and word(b,360) == 1160 and word(a,240) == word(b,240) == 0
                    slots = [word(a,o)for o in range(168,232,4)]
                    assert 1160 not in slots and 0 in slots
                    slot=slots.index(0); slots[slot]=1160
                    assert [word(b,o)for o in range(168,232,4)] == slots
                    flags=sum(2 << (4*i)for i,v in enumerate(slots[(slot//8)*8:(slot//8+1)*8])if v)
                    fields=[(79+slot,1160),(99+slot//8,flags),(121+slot//4,0)]
                    expected_added.append(cast_review.aura_packet(owner,fields)); self.casted.add(owner)
                self.casts.append(witness)
        if stage == 'ai':
            for owner, a in old.items():
                if word(a,360) != 1160 or word(a,0) != 0:
                    continue
                assert owner in current and word(a,64)==0xffffffff and word(a,240)==0
                assert word(a,280)==word(bytes.fromhex(before['raw_game2592_hex']),2528)
                b=current[owner]
                assert b[128:144] == a[128:144] and b[364:368] == a[364:368]
                expiry=word(a,132)if F(word(a,132))>F(now)else word(a,140)
                slots=[word(a,o)for o in range(168,232,4)]
                if F(expiry)<=F(now):
                    assert word(b,360)==0 and 1160 in slots
                    slot=slots.index(1160);slots[slot]=0
                    assert[word(b,o)for o in range(168,232,4)]==slots
                    flags=sum(2<<(4*i)for i,v in enumerate(slots[(slot//8)*8:(slot//8+1)*8])if v)
                    fields=[(79+slot,0),(99+slot//8,flags),(121+slot//4,0)]
                    expected_added.append(cast_review.aura_packet(owner,fields))
                    self.expirations.append(dict(guid=str(owner),frame=raw['frame'],completed_frame_number=raw['frame']+1,
                        stage_index=raw['stage_index'],now_bits=now,selected_expiry_bits=expiry,
                        primary_expiry_bits=word(a,132),backup_expiry_bits=word(a,140),
                        words128_140_preserved=True,duration364_preserved=True,slot=slot))
                else:
                    assert word(b,360)==1160 and b[168:232]==a[168:232]
                    self.counts['active_AI_status_owner_observations']+=1
                # Physical attack timer reset is a contact witness; scalar and
                # full921 semantics are covered by the separate AI reviewer.
                if (word(a,352)!=word(b,352) and word(b,352)==word(a,304)
                        and F(sub(word(a,352),action['dt_bits']))<=0):
                    weakness=word(a,128)if F(word(a,132))>F(now)else word(a,136)if F(word(a,140))>F(now)else 0
                    self.contacts.append(dict(guid=str(owner),frame=raw['frame'],stage_index=raw['stage_index'],
                        weakness_bits=weakness,unmitigated_contact_bits=mul(word(a,296),sub(B(1),weakness))))
            if added:
                first = next(i for i,p in enumerate(delta)if npc_aura(p['opcode'],p['payload_hex'])is not None)
                assert all(npc_aura(p['opcode'],p['payload_hex'])is not None for p in delta[first:])
                self.counts['expiry_batches_after_all_other_AI_packets']+=1
        assert [x['payload169_hex']for x in added]==expected_added,(stage,raw['frame'],len(added),len(expected_added))
        self.added.extend(dict(frame=raw['frame'],stage=stage,stage_index=raw['stage_index'],**x)for x in added)
        for owner in set(old)&set(current):
            a,b=old[owner],current[owner]
            if owner in self.casted and word(a,0)==0 and word(b,0)==1:
                self.deaths.append(dict(guid=str(owner),frame=raw['frame'],stage=stage,stage_index=raw['stage_index'],
                    status_retained=word(a,360)==word(b,360),spell360=word(b,360)))
            if stage not in('player','ai'):
                assert self.state(a)==self.state(b)
                if word(a,360)==1160:self.counts['nonconsumer_status_preservation_observations']+=1
            if stage=='player'and not cast_this_phase:
                assert self.state(a)==self.state(b)
            if stage=='player'and cast_this_phase and owner not in effect_owners:
                assert self.state(a)==self.state(b)
            if stage=='ai'and word(a,0)==1 and word(a,360)==1160:
                assert self.state(a)==self.state(b)
                self.counts['dead_status_retained_until_compaction']+=1
        removed=[owner for owner in old if owner not in current]
        for owner in removed:
            if owner in self.casted:
                assert stage=='ai'and word(old[owner],0)==1
                self.removals.append(dict(guid=str(owner),frame=raw['frame'],stage_index=raw['stage_index'],
                    spell360=word(old[owner],360),dead_rows_not_sent_to_live_AI=True))
        if stage=='ai'and removed:
            assert list(current)==[owner for owner in old if owner not in removed]
            self.counts['stable_AI_compaction_batches']+=1

    def report(self):
        assert self.selected and self.selected['frame']==665 and len(self.casts)==1
        assert self.casts[0]['frame']==670 and self.casts[0]['player_ticks_since_selection']==6
        assert self.countdown[4]['subtracted_bits']==0x32800000 and F(self.countdown[4]['subtracted_bits'])>0
        assert self.casts[0]['affected_target_count']==12 and len(self.expirations)==3
        assert len(self.added)==15
        return dict(selection=self.selected,countdown=self.countdown,casts=self.casts,
                    expirations=self.expirations,deaths=self.deaths,removals=self.removals,
                    contact_timer_witnesses=self.contacts,actual_Aura169_events=self.added,counts=dict(self.counts),
                    all_targets_bound_to_original_physical_GUIDs=True,
                    AI_independence='This reviewer authored AI; independent AI component review by another author is a declared dependency. This is a composition/readback check, not a second independent AI reconstruction.')


def component_reviews():
    values = [
        ('demo-shout135-independent-review-owned-20261101T210700.766545Z/review/review.json', '33211f76462dc3708d29df764da5cff006ac64d6fcfbb40e505be768069b0f0e'),
        ('demo-ai135-independent-review-20261101T210610.715719Z/review.json', '8a1ad29df94cf2d0c53be6075fb4924da723a6fe9bae5f7846ae8b2859616795')]
    result=[]
    for name,digest in values:
        path=ROOT/'evidence'/name; assert sha(path)==digest
        review=load(path); assert review['status']=='passed_scoped_read_only_review'
        assert sha(Path(review['comparison']))==review['comparison_sha256']
        result.append(dict(path=str(path),sha256=digest,comparison_sha256=review['comparison_sha256'],
                           scope='Existing independently reviewed component, zero new original cases in this integration review.'))
    return result


def source_guards(source):
    headless=(source/'reconstruction/core_spec/headless135.py').read_text()
    ai=(source/'reconstruction/core_spec/ai135.py').read_text()
    world=(source/'reconstruction/core_spec/ai_world135.py').read_text()
    owner=headless[headless.index('def _demo_owner135'):headless.index('\n\ndef ',headless.index('def _demo_owner135')+1)]
    assert all(text in owner for text in ("u64(raw,112", "u32(raw,360", "u32(raw,364", 'range(168,232,4)', 'u32(raw,240'))
    phase=headless[headless.index('def _ai_phase'):headless.index('def _effects_phase')]
    assert 'known_demo_statuses=tuple(_demo_owner135(state.records[j])for j in indices' in phase
    assert "if u32(state.records[j],360,'AI typed demo spell')==1160"in phase
    assert "elif u32(raw,0,'Headless AI live marker')==0:indices.append(j)"in phase
    assert phase.index('known_demo_statuses=')<phase.index('update_world_ordinary_units135(ai_input')
    assert 'put_u32(raw,360,0)'not in phase and 'put_u32(raw, 360, 0)'not in phase
    assert 'elif _get(raw,360):'in ai and 'known_demo_statuses:tuple=()'in ai
    body=world[world.index('def update_world_ordinary_units135'):]
    assert body.index('demo_bindings=demo_bindings135')<body.index('_validate(raw, state.now_bits')<body.index('removal=begin_demo_expiry135')<body.index('if _float(raw, 400)')<body.index('for guid, amount in attacks:')<body.index('declarations,packets,fields=finish_demo_expiry135')
    return dict(typed_sparse_exact_physical_owner=True,no_temporary_zero_to_bypass_guard=True,
                dead_rows_excluded_from_live_AI=True,default_unbound_nonzero_status_guard_retained=True,
                expiry_before_U400_contact_and_Aura_after_attack_batch=True)


def reviewer_sources(out):
    todo=[Path(__file__).resolve()];result={}
    while todo:
        path=todo.pop();name=str(path.relative_to(ROOT))
        if name in result:continue
        result[name]=sha(path);text=path.read_text()
        for item in ast.walk(ast.parse(text)):
            modules=([x.name for x in item.names]if isinstance(item,ast.Import)
                     else[item.module]if isinstance(item,ast.ImportFrom)and item.module else[])
            for module in modules:
                target=ROOT/'scripts'/(module.replace('.','/')+'.py')
                if target.is_file():
                    assert module.startswith('review_'),'Reviewer must not import a production/checker module'
                    todo.append(target)
        target=out/'reviewer-source-snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(path.read_bytes());assert sha(target)==result[name]
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recomparison',type=Path)
    parser.add_argument('--comparison-sha',required=True)
    parser.add_argument('--codec-review',type=Path,required=True)
    parser.add_argument('--codec-sha',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();began=time.monotonic();out=args.output.resolve();out.mkdir()
    reviewer_hashes=reviewer_sources(out)
    directory=args.recomparison.resolve();capture=CAPTURE.resolve()
    assert sha(directory/'comparison.json')==args.comparison_sha
    report=load(directory/'comparison.json');binding=load(directory/'capture-binding.json')
    assert report['status']=='matched_existing_complete_capture'and report['differences']==0
    assert(report['independent_frames'],report['independent_selections'],report['compared_stages'])==(750,6,10506)
    assert report['new_original_executions']==report['new_original_entry_calls']==0
    assert report['source_sha256_before']==report['source_sha256_after']==binding['current_comparison_sources']
    assert report['captured_source_sha256']==binding['frozen_capture_sources']
    sources=report['source_sha256_before']; captured=report['captured_source_sha256']
    assert len(sources)==111 and len(captured)==110
    source=directory/'source-snapshot';old_source=capture/'source-snapshot'
    for name,digest in sources.items():assert sha(source/name)==digest==sha(ROOT/name),name
    for name,digest in captured.items():assert sha(old_source/name)==digest,name
    changed={n for n in captured if captured[n]!=sources[n]}
    assert changed=={'scripts/opening_combat135_cas.py'}
    assert captured['scripts/opening_combat135_cas.py']==OLD_DECODER_SHA
    production=sorted(n for n in sources if n.startswith('reconstruction/'))
    assert production==S.frozen_closure(source)and len(production)==95
    for name in production:
        assert captured[name]==sources[name]
        for node in ast.walk(ast.parse((source/name).read_text())):
            if isinstance(node,ast.Call):
                fun=node.func;name_called=fun.id if isinstance(fun,ast.Name)else fun.attr if isinstance(fun,ast.Attribute)else''
                assert name_called not in('open','read_bytes','read_text','write_bytes','write_text','Popen','eval','exec','__import__'),(name,name_called)
    for name,digest in binding['capture_artifacts_before'].items():assert sha(capture/name)==digest==report['capture_artifacts_sha256'][name],name
    assert binding['new_original_calls']==0 and binding['original_execution_restarted']is False
    codec=load(args.codec_review);assert sha(args.codec_review)==args.codec_sha
    assert codec['negative_count']==codec['rejected_count']==28 and codec['sources_before']==codec['sources_after']
    assert not codec['original_program_executed']and codec['new_original_cases']==0
    for key in('pilot','Node_saved_codec_roundtrip'):
        assert codec[key]['logical_values_equal_external_truth']and codec[key]['per_line_SHA_equal_external_truth']
    decoder_sha=sources['scripts/opening_combat135_cas.py'];assert codec['sources_before']['scripts/opening_combat135_cas.py']==decoder_sha
    decoder_path=source/'scripts/opening_combat135_cas.py'
    spec=importlib.util.spec_from_file_location('declared_frozen_750_CAS_transport',decoder_path)
    transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
    assert transport.CAPTURE_RECORD_LIMIT==11304
    decoder=transport.CaptureCAS135(capture)
    fixture=load(capture/'fixtures.json');config=load(capture/'config.json');runtime=load(capture/'opening-combat135-cas-runtime.json')
    assert runtime==report['runtime']and fixture['independent_frames']==750 and fixture['stage_count']==10506
    assert load(capture/'inputs.json')==[{k:fixture[k]for k in('id','input','actions')}]
    assert config['snapshot_sha256']==SNAPSHOT_SHA==sha(Path(config['snapshot_path']))
    assert config['clock_scheduler']=='explicit_external_f32_add_G2352_not_original880'
    assert config['app_pointer']==14549000 and config['world_pointer']==26204808
    assert config['input_sha256']==sha(capture/'inputs.json')
    check=(old_source/'scripts/check_opening_combat135.py').read_text()
    assert check.index('row=corpus(')<check.index('child=subprocess.Popen(')
    regenerated=load(directory/'model-regeneration.json')
    assert regenerated['no_original_state_used']and regenerated['captured_and_regenerated_logical_bytes_equal']
    assert regenerated['fixture']==fixture
    regeneration_source=(source/'scripts/recompare_opening_combat135.py').read_text()
    assert regeneration_source.index('regenerated = corpus(')<regeneration_source.index('decoder = CaptureCAS135(')
    assert 'Popen('not in regeneration_source and 'subprocess'not in regeneration_source
    regen=gzip_identity(directory/'regenerated-expectations.jsonl.gz')
    assert {k:regen[k]for k in('records','bytes','sha256')}==regenerated['logical']==report['logical_model_expectations']
    assert regen['file_sha256']==regenerated['regenerated_expectation_sha256']
    original=(ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm').read_bytes()
    assert hashlib.sha256(original).hexdigest()==ORIGINAL_SHA
    manifest=load(capture/'manifest.json');module=(capture/manifest['module_file']).read_bytes()
    assert hashlib.sha256(module).hexdigest()==manifest['module_sha256']
    a,b=S.sections(original),S.sections(module)
    assert[x[0]for x in a]==[x[0]for x in b]and 8 not in[x[0]for x in a]
    assert all(original[x:y]==module[u:v]for(k,x,_,y),(_,u,_,v)in zip(a,b)if k!=7)
    assert exports(module)==exports(original)+[['research_opening_combat135_'+x['role'],0,x['index']]for x in manifest['roles']]+[['research_opening_combat135_stack',3,0]]
    read_static=S.static_reader(original);battle_definition=read_static(5467956,88);demo_definition=read_static(5467868,88)
    assert word(demo_definition,0)==11 and word(demo_definition,44)==1160 and demo_definition[84]==2
    del original,module
    base.prepare_additional(read_static,old_source)
    dependencies=component_reviews();guards=source_guards(source);parser_checks=aura_negatives()
    S.check_queue=base.check_queue500;S.check_value=base.check_value650
    expected_reader=S.JsonlReader(capture/'stage-expectations.jsonl.gz',True,1073741824)
    expected=iter(expected_reader);opening_item=next(expected);assert opening_item['record_kind']=='opening';opening=opening_item['expected']
    # Bind the same independently parsed world inputs explicitly; no world
    # loader or production parser is called by this reviewer.
    world_path=ROOT/'evidence/asset-world0135-independent-20261101T111736.050879Z'
    world_hashes={'terrain-query.bin':'3ecb0d08bc2202524a0b2a86cf43b7a6eba7d201de70f104c4dc675bf1e12b9e',
        'navigation.bin':'239b456859bedd6c4e1ebcdf5dadeefc6da66b344ec108e17f8b85819157fd79',
        'secondary-height.u32le':'07c7ab72911e7425456abdbad2a16b3d9fe068db17367996693f70a8be2df1d5',
        'receipt.json':'4042ee79112521f67bca6d39447d9072a9b9b2f1c6f78d3b8fdab21a9d36f7c5',
        'inputs.json':'603bd691eb614f4c0ae932401c2d790761c9b18b38951922c2fa9757bd4d7b80'}
    for name,digest in world_hashes.items():assert sha(world_path/name)==digest
    world_artifacts={str(world_path/n):h for n,h in world_hashes.items()}
    world_context=dict(world_input=dict(receipt=str(world_path/'receipt.json'),receipt_sha256='4042ee79112521f67bca6d39447d9072a9b9b2f1c6f78d3b8fdab21a9d36f7c5',artifacts=world_artifacts))
    distance=S.independent_distance_sha(opening,world_context)
    order=[('case_start',None,None,0),('constructor',None,None,0),('opening',None,None,0)];frame=0
    for index,action in enumerate(fixture['actions']):
        if action['kind']=='select':order.append(('stage',index,'select',frame))
        else:
            assert action['kind']=='controlled_tail_frame'
            order.append(('clock_control',index,None,frame));order.extend(('stage',index,stage,frame)for stage in base.STAGES);frame+=1
    order.append(('case_end',None,None,frame));assert frame==750 and len(order)==11260 and len(fixture['actions'])==756
    compressed=(capture/'results.cas.jsonl.gz').read_bytes();assert len(compressed)<=268435456
    inflate=zlib.decompressobj(31);index_raw=inflate.decompress(compressed,33554433)
    assert len(index_raw)<=33554432 and inflate.eof and not inflate.unused_data and not inflate.unconsumed_tail
    counts=Counter();maximum=defaultdict(int);records=Counter();clock=0;stage_index=0
    previous=previous_want=last=locale=first_guardian=first_battle=fourth_select=None
    selections=[];guardian_owners={};guardian_captures=guardian_payloads=packet_max=battle_tick_count=0
    battle_countdowns=[];previous_packets=[];previous_notifications=[];negative=[]
    resource_events=[];resource_deadline=0x42200000;resource_payloads=[];clock_crossings=[]
    demo=DemoTracker(demo_definition)
    lines=index_raw.splitlines(keepends=True);assert len(lines)==len(order)
    for line_index,line in enumerate(lines):
        assert time.monotonic()-began<420,'Read-only750 review420s budget'
        raw=decoder.decode_line(line);kind,action_index,stage_kind,frame_index=order[line_index]
        records[raw['record_kind']]+=1;assert raw['record_kind']==kind and raw['id']==0
        if action_index is not None:assert raw['action_index']==action_index and raw['frame']==frame_index
        if stage_kind is not None:assert raw['kind']==stage_kind
        if kind=='case_start':locale=raw['locale_prestate'];assert locale['effective_index']==0 and locale['once_flag']==3
        if kind=='clock_control':
            action=fixture['actions'][action_index];assert raw['old_bits']==clock and raw['dt_bits']==action['dt_bits']
            clock=B(F(clock)+F(action['dt_bits']));assert raw['new_bits']==clock and raw['original880_called']is False and raw['only_external_game_write_offset']==2352
            if F(raw['old_bits'])<40<=F(clock):clock_crossings.append(dict(frame=frame_index,old_bits=raw['old_bits'],new_bits=clock))
        if kind in('constructor','opening','stage'):
            raw['projection']['npc_aura_updates169']=projection_aura(raw)
            want=opening if kind=='opening'else None
            if kind=='stage':
                item=next(expected);assert item['record_kind']=='stage'and item['stage_index']==stage_index and item['action_index']==action_index and item['kind']==stage_kind
                want=item['expected'];counts['stage_identity_leaves']+=2
            guardians=base.check_snapshot500(raw,want,counts,maximum,read_static);packet_max=max(packet_max,raw['packets']['count'])
            for queue,field,old in(('packets','new_packets',previous_packets),('notifications','new_notifications',previous_notifications)):
                current=[dict(opcode=x['opcode'],payload_hex=x['payload_hex'])for x in raw[queue]['active']]if queue=='packets'else[x['payload_hex']for x in raw[queue]['active']]
                prefix=len(old)<=len(current)and current[:len(old)]==old;delta=raw[field]
                assert delta['prefix_preserved']==prefix and delta['previous_count']==len(old)and delta['current_count']==len(current)and delta['appended']==(current[len(old):]if prefix else[])
                if not prefix:assert delta['full_current']==current
                if queue=='packets':previous_packets=current
                else:previous_notifications=current
            if guardians:
                guardian_captures+=1;guardian_payloads+=len(guardians)
                if first_guardian is None:first_guardian=dict(frame=frame_index,stage_index=stage_index,count=len(guardians));negative=S.owner_negative_checks(raw,want,read_static)
                for owner in guardians:
                    identity=(owner['ability_pointer'],owner['header_pointer']);assert guardian_owners.get(owner['guid'],identity)==identity;guardian_owners[owner['guid']]=identity
            if kind=='stage':
                event=base.check_resource_transition(previous,raw,stage_kind,frame_index,clock,resource_deadline,resource_payloads)
                if event:
                    i=event['pickup_index'];a=previous_want['vectors']['pickups']['storage'][i][4:8];b=want['vectors']['pickups']['storage'][i][4:8]
                    assert a==b and all(type(v)is int for v in a)
                    event['expected_known_arrival_bytes_preserved']=a;resource_events.append(event);resource_deadline=event['next_deadline_bits']
                base.audit_additional(previous,raw,want,read_static)
                assert raw['stage_index']==stage_index and raw['projection']['now_bits']==clock
                assert raw['entry_index']==(1072 if stage_kind=='select'else S.ENTRIES[base.STAGES.index(stage_kind)])
                if stage_kind=='select':
                    selected=fixture['actions'][action_index]['index'];cards=previous['projection']['candidates']
                    assert previous['projection']['phase2587']==2 and raw['input_index']==selected
                    selection=dict(frame=frame_index,action_index=action_index,index=selected,card=cards[selected],phase_after=raw['projection']['phase2587']);selections.append(selection)
                    if len(selections)==4:
                        assert selection['card']['ability_id']=='battle_shout'and selected==0 and frame_index==379
                        fourth_select=selection;battle=next(bytes.fromhex(x)for x in raw['projection']['owned_records_hex']if word(bytes.fromhex(x),0)==5467956)
                        assert word(battle,8)==B(.5)
                if stage_kind=='player'and fourth_select:
                    prior=[bytes.fromhex(x)for x in previous['projection']['owned_records_hex']];current=[bytes.fromhex(x)for x in raw['projection']['owned_records_hex']]
                    bi=next(i for i,x in enumerate(prior)if word(x,0)==5467956);a,b=prior[bi],current[bi]
                    remaining=sub(word(a,8),fixture['actions'][action_index]['dt_bits']);battle_tick_count+=1
                    assert a[:8]+a[12:]==b[:8]+b[12:]
                    if F(remaining)>0:assert word(b,8)==remaining
                    else:
                        cd=mul(mul(mul(mul(word(battle_definition,52),0x3fb33333),word(a,16)),word(a,56)),raw['projection']['derived_bits']['1544']);cd=cd if F(cd)>.25 else B(.25)
                        assert word(b,8)==cd
                        duration=mul(mul(mul(word(battle_definition,68),0x3fb33333),word(a,28)),word(a,68));duration=duration if F(duration)>.1 else B(.1)
                        active=[bytes.fromhex(x)for x in raw['vectors']['live32']['storage'][:raw['vectors']['live32']['count']]]
                        buff=next(x for x in active if word(x,8)==8 and word(x,20)==6673)
                        assert buff[:8]==bytes(8)and word(buff,12)==mul(word(a,76),word(battle_definition,4))and word(buff,24)==add(clock,duration)and word(buff,28)==0
                        if first_battle is None:first_battle=dict(frame=frame_index,stage_index=stage_index,player_ticks_since_selection=battle_tick_count,clock_bits=clock,remaining_cooldown_bits=word(b,8),live_record_hex=buff.hex())
                    battle_countdowns.append(dict(frame=frame_index,remaining_bits=word(b,8)))
                demo.observe(previous,raw,fixture['actions'][action_index])
                path=raw['projection']['distance_map']
                if path is not None:
                    for key,value in distance.items():assert path[key]==value
                stage_index+=1
            previous=raw;previous_want=want;last=raw
        if kind=='opening':
            assert any('The Defias Uprising — survive the onslaught!'.encode()in bytes.fromhex(x)for x in raw['projection']['banner150_packets'])
            base.EXTRA['initial_banner_subtitle_verified']+=1
        if kind=='case_end':
            assert raw['boundary']is None and raw['host_calls']==[]and raw['stage_count']==10506 and raw['locale_writes']==0 and raw['locale_after']==locale
            for call in raw['calls']:assert call['stack_after']==1048576
            calls=[x for x in raw['calls']if x['role']!='original_allocator'];assert len(calls)==10508 and all(x['returned']for x in calls)
        if(line_index+1)%500==0:
            progress=dict(records=line_index+1,stages=stage_index,seconds=time.monotonic()-began);save(out/'progress.json',progress);print(json.dumps(progress),flush=True)
    assert decoder.record_index==11260 and stage_index==10506 and len(selections)==6 and next(expected,None)is None
    cas=decoder.finish(runtime['capture_cas']);assert cas==report['capture_cas_verification']
    assert cas['records']==11260 and cas['logical_bytes']==5311244307
    expected_receipt=expected_reader.receipt()
    assert(expected_receipt['records'],expected_receipt['uncompressed_bytes'],expected_receipt['uncompressed_sha256'])==(regen['records'],regen['bytes'],regen['sha256'])
    assert expected_receipt['file_sha256']==regenerated['captured_expectation_sha256']==sha(capture/'stage-expectations.jsonl.gz')
    assert expected_reader.bytes==fixture['expected_uncompressed_bytes']==666746759
    assert len(resource_events)==len(clock_crossings)==1 and resource_events[0]['frame']==400 and resource_events[0]['stage_index']==5615
    assert runtime['schema_version']==5 and runtime['output_protocol']=='bounded_stage_cas_jsonl_gzip'and runtime['budgets']==runtime['capture_cas']['limits']
    limits=runtime['budgets'];assert limits['logical_record_bytes']==2097152 and limits['logical_output_bytes']==8589934592 and limits['unique_blob_bytes']==536870912 and limits['blob_bytes']==16777216 and limits['blob_files']==65536 and limits['compressed_output_bytes']==268435456 and limits['owned_deadline_seconds']==180
    assert runtime['capture_cas']['compressed_bytes']==len(compressed)and runtime['capture_cas']['compressed_sha256']==hashlib.sha256(compressed).hexdigest()
    assert runtime['memory_page_cap']==4096 and runtime['peak_memory_bytes']<=268435456 and runtime['js_heap_cap_mib']==512 and runtime['denied_imports']==878 and runtime['host_imports_throw']is True
    assert all(maximum[x]==0 for x in S.EMPTY_DOMAINS)and first_battle['player_ticks_since_selection']==6
    reconciled=sum(counts[k]for k in('strict_record_bytes','projection_leaves','vector_shape_fields','stage_identity_leaves'))
    assert reconciled==report['comparison']['compared_leaves']and counts['unknown_cells']==report['comparison']['declared_unknown_cells']
    assert counts['unwritten_pickup_arrival_words']==report['comparison']['unwritten_pickup_arrivals']and counts['verified_opaque_pickup_amount_words']==report['comparison']['verified_opaque_pickup_amounts']
    assert base.BINDER.report()==report['pickup_address_proof']
    assert base.EXTRA['growth_events']==6 and base.EXTRA['wave_events']==base.EXTRA['supply_events']==base.EXTRA['initial_banner_subtitle_verified']==1
    terminal=load(capture/'process-terminal.json');owned=load(capture/'owned-process.json')
    assert terminal['exit_code']==0 and not terminal['deadline_exceeded']and owned['deadline_seconds']==180
    assert terminal['seconds']==report['original_process']['seconds']<180 and terminal['pid']==terminal['pgid']==owned['pid']==3527
    assert S.missing(terminal['pid'])and S.missing(terminal['pgid'],True)and sha(Path(owned['command'][0]))==NODE_SHA
    assert(capture/'stderr.log').stat().st_size==0 and load(directory/'differences.json')==[]
    prior_failure=load(directory/'prior-reader-failure.json')
    assert prior_failure['compared_stages']==0 and prior_failure['capture_parent_exit_code']==1 and prior_failure['original_wasm_process_exit_code']==0 and prior_failure['captured_records']==11260
    reread_owner=ROOT/'evidence/opening750-fragment-recomparison-owned-20261101T213904.135799Z'
    reread_terminal=load(reread_owner/'process-terminal.json');reread_process=load(reread_owner/'process.json')
    assert sha(reread_owner/'process-terminal.json')=='23707bc25f6d7b2f775d48a83510cb424abf45b1cfeb59589d90637a2fc41dd2'
    assert reread_terminal['exit_code']==0 and reread_terminal['error']is None and reread_terminal['seconds']<360
    assert reread_terminal['pid']==reread_terminal['pgid']==reread_process['pid']==58721
    assert reread_process['deadline_seconds']==360 and S.missing(58721)and S.missing(58721,True)
    old_owner=ROOT/'evidence/opening750-recomparison-owned-20261101T211808.938114Z'
    old_terminal=load(old_owner/'process-terminal.json')
    assert old_terminal['pid']==22550 and old_terminal['exit_code']==-15 and old_terminal['seconds']>=360
    assert old_terminal['error'].startswith('TimeoutExpired')and S.missing(22550)and S.missing(22550,True)
    for name,digest in sources.items():assert sha(source/name)==digest==sha(ROOT/name),name
    for name,digest in captured.items():assert sha(old_source/name)==digest,name
    for name,digest in binding['capture_artifacts_before'].items():assert sha(capture/name)==digest,name
    for name,digest in reviewer_hashes.items():assert sha(ROOT/name)==digest==sha(out/'reviewer-source-snapshot'/name),name
    save(out/'static-image-reads.json',read_static.proofs)
    result=dict(status='passed_scoped_read_only_review',version='0.135.1',actual_build='90898d5e3',
        comparison=str(directory/'comparison.json'),comparison_sha256=args.comparison_sha,capture_directory=str(capture),
        source_files=111,captured_source_files=110,production_files=95,current_and_frozen_sources_verified=True,
        only_decoder_changed=report['only_decoder_changed'],reviewer_script_sha256=sha(Path(__file__)),
        reviewer_sources=reviewer_hashes,
        transport=dict(source=str(decoder_path),sha256=decoder_sha,private_decoder_used=False,codec_review=str(args.codec_review),codec_review_sha256=args.codec_sha,negative_cases=28,full_finish=cas),
        stream_record_counts=dict(records),expected_stream=expected_receipt,regenerated_expectations_independently_hashed=regen,
        comparison_counts=dict(counts),reconciled_known_leaves=reconciled,nonexport_sections_identical=True,
        full_declared_projection_recompared=True,omitted_payload_max_counts={x:maximum[x]for x in S.EMPTY_DOMAINS},observed_vector_max_counts=dict(maximum),
        first_guardian=first_guardian,guardian_distinct_GUIDs=sorted(guardian_owners),guardian_owner_captures=guardian_captures,guardian_payload_comparisons=guardian_payloads,guardian_corruption_checks=negative,
        selections=selections,battle_first_actual_buff=first_battle,battle_player_countdown=battle_countdowns,
        demo=demo.report(),demo_source_guard_checks=guards,npc_Aura_parser_selfchecks=parser_checks,
        independent_Dijkstra=distance,world_context=world_context,final_progression=last['projection']['progression'],final_gold=last['projection']['gold'],
        observed_packet_max=packet_max,resource_events=resource_events,resource_context='None for mixed resource consumer; no nearby3..5 natural consumption in this stationary trajectory.',
        all150_payloads_and_declared_GUID_actor169_and_shape_selected_NPC_Aura169_compared=True,other_packet_payload_semantics_claimed_compared=False,
        pickup_address_proof=base.BINDER.report(),independent_growth_and_wave_supply_checks=dict(base.EXTRA),independent_growth_events=base.GROWTH,independent_wave_supply_events=base.WITNESSES,
        component_review_dependencies=base.COMPONENT_REVIEWS+dependencies,opaque_negative_checks=base.opaque_negative_checks(),
        exact_known_mask_cache=base.mask_descriptor.cache_info()._asdict(),exact_packet_item_cache=base.packet_item.cache_info()._asdict(),
        static_image_reads_sha256=sha(out/'static-image-reads.json'),original_process_terminal=terminal,original_Node_seconds=terminal['seconds'],
        parent_reader_failure_preserved=prior_failure,new_original_executions=0,new_original_cases=0,new_original_entry_calls=0,
        completed_recomparison_process=dict(terminal=reread_terminal,terminal_sha256=sha(reread_owner/'process-terminal.json'),
            process_sha256=sha(reread_owner/'process.json')),
        historical_partial_recomparison_timeout=dict(terminal=old_terminal,terminal_sha256=sha(old_owner/'process-terminal.json'),
            stages_observed_before_timeout=8000,accepted_complete=False),
        referenced_original_executions=1,referenced_original_entry_calls=10508,original_model_or_checker_executed_by_reviewer=False,
        full880_frames=0,native_Windows_execution=False,playable_replacement=False,
        scope='One human warrior seed0/navFalse stationary750 controlled14-tail frames, real6730+1089, original initialized snapshot, independent preparsed world, externalf32 G2352 clock. Recomparison of the same capture, not a fresh second original run.',
        limitations=['No full880/native/fullgame/latest138 gameplay-flow acceptance.','Only declared projections/known physical bytes and the listed wire shapes are semantically compared.','Unknown/unwritten storage, allocator addresses, unsupported status/proc/multiplayer/UI remain explicit.','Independent cast and AI component reviews are dependencies; AI implementation authored by this reviewer.'],
        elapsed_seconds=time.monotonic()-began)
    assert result['elapsed_seconds']<420
    save(out/'review.json',result)
    print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=result['status'],seconds=result['elapsed_seconds'],counts=dict(counts),demo=dict(casts=demo.casts,expirations=demo.expirations))),flush=True)


if __name__=='__main__':
    main()
