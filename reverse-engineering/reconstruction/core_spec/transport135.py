"""Independent Web32 fixed135 local transport methods, not an App constructor.

Restores the six real vtable methods over an explicit76B Rc/RefCell model.
Physical pointers are ownership tokens outside this pure model.  Untouched
ring/command slots remain None, never inferred zero.  Clock/logging branches
need explicit caller-supplied observations; their host acquisition is not
silently substituted, and remains outside the quiet-leaf original corpus.
"""
from dataclasses import dataclass,replace
from fractions import Fraction
from . import binary32 as f

CHOICES_MARKER=b'"type":"choices"'
VTABLE_ADDRESS=1495776
VTABLE_METHODS={12:28425,16:52236,20:45626,24:21513,28:47313,32:176109}
CELL_BYTES=76
TRANSPORT_BYTES=24


class UnknownTransport135(NotImplementedError):pass
class BorrowConflict135(ValueError):pass


def _bytes(value):
    if type(value)is not bytes:raise TypeError('Explicit immutable payload bytes required')
    return value


@dataclass(frozen=True)
class PayloadRing135:
    storage:tuple=()
    head:int=0
    count:int=0

    def __post_init__(self):
        cap=len(self.storage)
        if not 0<=self.count<=cap or(cap and not 0<=self.head<cap)or(not cap and(self.head or self.count)):
            raise ValueError('Valid VecDeque head/count/capacity required')
        for item in self.storage:
            if item is not None:_bytes(item)
        if any(self.storage[(self.head+j)%cap]is None for j in range(self.count)):
            raise ValueError('Every live payload must be explicit')

    @property
    def capacity(self):return len(self.storage)

    @property
    def active(self):return tuple(self.storage[(self.head+j)%self.capacity]for j in range(self.count))

    def append(self,payload):
        _bytes(payload);values=list(self.storage);cap=self.capacity;head=self.head
        if self.count==cap:
            grown=max(4,cap*2);values.extend([None]*(grown-cap))
            # Original55793's VecDeque relocation, preserving old/stale slots.
            if head>cap-self.count:
                tail=cap-head;prefix=self.count-tail
                if tail>prefix and grown-cap>=prefix:
                    values[cap:cap+prefix]=values[:prefix]
                else:
                    moved=grown-tail;values[moved:moved+tail]=values[head:head+tail];head=moved
            cap=grown
        index=head+self.count
        if index>=cap:index-=cap
        values[index]=payload
        return PayloadRing135(tuple(values),head,self.count+1)


@dataclass(frozen=True)
class CommandVector135:
    storage:tuple=()
    count:int=0

    def __post_init__(self):
        if not 0<=self.count<=len(self.storage):raise ValueError('Explicit command length/capacity required')
        for record in self.storage:
            if record is not None and(len(record)!=232 or any(w is not None and(type(w)is not int or not 0<=w<=255)for w in record)):
                raise ValueError('Opaque232B command words required')
        if any(record is None for record in self.storage[:self.count]):raise ValueError('Live command row required')

    @property
    def capacity(self):return len(self.storage)

    @property
    def active(self):return self.storage[:self.count]

    def append_timeout(self):
        values=list(self.storage)
        if self.count==len(values):values.extend([None]*(max(4,2*len(values))-len(values)))
        record=list(values[self.count]if values[self.count]is not None else(None,)*232)
        record[:8]=(2,0,0,0,0,0,0,0);values[self.count]=tuple(record)
        return CommandVector135(tuple(values),self.count+1)


@dataclass(frozen=True)
class TransportRow88:
    required:tuple
    optional:tuple
    word84:int

    def __post_init__(self):
        if len(self.required)!=3 or len(self.optional)!=4:raise ValueError('Three bytevectors/four optional bytevectors required')
        for value in self.required:_bytes(value)
        for value in self.optional:
            if value is not None:_bytes(value)
        if type(self.word84)is not int or not 0<=self.word84<=0xffffffff:raise ValueError('Raw u32 word84 required')


@dataclass(frozen=True)
class Instant135:
    seconds:int
    nanoseconds:int

    def __post_init__(self):
        if not 0<=self.seconds<1<<64 or not 0<=self.nanoseconds<1000000000:raise ValueError('Actual Web Instant u64 seconds/u32 nanos required')

    def elapsed_bits(self,now):
        # Original48383 saturates a backwards Instant to zero Duration.
        delta=max(0,(now.seconds-self.seconds)*1000000000+now.nanoseconds-self.nanoseconds)
        seconds,nanos=divmod(delta,1000000000)
        return f.add(f._encode(Fraction(seconds)),f.div(f.from_u32(nanos),0x4e6e6b28))


@dataclass(frozen=True)
class TransportCell135:
    strong:int=1
    weak:int=1
    borrow:int=0
    ring:PayloadRing135=PayloadRing135()
    commands:CommandVector135=CommandVector135()
    snapshot:bytes|None=None
    rows88:tuple|None=None
    rows12:tuple|None=None

    def __post_init__(self):
        if not 0<self.strong<=0xffffffff or not 0<self.weak<=0xffffffff or not 0<=self.borrow<=255:raise ValueError('Explicit live Rc owner counts/borrow byte required')
        if self.snapshot is not None:_bytes(self.snapshot)
        if self.rows88 is not None and any(not isinstance(row,TransportRow88)for row in self.rows88):raise TypeError('Actual structured88B rows required')
        if self.rows12 is not None and any(type(row)is not bytes or len(row)!=12 for row in self.rows12):raise ValueError('Opaque12B rows required')


@dataclass(frozen=True)
class Transport135:
    cell:TransportCell135=TransportCell135()
    armed_at:Instant135|None=None
    log_packets:bool=False
    arm_choices:bool=False


def _borrow(cell):
    if cell.borrow==1:raise BorrowConflict135('Original mutable RefCell borrow already held')


def send_payload(state,payload,*,now=None):
    """28425 clones payload and pushes bytevector; optional host branches explicit.

    Logging observation must be performed by a caller before calling this pure
    method.  This model reports the requirement instead of skipping the host.
    """
    _bytes(payload)
    if state.log_packets:raise UnknownTransport135('Original55988 host logging must be modeled before send')
    armed=state.armed_at
    if state.arm_choices and CHOICES_MARKER in payload:
        if not isinstance(now,Instant135):raise UnknownTransport135('Original60918 platform clock is an explicit missing input')
        armed=now
    _borrow(state.cell)
    return replace(state,armed_at=armed,cell=replace(state.cell,borrow=0,ring=state.cell.ring.append(payload)))


def replace_snapshot(state,payload):
    """52236 deep-clones bytes before borrowing, drops old optional, sets Some."""
    _bytes(payload);_borrow(state.cell)
    return replace(state,cell=replace(state.cell,borrow=0,snapshot=payload))


def poll_commands(state,*,now=None):
    """45626 moves whole232B vector, restores(cap0,ptr8,len0), optional timeout."""
    _borrow(state.cell);commands=state.cell.commands;armed=state.armed_at
    if armed is not None:
        if not isinstance(now,Instant135):raise UnknownTransport135('Original48383 platform elapsed clock is an explicit missing input')
        if f.to_float(armed.elapsed_bits(now))>1.5:
            armed=None;commands=commands.append_timeout()
    return replace(state,armed_at=armed,cell=replace(state.cell,borrow=0,commands=CommandVector135())),commands


def replace_rows88(state,rows):
    """21513 clones all3 required/four present optional bytevectors per row."""
    rows=tuple(rows)
    if any(not isinstance(r,TransportRow88)for r in rows):raise TypeError('Explicit88B transport rows required')
    _borrow(state.cell)
    return replace(state,cell=replace(state.cell,borrow=0,rows88=rows))


def replace_rows12(state,rows):
    """47313 copies each opaque12B row, replacing the previous optional vector."""
    rows=tuple(rows)
    if any(type(r)is not bytes or len(r)!=12 for r in rows):raise ValueError('Actual opaque12B records required')
    _borrow(state.cell)
    return replace(state,cell=replace(state.cell,borrow=0,rows12=rows))


def false_method(state):
    """176109 returns0 without inspecting its input; not network connectivity."""
    return 0


def initial_cell_writes135():
    """Original4253 constructor's exact written76B slots; unknown bytes=None."""
    values=[None]*76
    def put(at,word):values[at:at+4]=word.to_bytes(4,'little')
    for at,word in((0,1),(4,1),(12,0),(16,4),(20,0),(24,0),(28,0),(32,8),(36,0),(40,0xffffffff),(52,0xffffffff),(64,0xffffffff)):
        put(at,word)
    values[8]=0
    return tuple(values)
