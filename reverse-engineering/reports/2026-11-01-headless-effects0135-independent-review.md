# 0.135.1 含独立915空域的同G闭环复核

[072329最终收据](../evidence/full0135-oracle-20261101T072329.149731Z/headless135-comparison.json) 独立复核通过：8 seed、1,614帧、11,309阶段、11次自然选择、11,317次原件入口。65份冻结源码/58 core闭包含init、9个原角色索引/签名/body SHA与只export变更全部通过，当前无drift。整个400-frame固定policy corpus从快照重新生成，各action七阶段2088→1754→3757→915→921→2862→947逐项回放，与保存的原件结果0差异。没有重跑原件或修改作者源。

原八seed输入、动作、选卡、停点与064308保持完全相同；剥离新effects阶段和effect_state字段后，旧预期逐字段相等。本批新增915空队列状态来自独立构造常量和纯模型传递，未用071318 probe逐帧回填。2364/2356为0、1644为1、416 tag0、玩家XYZ及两Vec capacity/完整active records在全部阶段预测并严格比较。

inactive420..436五个word、物理vec指针与facing另存完整sidecar，共11,309阶段/90,472个u32观察，不预测为零、不加mask。适配器只向临时EffectSystemState提供合法u32代表值；在empty56/120、416tag0守卫下，这些值除范围校验和原样携带外不参与行为计算，且不会复制回canonical state。独立纯模型poison7组不同raw payload，其他行为输出全部相同；非空56、非空120、active416三个headless输入明确拒绝并保留状态。原件中没有写这些代表值。

每stage双128槽lossless delta独立还原，NPC累计613,762,048B、area127,384,576B与纯模型全部bytes/SHA一致；area顺序删除/单tick变换与counter/RNG连续核算再次通过。实际事件仍为6 area birth、34tick、4末槽到期、4旧area槽复用、1次flamestrike effect0死亡、151次blizzard slow；没有集成中的非平凡area压缩、非零19B复用或blizzard致死新证据。52次NPC旧槽复用保留416个非零未写字节，无非零stale U4复用。

终态仍为6个pending_selected_ability、2个400-frame预算；后者下一纯模型步为pending_due_event，没有执行第401原件帧。旧pickup/live共12,768次已声明未写word例外保持原范围，915/NPC/area没有新增mask。独立915在此只接受空56/120与inactive416的闭环域，非空组件另有独立收据，不能借此宣称完整915、916/975/38007/2602/2573/49037、完整880或真实1089资源入口完成。

[最终独审证据](../evidence/headless-effects0135-independent-review-20261101T072627.470924Z/review.json) 包含当前reviewer、适配器poison/guard和历史reviewer完整源；历史b31a54f3…与前一headless-area独审吻合，旧收据和快照未改。
