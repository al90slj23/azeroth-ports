# 官方0.135.1有序升级记录应用

独立 `core_spec.ability_upgrade135.apply_upgrade_card` 复用已独立实现的有序数值循环，definition pointer、ID与execution取自新[114能力目录](2026-11-01-catalogue0135.md)。在固定 **0.135.1 / 0898d5e3** 的完整原1072上重新验证 **3,629例、0差异**；未把0.134.0结果转记新版。

775例覆盖cleave上1..3个kind按所有顺序、重复及tier0..4组合；2,850例覆盖114个实际definition×5个kind×5个tier。另4例包括phase守卫、空kind不访问非法tier、owned index越界仍收尾及已知空modifier的新tier0初始化。未声明全部kind对每个定义都能自然生成；后者是直接构造原始合法kind字节的函数域对照。

每个kind先加level，再按原25368计算并更新对应数值/count，最后应用依赖level的新伤害因子，按列表顺序逐个执行。比较完整80B owned记录以及count1664、phase2587、kind2585、pending2376和candidate count1912。所有本语料word均精确比较，未放宽整数或有限浮点；起始record为level1、counts0与明确中性参数。更广record输入、真实producer与选卡消息/天赋后处理仍待连接。

完整原1072及共享callee不改，真实原分配器91941、36个原exports保留，仅增研究export节7；878宿主导入全throw，实际调用0。114个新实例，峰值14,942,208B，Node22.23.4及512页上限，owned进程60秒截止，exit0。源码、fixtures/expected、原结果、模块/manifest前后冻结并读回复核。最终证据 `evidence/full0135-oracle-20261101T034736.621817Z/`，相邻JSON保留收据和哈希；29例pilot仅探路，不加到full覆盖。

生产API只返回独立record变更，原件的1512属性与4600收尾虽然实际执行，不等于API已独立实现它们。此报告和[新能力初始化](2026-11-01-new-ability0135-spec.md)、[候选metadata](2026-11-01-candidates0135-spec.md)分别验收；完整kind0流程、UI/world/网络与自然一局没有由各项通过自动成立。复现：`python3 reverse-engineering/scripts/check_selection135_full_spec.py --phase full`。未调用应用start、访问存档或修改安装游戏。

独立只读复核重新生成全部输入/期望并比对持久原件结果，源码快照、原件及export-only模块绑定通过；复核未重跑WASM，收据与SHA见相邻JSON。
