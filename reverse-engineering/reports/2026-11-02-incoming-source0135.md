# 固定135：普通敌人来源到受伤历史

新独立[`incoming_source135.py`](../reconstruction/core_spec/incoming_source135.py)和已有受伤／48B history规格组合，**163组完整1073原件调用，0声明差异**。[独立只读审查通过](2026-11-02-incoming-source0135-independent-review.md)；没有接入连续headless或宣称完整1073全部副作用。

固定0.135.1／`90898d5e3`，WASM SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。最终[比较收据](../evidence/full0135-oracle-20261101T235458.632785Z/incoming-source135-comparison.json) SHA `84accac68189bdf3bb55dc41118e67fff3c36c6437512373ec31d2c3182459e9`。

## 来源规则

这是1073中第二次GUID查找，用于history来源文字和分类。按真实424B向量顺序比较U112，首个匹配记录胜出，marker1的已死亡记录也不跳过。无匹配时来源空串／分类4。匹配后依次区分U244的custom、U40的summoned与ordinary分支；本模块只接ordinary，另外两类明确停止。

ordinary分支读取U284定义指针，经58162使用已解析本地化名字或定义+16/+20英文fallback；U284为0时来源空串。history分类直接读取raw U416，不能从GUID或NPC表classification猜出。本轮显式使用fresh English fallback与148个普通NPC定义名；语言翻译表的完整producer没有恢复。

原件输入只有完整source424记录、GUID、标量和history初态，没有期待名称／分类。语料覆盖全部148个英文普通定义、raw rank byte、第二槽匹配、重复GUID首个胜出、死亡记录匹配、null definition、零GUID及phase guard。162次追加history，1次phase guard；原件全部callee保留，来源记录的actual postbytes也逐字落盘。

20源／9production执行前后不变。21个fresh实例，32MiB上限，峰值20,578,304B；878宿主导入全拒绝，实际0。Node76947在0.831秒exit0，PID／PGID消失，60秒自有期限。history严格比较5508个已知byte，资源指针1944次及allocator未写23652次保留未知及实际观察，不预测为0；每个active来源／技能／icon字符串另逐项比较。

先前3例pilot与早先163例只保存source prebytes＋runner不变断言，均保留。为让独审直接读取actual post-source，改进捕获后新跑最终163，计数不相加。

这里没有恢复更早的G1112伤害来源统计registry、全部keyed物理布局、反击／proc、custom／summon、Spell数据库、本地化producer或死亡复活。实际921帧的终局还需要接入完整incoming/history以及非平地世界的停止运动查询；不得把callbacks_complete或terrain_absent设真绕过这些依赖。没有访问安装包、存档、网络或EXE。

独审重新从原WASM提取148个英文名字、独立核对69,960B source实际post记录、2282个标量、所有声明history字节与字符串，0差异；20源／9production／32本地导入边。rank7／255仅证明metadata字节消费者，不因此扩大1367仅五分类的recap域。
