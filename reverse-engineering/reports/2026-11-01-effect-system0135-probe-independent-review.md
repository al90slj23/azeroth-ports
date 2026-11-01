# 0.135.1 原八seed真实915插入探针独立复核

[071318观察性收据](../evidence/full0135-oracle-20261101T071318.558372Z/effect-system135-probe-receipt.json) 通过独立只读核验。8 seed全部返回，11,309 snapshots包含1,614次完整原件915，9,695个旧独立阶段重比较0差异。66份source snapshots和57 core/init闭包、9个角色签名/body、原件非export字节与全部artifact通过；当前漂移仅root随后授权的headless/check/run三文件，不影响旧冻结模型。

保存prior-independent-expected与原064308 fixture逐字节相同；按probe快照中的旧模型重新生成400-frame固定policy corpus完全一致，没有静默换新模型或拟合原件结果。每个915快照与其前一area快照的projection、三域、双backing delta及消息逐项一致，其他阶段按旧独立预期严格比对。仅原有pickup/live未写word例外，effect/NPC/area没有新增mask。

真实构造器raw2592及各阶段均读回三域：两Vec不仅len0，所有cap/ptr/len均(0,8,0)，active及backing字节均空；clock2364=0、effect2356=0、action1644=1。末态raw2592再次交叉核对。冻结JS手写G更新仅原有NPC/area预留容量/指针、phase1和clock2352，没有在构造后写56/120/2364来制造空域。

2,763条packet和22条notification的完整描述/载荷已保存，独立核对逐case单调index、队列累计数量、opcode、payload长度和内存界限；载荷共132,197B与14,689B。915自身没有新增消息。此结论确认观察数据完整，不等于这些物理包已具有独立序列化模型。

本批是观察性插入与运行前已有no-op假设比对，**不是新915独立模型验收**，也不证明非空56/120或所有producer已恢复。真实entry仍是受控phase1、128槽预留；完整880和其他阶段尚未执行。原件没有被本复核再次运行，作者源未改。[最终独审证据](../evidence/effect-system0135-probe-independent-review-20261101T072258.540793Z/review.json)。
