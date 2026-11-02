# 0.139 自然位置组件独立复核：80结果一致，源码未验收

结论：保留本批80个原件结果与独立参考输出一致的事实，但当前组件不验收。发现13563距离计算顺序与原件不一致，并已提供能区分两种算法的有效clamp输入。没有执行作者生产模块、检查器、构建器或原件。

## 具体问题

`reconstruction/core_spec/world_position139.py:100` 用`hypot_bits(dx,dy)`计算13563前12次试探的地图中心距离。原件完整13563第141行却直接采用每次乘法先舍入为f32、f32相加、f32.sqrt；没有调用50441。hypot辅助函数是在f64中平方并相加后才demote到f32，顺序不同。8740的三处距离查询确实调用50441，不能全局替换hypot。

独立当前WAT/raw139world参考找到了第一trial即接受、nav为0、height有效的反例：

- playerXYZ `[3323121664,3292266496,1116209152]`，velocity `[0,0]`，半径26..36，RNG `[2604202828,455852230,828458172,3706585583]`，无pathMap。
- 原件WAT的f32距离位型1125604199，独立预测XYZ `[3323133279,3292274078,1116194242]`。
- 旧hypot算式的距离位型1125604200，独立预测XYZ `[3323133279,3292274077,1116194241]`。
- 最终RNG相同：`[3280341869,274167459,1172006293,3649586427]`。Y与Z各差1ulp。这里两组是纯参考推导，尚不是新原件观察；完整输入及来源在`evidence/world-position139-review-work/counterexample.json`，SHAcbc42c1bdc0bf26ca72b390bc3b7273d63e3e1241ec3ff3af5526f4411d591ad。

实现代理已收到反例并保持旧10件冻结，后续用独立新版本修正callsite，再做包含反例的fresh expected-first原件验证。不能以现有80条没有触发差异来忽略此源码问题。

## 本批实际核对范围

80个当前原件调用（63次完整8740、17次直接13563）按真实f32距离规则独立重算仍全部一致；原件RNG最终四词、XYZ、206080个非RNG Game字节及1280个RNG字节均核对。路径field400没有值backing时按真实分支惰读；field401与其他阈值、0/65535/500cost、偏移概率/速度阈值、收缩和16→13回退均由当前WAT恢复。attempt/draw/fallback计数只作独立参考诊断，不称原件直接观测。

只读重算期望仅使用root从139原始资产独立生成的terrain/nav/secondary canonical文件，没有读取原件memory。独立旧数学参考只复用纯height/triangle计算，绑定当前139五getter的完整静态与独审收据；没有转移旧135案例或旧actual/expected。原件侧使用已核合法v2 context（R20544696、G14685248），不使用旧坏snapshot。

输出目标只写12B，16B返回区域末4B A5和前后各16B canary均保持。world124与2318个range/5950608B的前后digest不变为冻结runner的只读观察，不是独立WorldRc生产，也没有由复核重新读取snapshot重算这些digest。路径view不变由冻结runner检查。Pythonopen期望读取审计只有三个canonical及其receipt，明确不是OS系统调用审计。

25来源/14生产文件/49导入边、10作者文件及快照SHA一致；原件仅增加导出，其余段逐字节保持。882导入全部拒绝、实际0host；80次snapshot restore、102次allocator与80次入口合计182个栈检查是runner断言与汇总。原件79403与最终复核37891均有exit0/PID和PGID消失收据。自然pathMap owner、App/world所有权、完整1108、native或完整游戏不在此次验收范围。

最终独审收据：`evidence/world-position139-independent-review-20261102T042537.052543Z/review.json`，SHAa9a83567b6f9c0873dff1e858ad2f032249952f108055a9523ded2eaa0392aea。首次80一致但finding-open收据及一次复核静态断言失败原样保留。当前状态为`not_accepted_source_fidelity_finding_despite80_output_matches`。
