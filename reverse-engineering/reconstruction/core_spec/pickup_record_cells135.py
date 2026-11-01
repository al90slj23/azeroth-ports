"""Independent56B pickup encoding without inventing an unwritten arrival."""
from .pickups134 import PickupRecord
from .record_cells135 import cells135,put_u32,put_u64,encode_row


def pickup_words135(record):
    if not isinstance(record,PickupRecord):raise TypeError('PickupRecord required')
    return (record.marker,record.arrival_bits,record.kind,record.amount,
        record.guid&0xffffffff,record.guid>>32,record.aux_capacity,record.aux_pointer,
        record.aux_count,record.visual_id,record.x_bits,record.y_bits,record.height_bits,record.spawn_time_bits)


def encode_pickup_cells135(record, *, prior=None):
    """Write defined semantic fields; retain +4 until its actual producer runs."""
    if not isinstance(record,PickupRecord):raise TypeError('PickupRecord required')
    row=[None]*56 if prior is None else cells135(prior,56)
    for i,value in enumerate(pickup_words135(record)):
        if value is not None:put_u32(row,4*i,value)
    return encode_row(row)
