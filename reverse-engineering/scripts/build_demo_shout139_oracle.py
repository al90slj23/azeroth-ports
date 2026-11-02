#!/usr/bin/env python3
"""Bind direct1160 andweakmerge21553/currentNPC_Aura4593/AIexpiry source."""
from build_thunder_clap139_oracle import build as base_build
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,sha,save,original,private_exports,function_proof,static_reader

def build(out):
 m=base_build(out);raw,identity,ranges=original();ids={21553,15556,68886,15962,6619,51773,925,30179,29237,1076,56864,59230,66546,1600,1093,1238,25511};proof,texts=function_proof(raw,identity,ranges,ids,out/'static');m['functions'].update(proof);read=static_reader(raw,identity);demo=read(5883180,88);assert demo[84]==2 and int.from_bytes(demo[:4],'little')==11 and int.from_bytes(demo[44:48],'little')==1160
 # No body is replaced; new exports are only research entrypoints.
 added=m['added_exports']+[('research139_demo_ai925',0,925),('research139_demo_merge21553',0,21553)];name='demo-shout139-original-exports.wasm';(out/name).write_bytes(private_exports(raw,identity,added));m.update(module_file=name,module_sha256=sha(out/name),added_exports=added,demo_shout88_hex=demo.hex(),static_reads={**m['static_reads'],**read.proof},scope='Fullcurrent922exec2/effect11/1160 directcomponent;21553finite16Bhelper;925weakAuraexpiry andcontacts separatetargets;no fullmain')
 save(out/'manifest.json',m);return m
