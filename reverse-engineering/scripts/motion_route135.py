"""Deterministic test inputs toward the first independently spawned rune.

This is a controlled trajectory generator, not recovered keyboard/joystick or
native client physics. It reads only the independent model and world queries;
the complete input sequence is frozen before running the original.
"""
from core_spec import binary32 as f
from core_spec.binary32_sqrt import sqrt_bits
from core_spec.player_motion135 import MotionInput135


class FirstRuneRoute135:
    def __init__(self):
        self.target=None;self.started=False;self.stopped=False;self.events=[]

    def before_frame(self,state,dt_bits):
        if self.stopped:return ()
        if self.target is None:
            if state.frames<401:return ()
            self.target=next((p for p in state.collection.death.records if p.kind in(3,4,5)),None)
            if self.target is None:return ()
            self.events.append(dict(event='target',frame=state.frames,guid=str(self.target.guid),kind=self.target.kind))
        present=any(p.guid==self.target.guid for p in state.collection.death.records)
        x,y,z=state.collection.player_xyz
        if present:
            dx,dy=f.sub(self.target.x_bits,x),f.sub(self.target.y_bits,y)
            distance=sqrt_bits(f.add(f.mul(dx,dx),f.mul(dy,dy)))
            travel=f.mul(state.collection.level.stats.previous_speed_bits,dt_bits)
            ratio=f.div(travel,distance)if f.to_float(distance)>f.to_float(travel)else f.from_float(1)
            x,y=f.add(x,f.mul(dx,ratio)),f.add(y,f.mul(dy,ratio))
            height=state.world.height(x,y)
            if not height.found:raise NotImplementedError('Controlled route needs independently resolved terrain')
            z=height.value_bits;opcode=238 if self.started else 181;flags=1;self.started=True
        else:
            opcode=183;flags=0;self.stopped=True
            self.events.append(dict(event='stop_after_consumption',frame=state.frames,guid=str(self.target.guid)))
        milliseconds=int(f.to_float(state.collection.level.stats.now_bits)*1000)
        payload=MotionInput135(flags,milliseconds,(x,y,z),0).payload24().hex()
        return (dict(kind='motion',opcode=opcode,payload24_hex=payload),)
