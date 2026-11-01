# 0.135.1 learned80 主施法链独立只读审查

结论：在显式空item/definition/proc、普通非致死目标的域内通过。最终依据为 [045930 receipt](../evidence/full0135-oracle-20261101T045930.365818Z/owned-cast135-comparison.json)：**639 cases、5,924入口阶段、4,923次accepted hit**。用最终冻结生产模型从既有fixture输入独立重放，预期全部重现；再比较既有原件结果的541,566个叶值，没有不可接受差异。60处float NaN payload/sign差异按NaN分类接受，不称逐bit相同。审查没有运行原件或修改生产源。

后续scope erratum：下文embedded basic80是当时G1256槽effect0隔离fixture的标签；真实1560后来确认该槽为racial80。本历史独审没有验证真实racial初始化/执行；后继[构造151](2026-11-01-initial0135-independent-review.md)、[racial720](2026-11-01-racial-cast0135-independent-review.md)及[新headless](2026-11-01-headless-area0135.md)单列。这里仅纠正文案，不冒充对旧源码的新复核，原review证据及SHA保持不变。

本次真实入口为1076 learned80与G1256 embedded basic80，随后1754处理命中队列；916的额外84B timed/proc系统不是本次主路径。原件WASM SHA、全部33份源码快照与artifact哈希吻合，当前源码无漂移；除export section7外所有原件字节逐段一致，新增1076/1754角色和body SHA吻合。生产相对导入闭包及执行包入口 `core_spec/__init__.py` 均被覆盖。

逐hit顺序为914核心结算、必需的after_hit消费者、再进入显式death消费者。4组raw0/negative area语料的24次回调全部收到最终minimum1伤害，玩家HP逐次自疗；同GUID投射语料保留8次独立回调，没有按GUID合并。实际1754稳定分离到期和未来命中，按原队列顺序处理到期damage>0项；模型保留相同顺序。

独立负例确认missing after_hit、非空item/definition、未声明空域、extra1596、refresh772、context908及缺失death消费者均拒绝。20个NaN字词探针确认owned/basic记录只有明确浮点索引允许NaN分类相等，level/counts/target counts、player keyed整数、GUID字符串、RNG与累计f64hex不被掩盖。九职业及fallback的prelude还按实际初始内存表检查了全部256个class byte所读取字段。

审查发现原32源清单遗漏包入口，root补入后重跑，最终使用33源版本。旧批只冻结当时列出的文件，其历史包入口未记录SHA；旧receipt及旧review证据不改，旧计数不升级为这次新证明。补充见 [provenance caveat](../evidence/owned-cast0135-independent-review-20261101T045826.625090Z/previous-source-provenance-caveat.json)。

本次不证明完整2088/880整帧调度、非空proc域、致死奖励/死亡RNG、完整112B hit envelope、网络包字节、视觉及治疗account日志，也不证明整个游戏已经重造。完整审查与可复算脚本见 [review.json](../evidence/owned-cast0135-independent-review-20261101T045826.625090Z/review.json)。
