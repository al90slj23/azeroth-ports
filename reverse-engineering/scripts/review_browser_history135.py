#!/usr/bin/env python3
"""Independent read-only real-resource/history review; no browser/WASM execution."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import argparse,hashlib,importlib.util,json,os,struct,sys
sys.dont_write_bytecode=True
import review_incoming_history135 as H

ROOT=H.ROOT
DEFAULT='full0135-oracle-20261101T093136.935919Z'
ALLOWED={0,521,523,643,644,645,658,659,660,735,804,827,835,845,848,851,877}
GLUE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/official-wenilla.js'
GLUE_SHA='636bcd5acba01a31c4b40234969243e964cc8e7e7610adf0817e3494d92c9945'
ASSETS={'__index':'1ca98562aee4c460c4eb46d20f1bf0facdff0fb0bc1f4b73814b9cfea5c4aad8',
 'dbfilesclient/spell.dbc':'913d01c0376d88310ed4a44ea1115f30fd8be15af64ce304f4f17b6bc51cf15b',
 'dbfilesclient/spellicon.dbc':'938e8c333fe914938994fc331c04655d7eb5719bc2d1b29eaf5fad4239abdfdc'}


def dbc(data):
    assert data[:4]==b'WDBC';rows,fields,stride,strings=struct.unpack_from('<4I',data,4)
    end=20+rows*stride;assert stride==4*fields and end+strings==len(data) and data[end]==0
    def word(j,col):assert 0<=j<rows and 0<=col<fields;return H.u(data,20+j*stride+col*4)
    def string(offset):
        assert 0<=offset<strings;zero=data.find(b'\0',end+offset);assert zero!=-1
        return data[end+offset:zero].decode('utf-8')
    return rows,fields,stride,word,string,lambda j:data[20+j*stride:20+(j+1)*stride].hex()


def metadata(root):
    sr,sf,ss,sw,st,sraw=dbc((root/'dbfilesclient/spell.dbc').read_bytes())
    ir,iff,isz,iw,it,iraw=dbc((root/'dbfilesclient/spellicon.dbc').read_bytes())
    assert (sf,ss,iff,isz)==(173,692,2,8);result={}
    for sid in (5568,28783,28308):
        matches=[j for j in range(sr) if sw(j,0)==sid];assert len(matches)==1;j=matches[0];iid=sw(j,117)
        matches=[k for k in range(ir) if iw(k,0)==iid];assert len(matches)==1;k=matches[0]
        result[str(sid)]=dict(spell_id=sid,spell_row=j,icon_id=iid,icon_row=k,name=st(sw(j,120)),icon=it(iw(k,1)),spell_record_hex=sraw(j),icon_record_hex=iraw(k))
    return result


def imports(raw,ranges):
    sec=next(x for x in ranges if x[0]==2);n,p=H.uint(raw,sec[2]);rows=[]
    for i in range(n):
        length,p=H.uint(raw,p);module=raw[p:p+length].decode();p+=length
        length,p=H.uint(raw,p);name=raw[p:p+length].decode();p+=length
        assert raw[p]==0;p+=1;typ,p=H.uint(raw,p)
        rows.append(dict(id=i,module=module,name=name,type_index=typ,allowed=i in ALLOWED))
    assert p==sec[3] and n==878;return rows


def independent_history(c,observations,names,counts):
    cap,head,length=c['capacity'],c['head'],c['count'];data=[list(bytes.fromhex(x))for x in c['storage']]
    labels=[('', '', '')for _ in data];previous=None;s=dict(c['input'])
    assert s['phase_2579']==1 and s['mode_2574']==0 and s['protection_2568']==0 and not s['units'] and not s['buffs'] and not s['modifiers']
    assert s['armor_1392_bits']==s['nearby_reduction_1444_bits']==s['reserve_768_bits']==s['shield_source_1344']==0
    assert len(c['ops'])==len(observations)
    for op,observed in zip(c['ops'],observations):
        assert set(op)=={'amount_bits','category','critical','now_bits','spell_id'} and op['category']in(1,2) and str(op['spell_id'])in names
        counts['spell_'+str(op['spell_id'])]+=1;before_cap=cap;amount=op['amount_bits'];absorbed=0;shield=s['shield_1532_bits']
        if H.ff(shield)>0:
            absorbed=shield if H.ff(shield)<H.ff(amount) else amount;s['shield_1532_bits']=H.fsub(shield,absorbed)
            x=H.fsub(s['barrier_1536_bits'],absorbed);s['barrier_1536_bits']=x if H.ff(x)>0 else 0
            s['shield_source_remaining_1348_bits']=H.fsub(s['shield_source_remaining_1348_bits'],absorbed)
            s['absorbed_740_bits']=H.fadd(absorbed,s['absorbed_740_bits'])
            s['maximum_shield_744_bits']=shield if H.ff(shield)>H.ff(s['maximum_shield_744_bits']) else s['maximum_shield_744_bits']
            if H.ff(s['shield_1532_bits'])<=0:
                for key in ('barrier_1536_bits','shield_source_remaining_1348_bits','absorbed_740_bits','maximum_shield_744_bits'):s[key]=0
            amount=H.fsub(amount,absorbed)
        hp_at_append=H.fsub(s['hp_1528_bits'],amount);s['hp_1528_bits']=hp_at_append;s['incoming_total_992']+=H.ff(amount);s['last_hit_1648_bits']=op['now_bits']
        cutoff=H.ff(H.fadd(op['now_bits'],0xc1200000))
        while length and (length>399 or H.ff(H.u(bytes(data[head][24:28]),0))<cutoff):
            counts['pruned_for_count'if length>399 else'pruned_for_time']+=1;head=(head+1)%cap;length-=1
        if length==cap:
            old=cap;cap=max(4,cap*2);data.extend([[None]*48 for _ in range(cap-old)]);labels.extend([None]*(cap-old))
            if head>old-length:
                prefix=old-head;suffix=length-prefix
                if prefix>suffix and cap-old>=suffix:
                    data[old:old+suffix]=[x[:]for x in data[:suffix]];labels[old:old+suffix]=labels[:suffix];counts['grow_move_low_segment']+=1
                else:
                    destination=cap-prefix;data[destination:cap]=[x[:]for x in data[head:old]];labels[destination:cap]=labels[head:old]
                    head=destination;counts['grow_move_high_segment']+=1;counts['grow_tie']+=int(prefix==suffix)
            else:counts['grow_nonwrapped']+=1
        slot=(head+length)%cap;row=data[slot][:];m=names[str(op['spell_id'])];new_labels=('',m['name'],m['icon'])
        row[:46]=struct.pack('<6I5I2B',1,0,0,len(m['name'].encode()),0,len(m['icon'].encode()),op['now_bits'],amount,absorbed,hp_at_append,s['max_hp_bits'],4,int(op['category']==2))
        row[8:12]=row[16:20]=[None]*4;data[slot]=list(row);labels[slot]=new_labels;length+=1
        if s['minimum_one_2578']and H.ff(s['hp_1528_bits'])<1:s['hp_1528_bits']=0x3f800000;counts['minimum_one_after_history']+=1
        assert observed['header']==dict(capacity=cap,head=head,count=length);active={(head+j)%cap for j in range(length)}
        for j,(known,actualhex)in enumerate(zip(data,observed['storage'])):
            actual=bytes.fromhex(actualhex);assert len(actual)==48
            for offset,(want,got)in enumerate(zip(known,actual)):
                if want is None:
                    if offset in(*range(8,12),*range(16,20))and labels[j]and labels[j][1]:
                        counts['resource_pointer_bytes']+=1;counts['resource_pointer_nonzero']+=bool(got)
                    else:
                        assert j not in active or offset in(46,47);counts['allocator_unwritten_bytes']+=1;counts['allocator_unwritten_nonzero']+=bool(got)
                else:
                    assert want==got,(c['id'],counts['stages'],j,offset,want,got);counts['strict_backing_bytes']+=1
                    if offset in(46,47):counts['strict_old_padding_bytes']+=1
            counts['backing_bytes']+=48
        assert len(observed['storage'])==cap and len(observed['active'])==length
        for j,row in enumerate(observed['active']):
            slot=(head+j)%cap;assert row['slot']==slot and row['raw_hex']==observed['storage'][slot]and tuple(row['strings'])==labels[slot]
            counts['active_rows']+=1
        scalar={key:s[key]for key in H.OFFSETS};scalar.update(incoming_total_992_bits=struct.pack('>d',s['incoming_total_992']).hex(),phase_2579=1)
        assert observed['scalar']==scalar
        game=bytes.fromhex(observed['raw_game2592_hex']);assert len(game)==2592 and[H.u(game,o)for o in(968,976,980)]==[cap,head,length]
        assert H.u(game,972)==observed['history_pointer']
        for key,offset in H.OFFSETS.items():assert H.u(game,offset)==scalar[key]
        assert struct.unpack_from('<Q',game,992)[0]==int(scalar['incoming_total_992_bits'],16)
        before=bytearray(previous if previous is not None else H.initial_game(c,game));H.put(before,2352,op['now_bits'])
        delta=[[o,H.u(game,o)]for o in range(0,2592,4)if H.u(game,o)!=H.u(before,o)];actual=observed['game_changes']
        if previous is None and c['capacity']and cap!=before_cap:
            delta=[x for x in delta if x[0]!=972];actual=[x for x in actual if x[0]!=972];counts['initial_old_heap_pointer_words_observed']+=1
        assert delta==actual;previous=game;counts['rawG_bytes']+=2592
        pm=bytes.fromhex(observed['message_metadata_backing_hex']);nm=bytes.fromhex(observed['notification_metadata_backing_hex'])
        assert len(pm)==H.u(game,1880)*16 and len(nm)==H.u(game,1892)*12
        assert len(observed['packets'])==H.u(game,1888)and len(observed['notifications'])==H.u(game,1900)
        for j,packet in enumerate(observed['packets']):assert packet['capacity']==H.u(pm,j*16)and len(bytes.fromhex(packet['raw_hex']))==H.u(pm,j*16+8)and packet['opcode']==struct.unpack_from('<H',pm,j*16+12)[0]
        for j,n in enumerate(observed['notifications']):assert n['capacity']==H.u(nm,j*12)and len(bytes.fromhex(n['raw_hex']))==H.u(nm,j*12+8)
        counts['stages']+=1
    counts['cases']+=1


def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',default=DEFAULT);args=p.parse_args();batch=Path(args.batch)
    batch=batch if batch.is_absolute()else ROOT/'evidence'/batch
    rp=batch/'browser-history135-comparison.json';receipt=json.loads(rp.read_text());assert receipt['phase']=='full'and receipt['differences']==0
    frozen=receipt['source_before'];assert frozen==receipt['source_after'];snap=batch/'source-snapshot'
    for name,digest in frozen.items():assert H.sha(snap/name)==H.sha(ROOT/name)==digest
    core=H.closure(snap,['incoming_history135.py','incoming135.py']);assert set(core)<=set(frozen)
    for name,digest in receipt['artifacts'].items():assert H.sha(batch/name)==digest
    original=H.ORIGINAL.read_bytes();assert hashlib.sha256(original).hexdigest()==receipt['original_sha256']==H.ORIGINAL_SHA
    config=json.loads((batch/'browser-history135-config.json').read_text());manifest=json.loads((batch/'manifest.json').read_text());module=Path(config['wasm_path']).read_bytes()
    assert H.sha(Path(config['chrome_path']))==config['chrome_sha256']
    command=receipt['process']['command'];assert command==[str(ROOT/'.toolchain/runtime/node_modules/node/bin/node'),'--max-old-space-size=512',str(ROOT/'scripts/run_browser_history135.mjs'),str(batch/'browser-history135-config.json')]
    assert H.sha(Path(command[0]))=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
    assert H.sha(Path(config['wasm_path']))==config['wasm_sha256']==manifest['module_sha256']
    osr=H.section_ranges(original);nsr=H.section_ranges(module);assert[x[0]for x in osr]==[x[0]for x in nsr]and 8 not in[x[0]for x in osr]
    for a,b in zip(osr,nsr):
        if a[0]!=7:assert original[a[1]:a[3]]==module[b[1]:b[3]]
    assert H.exports(module,nsr)==H.exports(original,osr)+[['research135_incoming_damage',0,1073]]
    assert H.signature(original,osr,1073)==('7f7d7e7f7f7f','')
    assert config['imports']==imports(original,osr)and sum(x['allowed']for x in config['imports'])==17
    assert config['memory_cap_bytes']==128*1024*1024 and config['deadline_seconds']==60
    assert H.sha(GLUE)==GLUE_SHA and config['official_glue_sha256']==GLUE_SHA
    bridge=Path(config['glue_path']).read_bytes();assert bridge[:len(GLUE.read_bytes())]==GLUE.read_bytes()and H.sha(Path(config['glue_path']))==config['glue_sha256']
    assert config['assets']==ASSETS and all(H.sha(Path(config['asset_root'])/name)==digest for name,digest in ASSETS.items())
    names=metadata(Path(config['asset_root']));assert names==receipt['independent_metadata']==json.loads((batch/'browser-history135-independent-metadata.json').read_text())
    evidence=receipt['metadata_instruction_evidence'];assert H.sha(ROOT/evidence['path'])==evidence['wat_sha256'];a,b=H.body(original,osr,4546)
    assert hashlib.sha256(original[a:b]).hexdigest()==evidence['body_sha256']=='073d44f43e2a1a3ebb31ad697f20516f07128a866eb8c7c40c2eb1fbcca2e00f'
    cases=json.loads((batch/'browser-history135-fixtures.json').read_text());inputs=json.loads(Path(config['fixtures_path']).read_text())
    assert Path(config['fixtures_path'])==batch/'browser-history135-inputs.json'and H.sha(Path(config['fixtures_path']))==config['fixtures_sha256']
    assert len(cases)==len(inputs)==receipt['cases']and all(set(c)==H.INPUT_KEYS for c in inputs)
    assert [{k:c[k]for k in receipt['input_exact_keys']}for c in cases]==inputs and not receipt['input_contains_expected']
    assert all(m['name']not in json.dumps(config)for m in names.values())
    for key in list(sys.modules):
        if key.startswith('core_spec')or key in('check_incoming_history135','source_closure135','build_full135_oracle','build_upgrade134_oracle'):del sys.modules[key]
    sys.path.insert(0,str(snap/'scripts'));spec=importlib.util.spec_from_file_location('review_frozen_browser_history_checker',snap/'scripts/check_browser_history135.py');author=importlib.util.module_from_spec(spec);spec.loader.exec_module(author)
    assert bridge[len(GLUE.read_bytes()):]==author.BRIDGE_APPEND.encode()
    assert json.loads(json.dumps(author.corpus(names,False),allow_nan=False))==cases
    runtime=json.loads((batch/'browser-history135-runtime.json').read_text());assert runtime==receipt['runtime']and runtime['status']=='passed'and runtime['error']is None
    assert runtime['denied_other_import_count']==861 and runtime['allowed_resource_imports']==[x for x in config['imports']if x['allowed']]
    assert not runtime['blocked_requests']and not runtime['browser_errors']and not runtime['user_profile_used']and not runtime['user_tabs_used']and not runtime['external_network_permitted']
    assert not runtime['appstart_called']and not runtime['full_game_started']and not runtime['downloads_performed']and not runtime['user_saves_accessed']
    result=runtime['result'];assert result['cap_verified']and result['native_self']and result['native_xhr']and not result['local_storage_keys']and not result['indexeddb_databases']
    assert not result['appstart_exports_called']and not result['finalizer_called']and result['max_memory_bytes']<=config['memory_cap_bytes']
    data_requests=[x for x in runtime['requests']if x['path'].startswith('/data/')];assert len(data_requests)==len(cases)*3
    for name,digest in ASSETS.items():assert sum(x['path']=='/data/'+name and x['sha256']==digest and x['status']==200 for x in data_requests)==len(cases)
    assert all(x['url'].startswith('http://127.0.0.1:')and x['status']==200 for x in runtime['requests'])
    calls=result['entry_calls'];assert all(e['returned']and e['name']in('__wbindgen_malloc','research135_incoming_damage')for e in calls)
    assert[e['sequence']for e in calls]==list(range(len(calls)));assert all(x['allowed']and x['id']in ALLOWED for x in result['imports'])
    for c in cases:
        selected=[e for e in calls if e['case_id']==c['id']and e['name']=='research135_incoming_damage'];assert len(selected)==len(c['ops'])
        assert selected[0]['once_before']==0 and selected[0]['once_after']==3
        for op,e in zip(c['ops'],selected):assert e['args'][1:]==[H.ff(op['amount_bits']),'0',op['critical'],op['category'],op['spell_id']]
        assert all(e['once_before']==3 and e['once_after']==3 for e in selected[1:])
        for event in result['imports']:
            if event['case_id']==c['id']and event['id']!=851:assert event['entry_name']=='research135_incoming_damage'and event['entry_sequence']==selected[0]['sequence']
    counts=Counter();assert len(result['results'])==len(cases)
    for c,observed in zip(cases,result['results']):assert c['id']==observed['id'];independent_history(c,observed['stages'],names,counts)
    assert counts['stages']==receipt['stages']==37 and counts['cases']==receipt['cases']==9
    assert counts['backing_bytes']==counts['strict_backing_bytes']+counts['resource_pointer_bytes']+counts['allocator_unwritten_bytes']
    assert receipt['process']['exit_code']==0 and receipt['process']['outer_deadline_seconds']==120
    lifecycle=runtime['lifecycle'];terminal=next(x for x in lifecycle if x['event']=='browser_process_final');assert terminal['exit_code']==0 and terminal['signal_code']is None
    assert any(x['event']=='context_closed'for x in lifecycle)and any(x['event']=='http_server_closed'for x in lifecycle)
    missing={}
    for label,pid in(('node',receipt['process']['pid']),('browser',runtime['browser_pid'])):
        try:os.kill(pid,0);missing[label]=False
        except ProcessLookupError:missing[label]=True
    for name,digest in frozen.items():assert H.sha(snap/name)==H.sha(ROOT/name)==digest
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('browser-history0135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    script=Path(__file__);helper=ROOT/'scripts/review_incoming_history135.py';(out/'reviewer-source.py').write_bytes(script.read_bytes());(out/'reviewer-helper.py').write_bytes(helper.read_bytes())
    review=dict(status='passed_scoped_real_browser_history_review',receipt=str(rp.relative_to(ROOT)),receipt_sha256=H.sha(rp),source_files=len(frozen),core_closure=core,
        source_snapshots_verified=True,current_source_drift={},only_wasm_export_section_changed=True,original_exports_preserved=True,official_glue_prefix_unchanged=True,
        exact_real_DBC_metadata=names,metadata_columns=dict(spell_id=0,spell_name=120,spell_icon_id=117,icon_id=0,icon_string=1),
        comparison=dict(counts),allowed_imports=17,denied_imports=861,actual_import_calls=len(result['imports']),actual_import_names=len({x['id']for x in result['imports']}),
        resource_gets=len(data_requests),original1073_calls=37,fresh_instances=9,explicit_call_log=len(calls),max_memory_bytes=result['max_memory_bytes'],wasm_cap_bytes=config['memory_cap_bytes'],
        true_cold_Once_loaded_by_original1073=True,input_has_no_expected_metadata=True,expected_model_replayed_without_original=True,
        original_or_browser_reexecuted=False,author_sources_modified=False,process_exit0_verified=True,pids_missing_at_review=missing,
        reviewer_sha256=H.sha(script),helper_sha256=H.sha(helper),
        limitations=['Only48B history/scalars in declared no-unit/empty-proc/nonfatal/minimum-one domain;whole1073/registry/keyed/proc behavior not independently modeled.',
          'Source pointer1 strict; genuineDBC name/icon pointer addresses normalized but everyactive string and UTF8 byte length strict.',
          'New allocator-unwritten data remains unknown;oldpadding and all other known backing strict.',
          'Three realSpellIDs/English metadata only;not allDBC columns/locales or fullgame/world/headless integration.',
          'Appstart exclusion relies on no implicit start, explicit entry whitelist/bind-only/call log;not exhaustive proof ofeveryindirectcallee.',
          'First old history allocation pointer on growth absent from sidecar;rawG delta for that oldword remains observational.'])
    (out/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'directory':str(out),'review_sha256':H.sha(out/'review.json'),'counts':dict(counts)},indent=2))


if __name__=='__main__':main()
