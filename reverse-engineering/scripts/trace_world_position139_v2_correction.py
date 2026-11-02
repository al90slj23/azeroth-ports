#!/usr/bin/env python3
"""Read-only AST/callsite correction record; no model or original execution."""
import ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/world-position139-v2-oracle-20261102T042946.182486Z'
STATIC=ROOT/'evidence/world-position139-static-20261102T033613.062984Z'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fn(p,name):return next(x for x in ast.parse(p.read_text()).body if isinstance(x,ast.FunctionDef)and x.name==name)
class Names(ast.NodeTransformer):
 def visit_Name(self,n):
  n.id=n.id.removesuffix('V2');return n
old=ROOT/'reconstruction/core_spec/world_position139.py';new=ROOT/'reconstruction/core_spec/world_position139_v2.py'
def normalized(node):return ast.dump(Names().visit(node),include_attributes=False)
assert normalized(fn(old,'sample_spawn_position'))==normalized(fn(new,'sample_spawn_position'))
a,b=fn(old,'sample_random_position'),fn(new,'sample_random_position')
oldexpr='hypot_bits(dx, dy)';newexpr='sqrt_bits(f.add(f.mul(dx, dx), f.mul(dy, dy)))'
def distances(tree):return [x for x in ast.walk(tree)if isinstance(x,ast.Assign)and len(x.targets)==1 and isinstance(x.targets[0],ast.Name)and x.targets[0].id=='distance']
x,y=distances(a),distances(b);assert len(x)==len(y)==1
assert ast.unparse(x[0].value)==oldexpr and ast.unparse(y[0].value)==newexpr
x[0].value=ast.parse(newexpr,mode='eval').body
assert normalized(a)==normalized(b)
wat=STATIC/'13563.wat';lines=wat.read_text().splitlines();sqrtline=next(i for i,x in enumerate(lines)if x.strip()=='f32.sqrt')
window=lines[sqrtline-15:sqrtline+2]
assert [x.strip()for x in window].count('f32.mul')>=2 and 'f32.add'in[x.strip()for x in window]
report=dict(kind='static_source_correction_not_dynamic',script_sha256=sha(Path(__file__)),old_source_sha256=sha(old),new_source_sha256=sha(new),old_source_preserved=True,spawn8740_function_AST_identical_after_type_rename=True,random13563_only_executable_AST_change=dict(old=oldexpr,new=newexpr),wat13563_sha256=sha(wat),wat_sqrt_line_1based=sqrtline+1,wat_window=window,rule='directf32sumSquaresThenSqrt; notcall50441',original_executions=0,model_executions=0)
p=OUT/'source-correction-proof.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(p),sha256=sha(p))))
