#!/usr/bin/env python3
"""Final readonly source/input-fidelity adjudication of frozen healing v2.

Prior numeric receipts remain immutable. This reviewer reads evidence/source
only and never imports/executes an author module or original target.
"""
from pathlib import Path
import ast,hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[1]
NUMERIC=ROOT/'evidence/healing-hurtactor139-review-20261102T115849.005296Z'
NUMERIC_SHA='7cdd2ba7bb1e2cc12f25a4d976421099716594b841c8ad6e5fcf8c8687906d83'
HURT=ROOT/'evidence/hurtactor139-oracle-20261102T114019.166570Z'
HAND='853c2ecc932ac946586f6166f083295fb9b4eb522d07f87609f2082f70d385b5'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
    out=Path(sys.argv[1]).resolve();out.mkdir()
    assert sha(NUMERIC/'review/review.json')==NUMERIC_SHA and sha(HURT/'task-handoff.json')==HAND
    h=load(HURT/'task-handoff.json');n=load(NUMERIC/'review/review.json');assert n['original_executions']==n['author_production_checker_runner_builder_executions']==0
    for name,v in h['frozen_author_files'].items():assert sha(ROOT/name)==v
    findings=[]
    for stem in('healing','hurtactor'):
        runner=ROOT/f'scripts/run_{stem}139_oracle.mjs';checker=ROOT/f'scripts/check_{stem}139.py';text=runner.read_text();sites=[]
        for line,s in enumerate(text.splitlines(),1):
            if "call('1076',"not in s:continue
            a=s.index("call('1076',");b=s.index(');',a)+2;code=s[a:b];match=re.search(r',\s*(source|incomingSource)\s*,\s*0\s*,\s*0\s*,\s*1\s*\);$',code);assert match,code
            sites.append(dict(line=line,source=code,actual_param3_contact_flag=0,actual_param4_category=0,actual_param5_spell_id=1,actual_NPC_GUID=True))
        assert len(sites)==1
        tree=ast.parse(checker.read_text());models=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Call)and isinstance(node.func,ast.Name)and node.func.id=='resolve_prefix139':
                flag=next(k.value for k in node.keywords if k.arg=='contact_flag');assert isinstance(flag,ast.Constant)and flag.value==1;models.append(dict(line=node.lineno,source=ast.get_source_segment(checker.read_text(),node),modeled_contact_flag=1))
        assert len(models)==1
        findings.append(dict(runner=str(runner.relative_to(ROOT)),runner_sha256=sha(runner),checker=str(checker.relative_to(ROOT)),checker_sha256=sha(checker),original_callsite=sites[0],model_callsite=models[0],input_parameter_equal=False))
    result=dict(status='not_accepted_current139_v2_source_parameter_mismatch',numeric_projection_status='matched_with_independent_reference_but_not_formal_source_input_acceptance',reviewer='/root/growth139_world',author='/root/growth139_review',author_handoff_sha256=HAND,author_files=h['frozen_author_files'],reviewer_script_sha256=sha(Path(__file__)),numeric_receipt=dict(path=str(NUMERIC/'review/review.json'),sha256=NUMERIC_SHA,owned_terminal_path=str(NUMERIC/'owned-terminal.json'),owned_terminal_sha256=sha(NUMERIC/'owned-terminal.json'),reference_sha256=n['independent_reference_sha256'],source_sha256=n['reviewer_script_sha256'],counts=n['counts']),findings=findings,
        decision='Actual1076 contactFlag0/category0/spellID1 is not the model contactFlag1 input. Finite default empty-source HP/lastHit/key/heal totals matched,but that does not establish input fidelity or accept v2 as a completed reconstruction domain. Await newv3 matching inputs and freshformal5+4.',
        parameter_metadata1466=dict(regen=dict(param2_spell_id=0,param3_pointee_head=-1,param4_pointee_head=0,static_record=1592624),Leech=dict(param2_spell_id=0,param3_pointee_head=-2,param4_pointee_head=-1),validation='Currentcaller/28155/staticliteral bindingsonly;notdynamicargsampling.'),
        preserved=dict(prior_numeric_receipts_unchanged=True,author11_andrevision1_unchanged=True,original_failed_hurtactor_a0011_preserved=True,clock7_unchanged=True),
        scope=['Numericreferencecovered42full2123+9full1076+32full922 asstored observations;45prefixsetup/64emptyconsumersareseparate. Reviewercreated0neworiginalcalls.','27positiveRegen/28positiveLeech/42damageevents,cap/key22/28,f32order/sharedG960/G1016/semanticf64reasonTotals/Vec48nameicon matched inthosenumericprojections.','Incomingcategory/history/callback areoutsidev2comparison;contact0vs1canselectdifferentsemanticbranches. Numericcoincidenceisnotanacceptancesubstitute.','SourceSpellID/param3/param4metadataarestaticproofonly. No full2077physical96key/catalog/bucket/Vec448implementationorfull884/native/gameaccepted.'],
        reviewer_original_executions=0,reviewer_author_module_checker_runner_builder_executions=0,reviewer_original_target_calls=0,author_files_modified=False,requires_v3=True)
    save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=result['status'],findings=len(findings))))
if __name__=='__main__':main()
