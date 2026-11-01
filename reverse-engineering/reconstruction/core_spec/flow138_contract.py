"""Fixed138 experiment admission constants; static mappings are not support.

These bindings distinguish the new source/ABI from historical135. A caller
must still restore each role's state producers and validate its actual domain.
No original program, metadata, file, index or network is read by this module.
"""
VERSION = '0.138.0'
BUILD = '382771e6c'
WASM_SHA256 = 'c60161d991ce97a9a4a9d3866b5e629d9e38f0fab8364c051faae8d01945b11b'

#role:(index, parameters, result, exact original bodySHA256)
ROLES = {
    'constructor':(1571,'7f7f7f','','37447d2eef76c4d93a5e2d2b5c0143ff8ef591e13fded44ee84e06bcb8d9a43e'),
    'cached_world_construct':(6760,'7f7f','','0cd6bdf5580660906a96fa8157e146c362d4743a1c3195ca2254151012628e28'),
    'opening':(1087,'7f','','ef47a74c810f0fe7c3cfc62ca1918adfcee260dfa06909775c543738d6f73c33'),
    'stats':(1512,'7f','','eed155e8b241316d7c129b174b20a1ae9627504f851231f3c81071b32f41bbae'),
    'player_tick':(2086,'7f7d','','2c8dffa5a1749a5ebc2d407b27e62ca6c07bcde3a911cbc5d687da4400e7013e'),
    'owned_tick':(1232,'7f7d','','e90d6463e66aab155f2efd662cc8ae3f231f782dab0ba6904108d5d71f9fe287'),
    'cast':(916,'7f7f','7f','77fd21222a8c50b526f0b429df7fc1bdad0c0d88a0da161416880e6b8361eb7a'),
    'auto_cast':(917,'7f7d','','e227b1c29b046bd8b144ac88e280bd2e353998d31d44a450f0acbb72c124bb43'),
    'player_aura':(1155,'7f','','a74385c6e5579e68f34a606a30656fe87b9c32725c22b72e88ab0a5f9e29a07a'),
}

STATS_LAYOUT = {
    'class_byte':360,'race_byte':361,'level':1432,'hp':1440,'maxhp':1536,
    'now':2352,'speed':1648,'action_sequence':1644,'player_guid':1336,
    'passives':(1696,1700,8),'adjustments':(1672,1676,16),
    'item_modifiers':(2028,2032,8),'owned_skills':(172,176,8),
    'definitions':(2052,2056,36),'timed':(596,600,12),'live':(1708,1712,32),
    'reserve':764,'player_pool_decay':752,
}

STATIC_GUARDS_ARE_RUNTIME_ACCEPTANCE = False
