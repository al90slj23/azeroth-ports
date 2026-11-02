#!/usr/bin/env python3
"""Bounded static source proof of empty callback vectors and fatal fields."""
from datetime import datetime,timezone
import hashlib,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
SOURCE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
def sha(path):
 h=hashlib.sha256()
 with path.open('rb')as stream:
  for block in iter(lambda:stream.read(1048576),b''):h.update(block)
 return h.hexdigest()
def main():
 assert sha(SOURCE)==SOURCE_SHA
 before=sha(Path(__file__))
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('callback-source-owner135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
 windows={9868:[('zero_headers_and_empty_ranked_input',1,58),('ranked_queue_empty',982,1034),('flag164_guard',1164,1198),('five_header_return',1505,1542)],
  25765:[('ranked_input_and_gear_set_guard',1,62),('gear_no_set_tag',138,170),('profile_headers_return',503,542)],
  20363:[('zero_counts_and_19slots',1,84),('slot_loop_end',155,176),('no_eight_piece_set',179,291)],
  1976:[('zero_lookup_unsigned_range_miss',449,460),('zero_lookup_not_found',1338,1345)],
  1560:[('source_producer',194,206),('fatal_lives_zero',807,824),('left_flag_zero',1164,1176),('header_copy',1246,1278),('empty_ring_constructor',988,1000),('empty_event_sort',2436,2451),('final_Game_copy',2738,2758)],
  1072:[('new_ability_reads_sources',486,515),('new_ability_reorders_owned',597,617),('ordinary_upgrade',811,978),('lives_trait_variant',687,730),('common_stats_finish',7056,7070)],
  1512:[('items_count_guard',40,68),('event_definition_count_guard',351,368)],
  24129:[('owned_priority_input',1,33),('owned_priority_output',463,516)],
  4600:[('late_Aura_continuation',734,755)]}
 db=sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row
 functions={}
 with(PROFILE/'official-0.135.1-full.wat').open('rb')as wat,SOURCE.open('rb')as binary:
  for index,selections in windows.items():
   row=dict(db.execute('select * from functions where idx=?',(index,)).fetchone());wat.seek(row['wat_start']);text=wat.read(row['wat_end']-row['wat_start']);lines=text.decode().splitlines();assert lines[0].startswith(f'  (func (;{index};)')
   binary.seek(row['body_start']);body=binary.read(row['body_end']-row['body_start']);(out/f'{index}.wat').write_bytes(text)
   accesses=[dict(operation=v['operation'],offset=v['field_offset'],line=v['wat_line']-row['wat_line']+1)for v in db.execute('select * from memops where function_idx=? and field_offset between 2024 and 2056 order by wat_offset',(index,))]
   functions[str(index)]=dict(**row,body_sha256=hashlib.sha256(body).hexdigest(),wat_sha256=hashlib.sha256(text).hexdigest(),header_memops=accesses,windows={label:[dict(line=j+1,instruction=lines[j].strip())for j in range(a-1,min(b,len(lines)))]for label,a,b in selections})
 assert all('store'not in row['operation']for row in functions['1512']['header_memops'])
 proof=dict(version='0.135.1',original_sha256=SOURCE_SHA,script_sha256=before,original_calls=0,full_profile_scan=False,sqlite_mode='ro',functions=functions,
  input_domain=dict(named='explicit_blank376_research_selected_profile',ranked_count160=0,ranked_flag164=0,equipped_item_ids260_332=[0]*19),
  source_chain=['1560 calls25765(outSP24,P376)','25765 calls9868(outSP20,P+152)','9868 explicit five Vec headers0/4/0;P160count0 skipsrankedinput;P164flag0 skipsrewrite','1976(0) firsttable default→unsigned0-1<99999 false→0<100000 true→notfound at1341..1344','20363 all19 missingIDs leavesclasssetcounts0 andreturnstag2','25765 tag2 selects no gear extra effects;fiveheaders copied to1560SP24..83','1560 copies60B toscratch2112..2171 then Game=scratch+88, givingG2024..2083','empty eventvector34902 sortcount0 noentries;1512 onlyreads sourceheaders'],
  outputs=dict(items8=dict(capacity_offset=2024,pointer_offset=2028,count_offset=2032,capacity=0,pointer_sentinel=4,count=0),eventdef36=dict(capacity_offset=2048,pointer_offset=2052,count_offset=2056,capacity=0,pointer_sentinel=4,count=0),incoming48=dict(capacity_offset=968,pointer_offset=972,head_offset=976,count_offset=980,capacity=0,pointer_sentinel=4,head=0,count=0),lives1632=0,left2567=0),
  selection_preservation=['1072 kind0 upgrade changesonlyexistingowned80 through25368 anditslocalwrites thencommoncontinuation','ordinarynewskill readsability20modifiers via26967,appendsowned80 and24129 reordersownedpriorities;doesnotrebuildthetwo callbackvectors','goldbranch28796 changescurrency;common1512/4600 readcallbackvectors','Equipment/trait/summon/item orkind1/2 pathsareexcluded;2435 andnonemptyprofile/equipment requiretheir realproducer'],
  fatal_field_rules=['1560 SP1720 i32store0→G1632 afterSP88 basecopy','1560 SP2655 i32store8 0→G2567 afterSP88 basecopy','1512 has no1632/2567write;normalupgrade/newskill/gold domain excludes1072 separatetag16 trait branch thatcanaddlives'],
  boundaries=['No natural6730 App/account/profile/menu producer claimed;nonblankrealaccountrequiresrealinputs','Findingheaderincrementsdoesnotreconstructnonemptyequipment/talentproducer','Staticproof isseparatefromfresh1560/controlled1072 differential','Initiallives0 isnot aclaimthatunrestoredfuturetrait/revival paths cannotchangeit'])
 path=out/'proof.json';path.write_text(json.dumps(proof,indent=2)+'\n');assert sha(Path(__file__))==before
 print(json.dumps(dict(directory=str(out),proof_sha256=sha(path),functions=len(functions),original_calls=0)))
if __name__=='__main__':main()
