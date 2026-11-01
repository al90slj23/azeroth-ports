"""Complete quiet2376 target announcements over explicit initialized names.

Locale dictionaries are inputs, not a reconstructed locale initializer. The
original compiled English suffixes remain literal, including with Chinese names.
All40B record cells, including unused unknown GUID/padding, remain unchanged.
"""
from dataclasses import dataclass,replace
import struct
from .special2376_135 import (SpecialState2376_135,SpecialResult2376_135,
    UnknownSpecial2376_135,tick_special2376_135,_target)
from .record_cells135 import u32,u64
from .spawn135_data import NORMALS

ELWYNN_ENGLISH_NAMES=tuple((f'enemy.{row[3]}',row[2])for row in NORMALS[0])
ELWYNN_CHINESE_NAMES=tuple((f'enemy.{600+i}',name)for i,name in enumerate((
    '狗头人寄生虫','幼狼','鱼人激流者','狗头人地卜师','迪菲亚暴徒','河爪蛮兵',
    '潜伏者','迪菲亚流氓巫师','迪菲亚执行者','狗头人工头','格鲁夫·迅牙','大肚子')))


@dataclass(frozen=True)
class SpecialLocale2376_135:
    names:tuple

    def __post_init__(self):
        if type(self.names)is not tuple or len(self.names)>128:
            raise ValueError('Explicit bounded locale name dictionary required')
        keys=[]
        for item in self.names:
            if type(item)is not tuple or len(item)!=2 or any(type(s)is not str for s in item):
                raise ValueError('Explicit UTF8 string key/value pairs required')
            key,value=item
            if not key or not value or '\0'in key or '\0'in value or len(value.encode())>4096:
                raise ValueError('Nonempty NUL-free bounded locale names required')
            keys.append(key)
        if len(set(keys))!=len(keys):raise ValueError('Unique locale keys required')


def tick_special2376_notify135(state,zone,locale):
    """Full2376 target/notification domain; due NPC production stays pending."""
    if not isinstance(locale,SpecialLocale2376_135)or type(zone)is not int or not 0<=zone<len(NORMALS):
        raise ValueError('Explicit valid zone and initialized locale-name input required')
    try:return tick_special2376_135(state)
    except UnknownSpecial2376_135 as error:
        if not str(error).startswith('Selected-target localized548'):raise
    target=_target(state);row=state.storage[target]
    index=u32(row,28,'special2376.notification.definition_index')
    if index>=len(NORMALS[zone]):
        raise UnknownSpecial2376_135('Out-of-range original definition panic remains a boundary')
    description=NORMALS[zone][index]
    name=dict(locale.names).get(f'enemy.{description[3]}',description[2])
    text=name+(' (Guardian)'if u64(row,0,'special2376.notification.marker') else "'s lair (empty)")
    payload=struct.pack('<5I',99,u32(row,16,'special2376.notification.x'),u32(row,20,'special2376.notification.y'),6,0)+text.encode()+b'\0'
    length=20+len(text.encode());capacity=32
    if length>capacity:capacity=max(2*capacity,length)
    if length==capacity:capacity*=2
    final=replace(state,selected392=1,target396=target,announced2565=1,announcement_time2392_bits=state.now_bits)
    return SpecialResult2376_135(final,((548,capacity,payload.hex()),),'special_target_announcement_complete')
