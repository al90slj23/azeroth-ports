# 官方0.135.1新能力初始化与完整原1072差分

固定 **0.135.1 / 0898d5e3**，原WASM SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。新独立 `core_spec.ability_state135` 使用新初始data重新提取的114个定义和tier表，对**完整原1072**完成 **2,781例、0字段差异**。其中全部114定义×tier0..4共570例，额外tier5表项114例另列，不声称候选会自然生成tier5。

新能力入口在1072，辅助26967/26591仍保留索引，舍入helper为85719。definition table为5467428/stride88/count114；cooldown表5884284、damage表5884336。原选卡phase2587/kind2585，owned cap/ptr/len1656/1660/1664，candidate1904/1908/1912，pending2376。所有地址由本版完整指令和初始data核对，不统一平移旧地址。

模型独立实现显式20B modifier快照的按序f32累加、ID/ID-list/school/execution筛选、targets先累加再round/saturate、冷却NaN/select下限0.4，以及tier分类后的伤害或冷却调整。覆盖七个额外word、modifier全部分派、顺序/二进制32位边界、真实与合成definition分类、owned append保留和入口guard。`modifiers=None`仍明确报未知，只有调用者已确认空向量才能传`()`。真实天赋/装备producer尚未恢复。

完整1072与到达的26967/26591/85719和共享尾部均为原件指令，仅增加研究export；独立API仍把通知、天赋/装备后处理、1512属性重算与4600收尾列为pending effects。每个owned80B字的比较对u32要求精确，浮点非NaN要求原始位相同，NaN只比分类。成功域为kind0新能力，其他kind只验入口拒绝；不接受kind1/2成功队列的完成声明。

最终证据 `evidence/full0135-oracle-20261101T034346.401772Z/new-ability135-full-20261101T034438.140835Z/`。87个实例，峰值20,774,912B；固定Node22.23.4、512页内存、60秒owned进程截止，exit0、宿主调用0，全部878宿主导入throw。原始36个exports、全部非export节和callee字节保持不变。参与源码与结果/输入/manifest均前后冻结并保存源码快照；相邻JSON记录哈希和比较范围。

少量复用模型docstring/error仍保留134标签，表示继承实现的历史文本；实际135原件和字段以本报告、static-manifest和runner为准，未据旧标签定位或转记验证次数。首轮21例pilot不加到2,781例full覆盖。没有调用应用start、网络或用户存档，未改安装包。复现：`python3 reverse-engineering/scripts/check_new_ability135_full_spec.py --phase pilot`，再按输出目录执行`--phase full --full-directory <目录>`。

独立只读复核重新生成全部输入/期望并比对持久原件结果，源码快照、原件及export-only模块绑定通过；复核未重跑WASM，收据与SHA见相邻JSON。
