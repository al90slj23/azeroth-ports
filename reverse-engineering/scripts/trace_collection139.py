#!/usr/bin/env python3
"""Bound current139 collect/erase/move/currency callees; static only."""
from datetime import datetime,timezone
import sqlite3
from incoming139_tools import ROOT,PROFILE,SOURCE_SHA,original,function_proof,static_reader,save,sha

def main():
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('collection139-static-%Y%m%dT%H%M%S.%fZ');out.mkdir();raw,identity,ranges=original();ids={1600,2890,32070,27650,29338,4677,86979,88159,20958,10261,15962,46462,10804,51773,66558};proof,texts=function_proof(raw,identity,ranges,ids,out)
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:calls={str(i):list(db.execute('select callee,wat_line from calls where caller=?',(i,)))for i in ids}
 assert 'i64.store offset=2196 align=4'in texts[1600]and'i64.store offset=2204 align=4'in texts[1600]
 assert 'i32.const 2\n          i32.eq\n          br_if 0 (;@3;)'in texts[32070]and'call 81894\n        unreachable'in texts[32070]
 result=dict(version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,script_sha256=sha(__file__),functions=proof,direct_calls=calls,empty_claim_constructor=dict(Game_base88=True,SP2196_i64_34359738368='G2108cap0/G2112ptr8',SP2204_i64_0='G2116count0'),marker2='32070 partialcompaction/count-- then@3→81894unreachable;not skip170 normalreturn',original_executions=0,unknowns=['crosslevel4677withnonemptyworld','networktransportafterlocalmode1or2forwardqueues','kind2andotherresources','nonemptyauxiliaryGUIDdestructionowner'])
 save(out/'trace.json',result);print(str(out));print(sha(out/'trace.json'))
if __name__=='__main__':main()
