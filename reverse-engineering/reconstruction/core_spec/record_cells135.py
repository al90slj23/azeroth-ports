"""Physical record cells with explicit unknown bytes; no invented backing.

Full known records keep their historical hex encoding. A record containing an
unwritten byte remains an immutable tuple of bytes/None across module borders.
Only an actual consumer read requires its byte range to be known.
"""


class UnknownRecordRead135(ValueError):
    """A consumer attempted to read one or more unknown physical record cells."""

    def __init__(self, offset, width, consumer):
        self.offset = offset
        self.width = width
        self.consumer = consumer
        super().__init__(f'{consumer}: unknown record read at +{offset}, width {width}')


def _view(raw):
    if isinstance(raw, str):
        return bytes.fromhex(raw)
    if isinstance(raw, (bytes, bytearray, tuple, list)):
        return raw
    raise TypeError('Record must be hex, bytes, or a byte/None cell sequence')


def _check_cell(cell):
    if cell is not None and (type(cell) is not int or not 0 <= cell <= 255):
        raise ValueError('Record cells must be integers0..255 or None')
    return cell


def cells135(raw, size=424):
    """Return a new mutable list, validating size and every physical cell."""
    if type(size) is not int or size < 0:
        raise ValueError('Record size must be a nonnegative integer')
    row = list(_view(raw))
    if len(row) != size:
        raise ValueError(f'Expected {size} physical record cells, got {len(row)}')
    for cell in row:
        _check_cell(cell)
    return row


def _bounds(row, offset, width):
    if type(offset) is not int or offset < 0 or offset + width > len(row):
        raise ValueError('Record read/write outside physical row')


def _unsigned(raw, offset, width, consumer):
    row = _view(raw)
    _bounds(row, offset, width)
    selected = tuple(_check_cell(cell) for cell in row[offset:offset + width])
    if any(cell is None for cell in selected):
        raise UnknownRecordRead135(offset, width, consumer)
    return sum(cell << (8 * index) for index, cell in enumerate(selected))


def u32(raw, offset, consumer='record135.u32'):
    return _unsigned(raw, offset, 4, consumer)


def i32(raw, offset, consumer='record135.i32'):
    value = _unsigned(raw, offset, 4, consumer)
    return value - 0x100000000 if value & 0x80000000 else value


def u64(raw, offset, consumer='record135.u64'):
    return _unsigned(raw, offset, 8, consumer)


def _put(raw, offset, value, width):
    if not isinstance(raw, (list, bytearray)):
        raise TypeError('Writing a record requires mutable cells')
    _bounds(raw, offset, width)
    if type(value) is not int or not 0 <= value < 1 << (8 * width):
        raise ValueError(f'Value must be an unsigned{8 * width}-bit integer')
    raw[offset:offset + width] = [(value >> (8 * index)) & 255 for index in range(width)]


def put_u32(raw, offset, value):
    _put(raw, offset, value, 4)


def put_u64(raw, offset, value):
    _put(raw, offset, value, 8)


def encode_row(cells):
    """Keep unknown cells unknown; only fully known rows become legacy hex."""
    row = tuple(_check_cell(cell) for cell in _view(cells))
    return row if any(cell is None for cell in row) else bytes(row).hex()


def known_bytes(raw):
    """Require every cell for an explicit full-row bytes consumer."""
    row = tuple(_check_cell(cell) for cell in _view(raw))
    if any(cell is None for cell in row):
        raise UnknownRecordRead135(0, len(row), 'record135.known_bytes')
    return bytes(row)


def optional_u32(raw, offset, consumer='record135.optional_u32'):
    try:
        return u32(raw, offset, consumer)
    except UnknownRecordRead135:
        return None


def optional_u64(raw, offset, consumer='record135.optional_u64'):
    try:
        return u64(raw, offset, consumer)
    except UnknownRecordRead135:
        return None
