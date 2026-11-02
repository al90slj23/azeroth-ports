# 0.139 经验球与金币1446独立复核

当前kind0经验球／kind1金币的声明域通过。43次完整1446、24个经验球输入与19个金币输入全部独立重算一致；复核未执行作者生产代码、检查器、构建器或原件。

几何从当前139本体重新绑定：1446使用50441的hypot算式，将半径限制到zoneRadius−2，本地图为118，再查询当前地形；primary缺席时按真实fallback高度。期望地形只读取root从原始资产独立生成的canonical数据，不读取原件memory。4个clamp场景的XY/Z和后续消息均一致。

经验球达到45个闲置对象（kind0且marker0）后，按XY距离的严格total-order比较选最近项，平局保留先出现者，amount按u32回绕。3次merge均只改amount，没有新GUID、counter、RNG或消息。44个闲置对象的边界仍追加，容量按max(4,2×旧cap)增长。新56B记录只写52B，4..7的4B未写区以及新分配的闲置槽保留None；已有caller backing的字节全部保留。

显示规则单独核原件覆盖顺序：经验量0..3用0.22，4..19用0.35，超过19时后续store会再写为0.9，并改用display16587。不能漏掉最后一次覆盖。金币1886的counter/u24GUID、uniform上界拒绝、yaw和半角sin/cos也从当前139重新绑定。

40条新增完整169消息共5052B逐字节重建，含packedGUID、XYZ/yaw、速度、逻辑BTree的field mask及所有值。17996个known字节完全一致，8884个None保留；6205个实际非零的未知字节没有回填。43组2592B原始Game中109564个非声明写入字节守恒，RNG、counter和容器count/cap均相符。物理BTree树形和分配地址不在独立实现声明内。

当前12个完整函数本体、签名、export-only模块和23来源／13生产文件／44导入边均核SHA。原件runner报告43个healthy-v2恢复实例、882导入拒绝、0host、108次栈检查；这些是冻结runner观察。原件PID60386与独审PID86670均exit0且PID/PGID消失。没有重新执行1600、6786或世界owner生产。

首次完整43例的5处packet差异源于漏写0.9，旧源SHA4059122c…与abf7125a…失败收据完整保留，pilot2也单列。这一研究实际共88次1446调用，本次只将修正后43例作为覆盖，没有把失败或pilot累加为通过。

作者comparison已散列固定stdout、terminal等输出；runtime JSON没有单独列入artifact表，但其完整内容与comparison内联runtime一致，独审另固定当前文件SHA。该边界如实保留，不改旧收据。Pythonopen审计不等于OS系统调用审计。

最终收据：`evidence/death-pickups139-independent-review-20261102T053201.026803Z/review.json`，SHAd495ff1b19a5b49b482b86e2e2e106855cbc33b03db02843de0217970d1d7c78。完整913死亡、经验球拾取／升级、其他kind、primary-present地图、自然App、完整游戏及Windows执行仍未验收。
