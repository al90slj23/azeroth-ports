"""Verify Android pause patches exactly the engine imports, not global browser APIs."""
import ast
from pathlib import Path
root = Path(__file__).resolve().parents[1]
source = (root/'scripts/prepare_assets.py').read_text()
ast.parse(source)
original = (root/'assets/latest-web-core/wenilla.js').read_text()
assert original.count('arg0.cancelAnimationFrame(arg1);') == 1
assert original.count('const ret = arg0.requestAnimationFrame(arg1);') == 1
assert original.count('const ret = arg0.now();') == 2
assert original.count('const ret = Date.now();') == 1
prepared = (root/'build/assets/overlay/wenilla.js').read_text()
assert prepared.count('AzerothAndroidPause.cancelFrame(arg0, arg1)') == 1
assert prepared.count('AzerothAndroidPause.requestFrame(arg0, arg1)') == 1
assert prepared.count('AzerothAndroidPause.monotonicNow(arg0)') == 2
assert prepared.count('const ret = Date.now();') == 1
assert 'window.requestAnimationFrame =' not in prepared
assert 'window.performance.now =' not in prepared
print('Engine-only frame imports and real save wall-clock preserved')
