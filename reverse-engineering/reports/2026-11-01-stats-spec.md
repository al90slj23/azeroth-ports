# 1573独立属性规格：真实原函数与全部内部callee差分

目标为 **0.126.0 / 3e72472a**。已新增可执行的独立属性模型 [`derived_stats.py`](../reconstruction/core_spec/derived_stats.py)，并在受控合成状态上直接调用**原完整1573及其原内部callee**：**8495例全部通过，0字段差异，0 host调用**。这次不再只有静态摘要，也不把替代allocator的测试冒充完整原callee验收。

原WASM SHA-256：`067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c`。原1573的4479字节body SHA-256：`e05c38868e23157be89c2ac8030ef941ce24f583758c2e3c5f9d29cda8d5db07`。生产模型不读取原WASM、WAT、索引、真实存档或网络。

## 独立实现的内容

模型输入全部以u32及binary32原始bits表达，输出22个`G1176..1260`字段、当前生命`G1344`、速度值和更新条件、对象字段22/28/1109，以及实时效果被接受的记录索引。每条加、减、乘、除独立经过共享`binary32.py`舍入；没有修改共享算术。原select比较顺序、NaN行为、有符号零选择及u32回绕保留。

- 职业和种族byte选择，包括6/10回到Warrior、未命中回到Warrior/Human；9职业HP/护甲和8种族修饰使用独立常量。
- `f32(u32(level))-1`建立基础伤害/恢复/HP，不先夹等级；1244保留饱和转换后的u32加1回绕和上限3。
- 种族8B、被动8B、调整16B、物品8B各自的tag分派；tag0及超出表范围的默认分支单独保留，不能共用一张语义表。
- 物品tag32按原顺序从负零求和，严格大于0后查找**第一个**9字节`soul_link`；只有其u8等级非零才追加tag5的`rank*.01`。
- 12B限时记录对应36B定义：保留`expires <= now`跳过条件、索引边界、定义kind27、u32层数转换及追加顺序。`now/expiry`为NaN时不改写为普通布尔时间判断。
- 32B实时效果：当前过期检查；同spellID的其他仍有效记录比较；spell774免去同spell支配扫描；type8/9强弱及先出现者的相等优先规则；type非8/9使用零比较值；23451额外移速`.6`、23505额外伤害`.5`。接受项的数值按原遍历顺序累加。
- 最终HP、haste倒数、暴击溢出转倍率、速度2.2上限、护甲cap与两条护甲转伤害项、比例/平值恢复、1252派生比值和当前HP上限调整；对象字段使用原ceil和饱和u32转换。
- 移速变化的`abs(newSpeed-oldSpeed) > .01`判定；独立模型返回是否产生更新，真实原函数实验另验证序号与队列计数。

调整tag5的特殊组合现已独立恢复：护甲加`minNum(value, definition32*3)`，HP倍率加`value*4`。调整tag6的护甲加`minNum(value*.16,.12)`，并加HP倍率value。这里没有根据名称猜测真实装备/天赋ID。

## 两层原件实验与证据边界

第一层保留原1573完整body与全部175681个函数index，其他函数为trap，只有106495、65045、71577换成受控WASM arena分配、8B向量扩容、free计数shim。既有BTree键和匹配速度排除了插入和消息路径。8483例全过，确实运行过1740次分配shim、750次扩容shim、1855次free shim。这一层只证明**替代分配依赖下的原body数值执行**。

第二层使用[`build_full_function_oracle.py`](../scripts/build_full_function_oracle.py)生成的完整原模块研究副本。**仅section7添加导出，所有原函数body、数据、table、globals、memory和其他section逐字节保持**。原模块没有隐式WASM start；没有调用应用`start`或其他启动导出。878个host imports全部设置为立即抛错，实验实际调用次数为0。合成状态和所有向量、定义均由原106495取得；每64例重建实例，避免覆盖原stack/static/heap。

[`run_full_stats_probe.mjs`](../scripts/run_full_stats_probe.mjs)是根任务先做的**单例baseline探针**：它只证明Warrior/Human/level1空辅助状态可以调用原1573，并生成原BTree和移动队列。本报告的8495例结果来自另一个完整矩阵runner [`run_stats_full_oracle.mjs`](../scripts/run_stats_full_oracle.mjs)，其研究模块同样只增加导出；它实际逐例运行原1573及全部到达的原callee，再与独立模型比较数值和副作用字段。单例probe不计入8495例，也不作为四套tag、限时或实时效果已验收的证据。

此层没有替代任何callee：真实65045和71577处理临时向量，真实3736从空map插入22/28/1109，真实47820和队列扩容在需要时构建移动包。8495例产生**25485次对象字段插入、1483条移动包入队**；所有22个派生字段、当前生命、3个对象字段、1456速度、1452序号、1696队列计数均符合独立模型。133个实例，最大内存14811136字节；项目固定Node最终复跑：micro执行0.236秒、完整原件执行1.871秒，进程上限60秒、WASM内存上限512页。数据写进原内存与包队列已经发生，外部消息投递没有执行。

| 输入族 | 完整原callee例数 |
|---|---:|
| 全部职业byte选择 | 256 |
| 全部种族byte选择 | 256 |
| 9职业与等级边界 | 981 |
| 被动tag及非有限/零值 | 345 |
| 调整tag及定义辅助值 | 810 |
| 物品tag及非有限/零值 | 645 |
| 当前/最大HP select组合 | 225 |
| soul_link、重复ID、tag32求和分组 | 525 |
| 限时记录失效/NaN/层数/无效索引 | 180 |
| 32B类型、强弱、相等、774及特殊ID | 3600 |
| 32B失效与非有限时间 | 60 |
| 固定种子混合有序记录 | 600 |
| 移速阈值及非有限旧值 | 12 |
| **合计** | **8495** |

所有非NaN输出逐bit比较；NaN只比较分类，不承诺payload或符号在不同引擎一致。原件实验不是把独立模型编译成WASM后再同自身比较：完整原模块只增加内部函数导出，原1573和内部callee没有改写。

两套检查器现都使用项目绝对路径`.toolchain/runtime/node_modules/node/bin/node`，版本固定为 **v22.23.4**，运行前后核对SHA-256 `2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0`。两层均设置`--max-old-space-size=512`及`--wasm-max-mem-pages=512`，独立进程组60秒超时后终止；运行时path/version/SHA、flags、退出码、耗时和stderr哈希写入各自comparison。最终运行的`micro-oracle-stderr.log`和`full-original-stderr.log`均为0字节。持久化fixtures与results的ID、完整覆盖、顺序和唯一性也已核对；另有4例重复/乱序/缺失/布尔ID拒绝检查。

初版检查器依赖`PATH node`；审查时该入口为v22.21.1，初版没有固定或记录运行时。旧证据仍保留在`evidence/stats-oracle-20261031T234900.686987Z`，最终结论改绑定到项目固定Node的新目录。模型未变，最终两层的fixtures和原件输出哈希也都与旧运行相同。


## 复现

```sh
# 独立body + 明确分配shim层；命令会创建新的ignored证据目录。
python3 reverse-engineering/scripts/check_stats_spec.py

# 原函数及全部原内部callee层；先生成只增加导出的原模块研究副本。
python3 reverse-engineering/scripts/build_full_function_oracle.py --functions 1573 71577 106495
python3 reverse-engineering/scripts/check_stats_full_spec.py \
  --full-directory reverse-engineering/evidence/full-function-oracle-20261031T234819.732432Z \
  --output-directory reverse-engineering/evidence/stats-oracle-20261101T001221.774880Z
```

本次证据位于`evidence/stats-oracle-20261101T001221.774880Z`，两层comparison、全部fixtures、逐例原件输出及模块/函数/静态片段hash均已保留。完整原模块研究副本位于`evidence/full-function-oracle-20261031T234819.732432Z`。公开JSON绑定证据及源码hash。

## 仍未证明的部分

合成记录覆盖1573的数值分派和所述副作用，但不自动恢复每个modifier的真实装备、天赋、技能来源，也不证明真实存档兼容、原游戏启动循环、UI、网络交付或全游戏独立运行。独立模型以记录为输入；真实记录生产、失效及其他系统的调度仍需对应模块继续实现。此报告不把孤立函数通过写成全游戏验收。
