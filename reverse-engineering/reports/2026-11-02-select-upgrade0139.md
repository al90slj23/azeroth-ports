# 0.139.0：实际顺劈升级卡选择

作者正式19组（18个不同输入）冻结，等待异作者独审。真实新2945／1600→完整1108→4677／2181三卡→1093，19次选择0声明差异；18次现有顺劈升级、1次新技能；包含实际首张为new与upgrade的两条router路径。所有四NPC、两符文、时间窗、四special和69边界原始background头／指针／完整backing逐阶段恒定。

17个可达升级键全覆盖：tier0只有kind0／1，tier1至3各有0／1／2，tier4六种两kind顺序。输入来自独立自然App seed搜索，保留四敌人位置／朝向／抖动、两符文、时间窗和69个边界yaw的全部RNG消耗；搜索省略重复packet构造，不省RNG；选中的每个seed随后重跑完整model和新原件。未根据原件输出补模型、改卡或重抽。初次搜索错误要求不可达tier0kind2，16,384个纯model输入未找到而停止；旧源与失败已保存，0原件执行。修正目标为17后完成。

当前1093逐kind先加owned rank，调用25511算实际tier值，再改damage／cooldown／targets、计数，最后逐步施加rank伤害尾乘；完全按实际kinds顺序。五张表从当前139地址5405004／5040／5076／5112／5148重新逐字绑定，未转记旧版通过。选择后完整80B、23属性、已知player fields、RNG、phase2→1和live32一致：456B已知／152 None；None实际均非零，继续保留未知。113988个background已知byte occurrence及66588 None逐步核对。

19次完整1108＋19次4677＋19次1093为57个组合目标入口，2945／1600各19次为38 setup；不将内部2181／25511／4603／26364调用另计。1组原件pilot、初次import setup错误与不可达键搜索分别留档，不相加为覆盖。8个source guard是模型自检。

新API select_card_any139直接路由真实new或upgrade；当前升级仅首constructor顺劈rank1、count0、neutral additional域。Repeated／saturated／其他技能、金币卡、非空live32属性重算、活动移动stop/resume与完整UI／外观／其他键／后续完整消息流／Aura48／物理BTree仍未知。原件侧仍借合法v2初始化资源上下文，未还原自然App／Rc／externref／完整主循环或Windows原生一局。旧v1／v2六件、九件及其收据均未改。

[机器报告](2026-11-02-select-upgrade0139.json)包含完整边界与证据。
