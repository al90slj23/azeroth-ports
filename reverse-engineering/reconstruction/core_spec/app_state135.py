"""Typed partial App5168 constructor projection from original4253.

Unknown/inactive bytes remain None. This is not a complete valid App producer,
renderer/profile/account constructor, original allocator or permission to call
880. Live pointers and entropy-dependent initializer outputs are explicit.
"""
from dataclasses import dataclass
import struct

SIZE=5168
MASK64=(1<<64)-1
SERVER_BYTES=b'azeroth.local'
TRANSPORT_VTABLE=1495776
FRAME_CALLBACK_VTABLE=5305816


class UnknownAppState135(NotImplementedError):pass


def _unsigned(value,bits=32):
    if type(value)is not int or not 0<=value<1<<bits:raise ValueError('Explicit uint'+str(bits)+' required')
    return value


@dataclass(frozen=True)
class AppLiveBlock135:
    offset:int
    data:bytes
    producer:str

    def __post_init__(self):
        # These are the actual4253 memcpy/copy groups, not arbitrary patches.
        if(self.offset,len(self.data))not in((4160,368),(4528,48),(4980,36)):
            raise ValueError('Only declared4253 live-copy regions are admitted')
        if type(self.data)is not bytes or not self.producer:raise ValueError('Live bytes require explicit producer identity')


@dataclass(frozen=True)
class AppConstructorInputs135:
    lcg_seed_u64:int
    transport_pointer:int
    history240:bytes
    hash_maps128:bytes
    server_string_pointer:int
    startup_flag5161:int
    live_blocks:tuple=()

    def __post_init__(self):
        _unsigned(self.lcg_seed_u64,64)
        for p in(self.transport_pointer,self.server_string_pointer):
            if not _unsigned(p):raise ValueError('Real live allocation pointer required')
        if self.startup_flag5161 not in(0,1):raise ValueError('Actual constructor branch flag0/1 required')
        if type(self.history240)is not bytes or self.history240!=struct.pack('<3I',0,1,0)*20:
            raise ValueError('Actual empty53845 twenty byte-vector headers required')
        if type(self.hash_maps128)is not bytes or len(self.hash_maps128)!=128:
            raise ValueError('Four typed32B RandomState/map initializer outputs required')
        seed0,seed1=struct.unpack_from('<2Q',self.hash_maps128,16)
        for i in range(4):
            if struct.unpack_from('<4I',self.hash_maps128,i*32)!=(5222416,0,0,0):
                raise UnknownAppState135('Original empty-table header differs')
            if struct.unpack_from('<2Q',self.hash_maps128,i*32+16)!=((seed0+i)&MASK64,seed1):
                raise UnknownAppState135('Actual4253 four sequential hash seeds required')
        if any(not isinstance(x,AppLiveBlock135)for x in self.live_blocks):raise TypeError('Typed live blocks required')
        if len({x.offset for x in self.live_blocks})!=len(self.live_blocks):raise ValueError('Duplicate live block')


@dataclass(frozen=True)
class AppKnowledge135:
    offset:int
    length:int
    label:str
    kind:str
    evidence:str


@dataclass(frozen=True)
class AppProjection135:
    storage:tuple
    knowledge:tuple
    owned_payload_requirements:tuple
    pending:tuple

    def __post_init__(self):
        if len(self.storage)!=SIZE:raise ValueError('App5168 storage required')
        if any(x is not None and(type(x)is not int or not 0<=x<256)for x in self.storage):raise ValueError('Known byte or explicit None required')

    @property
    def legal_full_app(self):return False

    @property
    def known_byte_count(self):return sum(x is not None for x in self.storage)

    @property
    def unknown_ranges(self):
        ranges=[];start=None
        for offset,value in enumerate((*self.storage,0)):
            if value is None and start is None:start=offset
            elif value is not None and start is not None:ranges.append((start,offset-start));start=None
        return tuple(ranges)

    def require_known(self,offset,length):
        if not 0<=offset<=offset+length<=SIZE:raise ValueError('App range')
        selected=self.storage[offset:offset+length]
        if any(x is None for x in selected):raise UnknownAppState135('Requested App range contains inactive or unrestored bytes')
        return bytes(selected)


def seed_derived_field4936(seed):
    """Exact4253 integer mix/select, semantic label intentionally unresolved."""
    _unsigned(seed,64)
    mixed=(seed>>46)^(seed>>23)^(((seed*2177342782468422677)&MASK64)>>40)^seed
    value=mixed&8388607;candidate=value|8388608
    return value+8388352 if candidate>16776959 else candidate


def project_app_constructor135(value):
    """Known4253 stores plus explicit real live inputs; never blanket-zero."""
    if not isinstance(value,AppConstructorInputs135):raise TypeError('Typed constructor inputs required')
    storage=[None]*SIZE;knowledge=[]
    def write(offset,data,label,kind='constant',evidence='4253:8602..8894'):
        if not 0<=offset<=offset+len(data)<=SIZE:raise ValueError('Write exceeds App')
        for j,x in enumerate(data):
            previous=storage[offset+j]
            if previous is not None and previous!=x:raise ValueError('Conflicting independently described constructor writes')
            storage[offset+j]=x
        knowledge.append(AppKnowledge135(offset,len(data),label,kind,evidence))
    def word(offset,n,label):write(offset,struct.pack('<I',n&0xffffffff),label)
    def doubleword(offset,n,label):write(offset,struct.pack('<Q',n&MASK64),label)
    # Inactive enum/option payloads are NOT initialized by these tag stores.
    doubleword(0,0,'first_wallclock_option_absent')
    doubleword(16,2,'game2592_absent_tag')
    doubleword(2608,2,'second768_variant_absent_tag')
    word(3376,2,'selected_profile376_absent_tag')
    for offset,length,label in((8,8,'wallclock_inactive_f64'),(24,2584,'game2592_inactive_payload'),
            (2616,760,'second768_inactive_payload'),(3380,372,'selected_profile376_inactive_payload'),
            (4752,16,'party_absent_payload')):
        knowledge.append(AppKnowledge135(offset,length,label,'inactive','4253:8685..8693,8889..8894'))
    write(3752,value.history240,'twenty_empty_bytevector_history_headers','validated-leaf-input','53845→4253:8760..8767')
    for i in range(4):
        start=3992+i*32
        write(start,value.hash_maps128[i*32:i*32+16],f'empty_hash_table_header{i}','constant','4253:8804..8831/static5222424')
        write(start+16,value.hash_maps128[i*32+16:(i+1)*32],f'hash_seed_pair{i}','typed-live-input','4253:8488..8595,8768..8803')
    doubleword(4120,0,'raw_collection4120')
    doubleword(4128,4294967296,'raw_collection4128')
    doubleword(4136,0,'raw_collection4136')
    word(4144,1,'raw_field4144')
    write(4148,bytes(7),'exact_overlapping_zero_stores4148_4151')
    word(4748,-1,'party_option_absent_tag')
    write(4768,struct.pack('<I',value.transport_pointer),'live_transport24_pointer','typed-live-input','4253:8736..8738')
    word(4772,TRANSPORT_VTABLE,'actual_transport_vtable')
    write(4776,bytes(72),'exact_zero_stores4776_to4847')
    write(4848,bytes(76),'original_explicit_memory_fill76','constant','4253:8841..8846')
    write(4928,struct.pack('<Q',value.lcg_seed_u64),'initial_lcg_entropy_seed','typed-live-input','4253:8883..8885')
    write(4936,struct.pack('<Q',seed_derived_field4936(value.lcg_seed_u64)),'seed_derived_raw_word4936','computed','4253:8853..8882')
    write(4944,struct.pack('<3I',0,4,0)*3,'three_empty_input_queues','constant','4253:8605..8619')
    write(5016,struct.pack('<3I',0,4,0)*2,'two_empty_output_vectors')
    write(5040,struct.pack('<3I',0,1,0),'empty_byte_output_cache')
    word(5052,13,'server_string_capacity')
    write(5056,struct.pack('<I',value.server_string_pointer),'live_server_string_pointer','typed-live-input','4253:8847..8852')
    word(5060,13,'server_string_length')
    word(5064,-1,'raw_absent_option5064')
    for offset,length in((5076,4),(5080,8),(5088,8),(5096,4),(5116,4),(5120,1),(5162,1)):
        write(offset,bytes(length),'exact_zero_store'+str(offset))
    write(5161,bytes([value.startup_flag5161]),'constructor_loaded_state_branch_flag','typed-live-input','4253:8643..8645')
    word(5163,-16711680,'unaligned_raw_word5163')
    for block in value.live_blocks:write(block.offset,block.data,block.producer,'typed-live-copy','4253:8628..8684')
    for offset,length,label in((4160,368,'settings368_constructor'),(4528,48,'loaded_state48_constructor'),(4980,36,'preferences36_constructor')):
        if not any(x.offset==offset for x in value.live_blocks):knowledge.append(AppKnowledge135(offset,length,label,'unrestored-live-copy','4253:8628..8684'))
    classified={j for row in knowledge for j in range(row.offset,row.offset+row.length)}
    start=None
    for offset in range(SIZE+1):
        unknown=offset<SIZE and storage[offset]is None and offset not in classified
        if unknown and start is None:start=offset
        elif not unknown and start is not None:
            knowledge.append(AppKnowledge135(start,offset-start,'unmapped_constructor_bytes','unrestored','No complete producer/read-liveness proof yet'))
            start=None
    pending=('This partial projection is never a complete legal App5168; all None bytes remain unknown/inactive.',
        'Real entropy/hash/transport/string allocations and their ownership must come from actual producers or declared typed live inputs.',
        'Settings368/loaded-state48/preferences36 parsing and other initialization branches are not independently restored.',
        'Selected-profile construction/selection, Game install caller24129, oldGame destruction and Rust source-forget semantics remain separate.',
        'No app start, network, storage, renderer, original instance or full880 is executed by this model.')
    return AppProjection135(tuple(storage),tuple(knowledge),
        ((value.server_string_pointer,SERVER_BYTES,'owned13B_string_cap13_len13'),
         (value.transport_pointer,24,'typed_transport24_with_actual76B_cell_and_real_holders')),pending)


def game_install_contract135():
    """Actual880/1371 move contract; not an implementation of caller24129."""
    return dict(destination_app_offset=16,bytes=2592,old_tag_offset=16,absent_tag=2,
        drop_old_unless_absent_function=1627,preceding_function=24129,
        move_not_clone=True,additional_world_rc_increment_from_copy=0,source_must_be_forgotten=True,
        complete_caller_semantics_recovered=False,
        evidence=('880:13478..13495,15007..15008,15850..15864','1371:11306..11326'))


def app_owner_layout135():
    """4253's real Rc/borrowed-App allocation, excluding uninitialized padding."""
    return dict(allocation_bytes=5184,strong_offset=0,weak_offset=4,
        borrow_byte_offset=8,app_offset=16,app_bytes=5168,
        initially_written_strong=1,initially_written_weak=1,initially_written_borrow=0,
        bytes9_through15_unknown=True,final_holder_counts_not_predicted=True,
        evidence='4253:8938..8987')


def app_pointer_from_tick_closure135(env_pointer,vtable_pointer,read_u32):
    """4253's real25ms NoArgs interval closure; pure read-only pointer decode.

    OfficialJS does not expose.original. A transparent import wrapper can map
    callback identity to __wbindgen_cast_0010(a,b). Only this guarded vtable is
    admitted; arbitrary RAF/event closures may have different environments.
    """
    _unsigned(env_pointer);_unsigned(vtable_pointer)
    if vtable_pointer!=FRAME_CALLBACK_VTABLE:raise UnknownAppState135('Not the guarded original83825 tick closure')
    rc=_unsigned(read_u32(env_pointer+8))
    if not rc or rc>0xffffffff-16:raise ValueError('Invalid actual Rc pointer')
    return rc+16
