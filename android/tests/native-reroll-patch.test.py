"""Guard the Android-only native UI edit against upstream/code-scope drift."""
import hashlib
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import patch_mobile_reroll as ui

class NativeRerollPatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=ROOT/'assets/latest-web-core/wenilla_bg.wasm'
        cls.original=cls.source.read_bytes()
        cls.output,cls.edits=ui.patch(cls.original)
    def test_original_snapshot_untouched(self):
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),ui.ORIGINAL_SHA256)
        self.assertNotEqual(self.original,self.output)
        self.assertEqual(len(self.original),len(self.output))
    def test_only_the_local_button_constants_change(self):
        allowed=set()
        for e in self.edits:allowed.update(range(e['offset'],e['offset']+len(bytes.fromhex(e['old_bytes']))))
        changed={i for i,(a,b) in enumerate(zip(self.original,self.output)) if a!=b}
        self.assertTrue(changed)
        self.assertTrue(changed<=allowed)
        self.assertTrue(all(ui.FUNCTION_START<=i<ui.FUNCTION_END for i in changed))
        self.assertEqual(len(self.edits),28)
    def test_source_drift_and_double_patch_are_rejected(self):
        with self.assertRaises(ValueError):ui.patch(self.output)
        changed=bytearray(self.original);changed[100]^=1
        with self.assertRaises(ValueError):ui.patch(changed)

if __name__=='__main__':unittest.main()
