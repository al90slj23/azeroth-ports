"""Explicit local Python/JS dependency closure guard for137 experiments."""
from pathlib import Path
import ast,re
ROOT=Path(__file__).resolve().parents[1]

def verify_local_source_closure(files):
    """Require every explicit local Python/JS import, including fixture data.

    The production closure alone does not include checker-only corpus inputs.
    Reject an incomplete declared closure before generating any expectations.
    """
    declared=set(files);edges=set()
    for name in files:
        path=ROOT/name
        if path.suffix=='.mjs':
            for relative in re.findall(r"from\s+['\"](\.[^'\"]+)['\"]",path.read_text()):
                dependency=str((path.parent/relative).resolve().relative_to(ROOT))
                assert dependency in declared,(name,dependency)
                edges.add((name,dependency))
            continue
        if path.suffix!='.py':continue
        parts=Path(name).with_suffix('').parts
        for node in ast.walk(ast.parse(path.read_text())):
            modules=[]
            if isinstance(node,ast.Import):modules=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom):
                if node.level:
                    assert parts[0]=='reconstruction','Unhandled relative script import'
                    prefix=list(parts[1:-node.level]);module='.'.join(prefix+([node.module]if node.module else[]))
                else:module=node.module or''
                modules=[module]+[module+'.'+a.name if module else a.name for a in node.names]
            for module in modules:
                if not module:continue
                rel=Path(*module.split('.'))
                for folder in('scripts','reconstruction'):
                    source=ROOT/folder/rel.with_suffix('.py');package=ROOT/folder/rel/'__init__.py'
                    dependency=source if source.is_file()else package if package.is_file()else None
                    if dependency is None:continue
                    key=str(dependency.relative_to(ROOT));assert key in declared,(name,key)
                    edges.add((name,key))
                    for parent in dependency.parents:
                        if parent==ROOT/folder:break
                        initializer=parent/'__init__.py'
                        if initializer.is_file():
                            key=str(initializer.relative_to(ROOT));assert key in declared,(name,key)
                            edges.add((name,key))
    return [list(row)for row in sorted(edges)]
