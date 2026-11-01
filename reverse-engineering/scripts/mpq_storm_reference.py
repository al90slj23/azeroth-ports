"""Pinned StormLib reference only; production resource_spec does not import it."""
import ctypes as c
from pathlib import Path

from mpq_toolchain import verify


class Storm:
    def __init__(self):
        self.identity = verify()
        self.lib = c.CDLL(self.identity['library'])
        signatures = {
            'SFileOpenArchive': ([c.c_char_p, c.c_uint32, c.c_uint32, c.POINTER(c.c_void_p)], c.c_bool),
            'SFileCloseArchive': ([c.c_void_p], c.c_bool),
            'SFileOpenFileEx': ([c.c_void_p, c.c_char_p, c.c_uint32, c.POINTER(c.c_void_p)], c.c_bool),
            'SFileGetFileSize': ([c.c_void_p, c.POINTER(c.c_uint32)], c.c_uint32),
            'SFileReadFile': ([c.c_void_p, c.c_void_p, c.c_uint32, c.POINTER(c.c_uint32), c.c_void_p], c.c_bool),
            'SFileCloseFile': ([c.c_void_p], c.c_bool),
        }
        for name, (arguments, result) in signatures.items():
            method = getattr(self.lib, name)
            method.argtypes, method.restype = arguments, result

    def archive(self, path):
        handle = c.c_void_p()
        if not self.lib.SFileOpenArchive(str(Path(path).resolve()).encode(), 0, 0x100, c.byref(handle)):
            raise ValueError('StormLib read-only open failed')
        return StormArchive(self, handle)


class StormArchive:
    def __init__(self, storm, handle):
        self.storm, self.handle = storm, handle

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if not self.storm.lib.SFileCloseArchive(self.handle):
            raise ValueError('StormLib close failed')

    def read(self, name, *, max_bytes=32 * 1024 * 1024):
        lib = self.storm.lib
        handle = c.c_void_p()
        if not lib.SFileOpenFileEx(self.handle, name.encode('latin1'), 0, c.byref(handle)):
            raise FileNotFoundError(name)
        try:
            high = c.c_uint32()
            size = lib.SFileGetFileSize(handle, c.byref(high))
            if high.value or size > max_bytes:
                raise ValueError('StormLib file exceeds budget')
            result = bytearray()
            while len(result) < size:
                wanted = min(1024 * 1024, size - len(result))
                buffer, read = c.create_string_buffer(wanted), c.c_uint32()
                if not lib.SFileReadFile(handle, buffer, wanted, c.byref(read), None) or read.value != wanted:
                    raise ValueError('StormLib short/failed read')
                result.extend(buffer.raw)
            return bytes(result)
        finally:
            if not lib.SFileCloseFile(handle):
                raise ValueError('StormLib file close failed')
