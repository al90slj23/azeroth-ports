"""Read-only binding of declared unresolved922 scratch words after their write.

This does not predict or recover the caller stack. It only verifies that the
same written word follows the independently specified whole-record copies and
partial writes. Original observations never enter the production model.
"""
import struct


class LiveAuxiliaryVerifier135:
    def __init__(self):
        self.origins={}
        self.observations=0

    def observe(self,raw,expected):
        entries=expected.get('unresolved_live_auxiliary_origins',[])
        model=expected['vectors']['live32']
        actual=raw['vectors']['live32']
        slots=set()
        for item in entries:
            index=item['slot'];token=tuple(item['source'])
            if (index in slots or not 0<=index<model['capacity']
                    or len(token)!=5 or token[0]!='922.effect8or9.caller_frame+48'
                    or model['storage'][index][16:20]!=[None]*4):
                raise ValueError('Invalid named unresolved live auxiliary source')
            slots.add(index)
            row=bytes.fromhex(actual['storage'][index]);word=struct.unpack_from('<I',row,16)[0]
            if token not in self.origins:
                if raw['record_kind']!='stage' or raw['kind']!='player' or index>=actual['count']:
                    raise ValueError('New scratch source must originate in an admitted player cast')
                if (struct.unpack_from('<I',row,8)[0]not in(8,9)
                        or struct.unpack_from('<I',row,20)[0]!=token[2]
                        or struct.unpack_from('<Q',row,0)[0]!=0):
                    raise ValueError('Original922 write destination differs from named source')
                self.origins[token]=dict(first_stage=raw['stage_index'],first_slot=index,
                    observed_word=word,spell=token[2])
            elif self.origins[token]['observed_word']!=word:
                raise ValueError('Written opaque word changed during independently specified copy/inheritance')
            self.observations+=1

    def report(self):
        return dict(kind='unresolved_written_source_observation_and_copy_binding_not_value_prediction',
            distinct_sources=len(self.origins),observations=self.observations,
            source_words=[dict(source=list(k),**v)for k,v in self.origins.items()],
            original_values_fed_to_model=False,caller_stack_producer_reconstructed=False)
