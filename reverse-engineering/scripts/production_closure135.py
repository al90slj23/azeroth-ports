"""Local production import closure across core_spec and resource_spec."""
import ast


def production_sources135(root,*entries):
    base=root/'reconstruction';allowed=('core_spec','resource_spec');pending=list(entries);seen=set()
    while pending:
        name=pending.pop()
        if name in seen:continue
        parts=name.split('.');path=base.joinpath(*parts).with_suffix('.py')
        if not path.is_file():
            path=base.joinpath(*parts)/'__init__.py'
            if not path.is_file():raise ValueError('Missing local production dependency '+name)
            package=name
        else:package=name.rsplit('.',1)[0]
        seen.add(name)
        if name not in allowed:pending.append(parts[0])
        for node in ast.walk(ast.parse(path.read_text())):
            candidates=[]
            if isinstance(node,ast.ImportFrom):
                if node.level:
                    if node.level!=1:raise ValueError('Unexpected package nesting')
                    prefix=package
                    if node.module:prefix+='.'+node.module
                else:prefix=node.module or ''
                if prefix.split('.')[0]not in allowed:continue
                candidates.append(prefix)
                for alias in node.names:
                    child=prefix+'.'+alias.name
                    if base.joinpath(*child.split('.')).with_suffix('.py').is_file():candidates.append(child)
            elif isinstance(node,ast.Import):candidates.extend(a.name for a in node.names if a.name.split('.')[0]in allowed)
            pending.extend(candidates)
    result=[]
    for name in seen:
        p=base.joinpath(*name.split('.')).with_suffix('.py')
        if not p.is_file():p=base.joinpath(*name.split('.'))/'__init__.py'
        result.append(str(p.relative_to(root)))
    return tuple(sorted(set(result)))
