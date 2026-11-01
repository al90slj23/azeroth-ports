"""Static local production import closure, including executed package entry."""
import ast
from pathlib import Path


def core_sources(root, *entries):
    base = root / 'reconstruction/core_spec'
    pending = [base / '__init__.py', *(base / name for name in entries)]
    seen = set()
    while pending:
        path = pending.pop()
        if path in seen: continue
        if not path.is_file(): raise ValueError(f'Missing explicit production dependency:{path}')
        seen.add(path)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.level:
                if node.level != 1: raise ValueError('Unexpected nested production package')
                names = [node.module] if node.module else [alias.name for alias in node.names]
                pending.extend(base / (name.replace('.', '/') + '.py') for name in names)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('core_spec.'):
                        pending.append(base / (alias.name[len('core_spec.'):].replace('.', '/') + '.py'))
    return tuple(sorted(str(path.relative_to(root)) for path in seen))
