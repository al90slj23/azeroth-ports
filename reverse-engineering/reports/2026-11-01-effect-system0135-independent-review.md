# 0.135.1 delayed56/915组件独立只读复核

**500组、2121阶段通过**：383正常返回、117预期raw255在pop后真实unreachable。两类分开，未把trap计为正常玩法。冻结模型重生fixture及逐action重放严格匹配保留原件输出；5项未知域guard重放通过。

17源快照及包含package init的完整闭包通过；原件全部非export节逐字节一致，915body/导出身份通过。当前漂移见JSON（若为共享导出扩展，只说明原批仍绑定其冻结源码）。

另逐一核对915、4543及8个callee的原件body与WAT身份。独立字节算法复核due/owner筛选、稳定56B压缩与完整尾槽、raw255先pop后trap、outer marker低位与4543独立marker!=1查找，以及16槽aura首次匹配归零。完整56B backing与424B单位记录全部严格，无字段mask或NaN分类放宽。clock/due的NaN payload按原始字词保留。

非空120B效果在进入前拒绝并原样保留；ordinary910只返回真实pop后的pending边界。特殊35/36仅有限平地且geometry来源显式缺席。RNG/counter保持、player XYZ/action词、消息opcode顺序均对照；原物理payload只保留侧录，未独立恢复wire、消息GUID或几何编码。真实producer、120/910、完整915/880及完整游戏仍未验收。

没有重跑原件或修改作者源码。证据：`evidence/effect-system0135-independent-review-20261101T073734.885524Z/review.json`。
