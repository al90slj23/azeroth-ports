#!/usr/bin/env python3
"""Read the fixed135 Boss declarations/point lists without executing the game."""
from pathlib import Path
import hashlib
import json
import struct
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source


def extract():
    binary=SOURCE.read_bytes();assert hashlib.sha256(binary).hexdigest()==SOURCE_SHA
    segments=parse_source(binary)[4]
    memory=bytearray(max(s['address']+s['length']for s in segments if s['address']is not None))
    for s in segments:
        if s['address']is not None:memory[s['address']:s['address']+s['length']]=binary[s['file_offset']:s['file_offset']+s['length']]
    u=lambda p:struct.unpack_from('<I',memory,p)[0]
    bosses=[];points=[]
    for zone in range(12):
        address=5456016+zone*152;bp,count=u(address+72),u(address+76);assert count==5
        pointptr,pointcount=u(address+56),u(address+60);assert pointcount<100
        points.append(tuple(struct.unpack_from('<2I',memory,pointptr+i*8)for i in range(pointcount)))
        rows=[]
        for i in range(count):
            p=bp+i*72;abilityptr,n=u(p+8),u(p+12);assert 0<n<20
            rows.append((p,u(p+32),u(p+36),u(p+40),u(p+44),u(p+48),u(p+52),u(p+56),u(p+60),memory[p+68],
                         abilityptr,n,tuple(u(abilityptr+j*44+40)for j in range(n))))
        bosses.append(tuple(rows))
    return tuple(bosses),tuple(points)


if __name__=='__main__':
    bosses,points=extract()
    p=ROOT/'reconstruction/core_spec/spawn_boss135_data.py'
    if p.exists():raise ValueError('Refusing to overwrite existing frozen declaration data')
    p.write_text('"""Fixed0.135.1 sixty Boss definitions and static spawn points; no runtime original reads."""\nBOSSES = '+repr(bosses)+'\nPOINTS = '+repr(points)+'\n')
    print(json.dumps({'definitions':sum(map(len,bosses)),'point_counts':list(map(len,points)),'data_source_sha256':SOURCE_SHA}))
