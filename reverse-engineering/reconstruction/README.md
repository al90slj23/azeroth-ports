# 独立核心的可执行规格

本目录保存自己实现的规则代码，目标是逐步组成能独立运行的替代核心。**当前主目标为官方0.134.0**；升级值、80B拥有记录更新的限定域、新扣血和120级经验投影已经过新版原件对照，其余历史模型正逐项迁移。各自确切范围见[版本支持清单](version-support.json)，不能直接视为新版全部行为。当前还不是可玩游戏，现有Mac/Android安装包继续保持原样。

- `core_spec/binary32.py`：精确有理数运算后按IEEE binary32 nearest-even逐步舍入；NaN载荷不保证保留。
- `core_spec/upgrade_values.py`：五种升级值计算，输入为明确的状态字段/原始浮点位，输出为binary32位。不会读取或执行原游戏。
- `core_spec/enemy_scaling.py`：普通/精英的两条生命成长曲线，保留运算顺序；不包含完整生成公式。
- `core_spec/radius.py`：原35684的log1p家族近似与半径软压缩，逐操作建模；不以语言标准数学函数替代近似。
- `core_spec/progression.py`：85387舍入、等级阈值及XP/pending数值投影；不包含原3231的属性/治疗/消息/选卡副作用。
- `core_spec/progression134.py`：新版85718阈值、120级上限、u32 XP/pending绕回和选卡资格守卫投影；phase3完整原4630的2197例四字段一致，真实候选生成/消息/治疗独立实现仍缺。
- `core_spec/rng.py`：四字递推与32475区间采样，含拒绝重抽；不包括seed初始化或全游戏随机时序。
- `core_spec/derived_stats.py`：22派生属性、当前HP、四套tag及32B实时效果；输出对象字段和移动更新决策，未实现真实modifier生成方。
- `core_spec/ability_state.py`：80B拥有能力、真实升级顺序、新tier0初始化与选卡控制投影；未实现后处理显式pending，未知新tier明确拒绝。
- `core_spec/combat.py`：命中基数/暴击、伤害加区/上限、HP/统计/死亡主字段；完整死亡XP/loot/RNG和触发仍未闭包。
- `core_spec/combat134.py`：新版424B单位状态、M加区/新T36B rawtag50/51/阶段系数、HP/有效伤害/死亡主字段的独立投影；保持`amount*(M+T)*P`的逐步f32顺序。不是完整施法、触发或死亡管线。
- `core_spec/incoming134.py`：新版玩家减伤/盾消费与barrier替换标量规则的前缀；所有未实现回调显式pending。139例非致死空状态的选定最终字段与完整原1063一致，盾耗尽、复活/死亡、完整施法未验收。
- 原件函数对照器在 `../scripts/check_*_spec.py` 和 `../scripts/check_enemy_scaling.py`；生成的WASM、输入及结果仅写入被忽略的 `../evidence/`。

```sh
# 新版0.134.0的实际原件差分。
python3 reverse-engineering/scripts/check_upgrade134_spec.py
python3 reverse-engineering/scripts/check_selection134_full_spec.py
python3 reverse-engineering/scripts/check_combat134_full_spec.py
python3 reverse-engineering/scripts/check_progression134_full_spec.py
python3 reverse-engineering/scripts/check_incoming134_nonfatal_spec.py

# 历史0.126.0的隔离数值对照。
python3 reverse-engineering/scripts/check_upgrade_spec.py
python3 reverse-engineering/scripts/check_enemy_scaling.py
python3 reverse-engineering/scripts/check_radius_spec.py
python3 reverse-engineering/scripts/check_progression_spec.py
python3 reverse-engineering/scripts/check_rng_spec.py
```

升级数值、敌人成长、半径等命令执行原件纯数值函数的隔离复制体，不启动完整游戏。这些复制体没有host imports、start、网络、时钟、图形或存档接口。升级模块保留函数索引，仅导出计算函数和固定内存，其他函数为trap；敌人成长模块只有两条无引用函数；半径模块保留单一helper和一页scratch内存。复制体均重解析并核对原体哈希，WABT验证后才交给Node。

新版完整选卡与扣血工具另用`build_full134_oracle.py`：只修改export节，保留所有原内部指令和callee。`full134_host.mjs`复核固定原件、原导出前缀及全部非export节；878宿主导入均拒绝，应用入口不调用。它们确实实例化完整官方模块，但只以原分配器构造的合成状态调用指定内部函数。选卡779例与扣血454例均0差异，宿主实际调用0次；前者生产后处理仍pending，后者未独立实现完整死亡loot/RNG。详见[新版选卡](../reports/2026-11-01-selection0134-spec.md)与[新版扣血](../reports/2026-11-01-combat0134-spec.md)。

历史0.126.0：升级11560组、敌人成长24636组、半径helper/外层组合29041组、经验helper/重组30125组、RNG18144组均0差异。半径和XP外层为JS/f32重组，没有执行原934/3231；NaN类别比较不包含payload，非法档位/区间仅比较替代panic trap。边界及证据见[升级](../reports/2026-11-01-executable-spec.md)、[敌人成长](../reports/2026-11-01-world-progression.md)、[半径](../reports/2026-11-01-radius-spec.md)、[经验](../reports/2026-11-01-progression.md)、[RNG](../reports/2026-11-01-rng.md)。这些独立规则尚未组成可玩流程。

生产规格只依赖Python标准库。对照需要研究区已经安装并校验的Node和WABT，以及固定原始WASM；原始游戏文件不加入本目录或Git。全模块覆盖和完成标准见[重造工作基线](../RECONSTRUCTION.md)。

后续完整函数对照与早期微模块分开：`build_full_function_oracle.py`仅给原0.126.0增加批准函数导出，所有其他section逐字节保留；所有878个宿主导入设为拒绝，应用start不调用。属性8495、完整选卡5、完整扣血32，以及暂停域完整XP1954份对照，验证范围各自列在报告。这些工具仍固定旧SHA，不能给新版强行套用旧函数索引；新版有单独profile。
