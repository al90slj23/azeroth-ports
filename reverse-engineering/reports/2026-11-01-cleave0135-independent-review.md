# Cleave 0.135.1 独立复核

结论：**PASS**。只读复核现有收据、源码快照和静态片段，未执行原件。

- 已重新生成 351 组合成输入及独立期望，与封存 fixture 逐对象一致；1923 阶段、1845 次 accepted hit 的原件输出无差异。
- 37 个源码的当前字节、前后 SHA、封存快照一致；10 份产物 SHA 一致。原 WASM SHA 固定，所有非 export section 与原件逐字节相同，无隐式 start。
- 静态复核 execution5 目标数与 range7 →8685→43468→914→2244 effect0；exec7 专用排序/低血倍率未套入 cleave。
- 8 个纯模型保护检查通过，包含旧默认拒绝、未知 effect/ID/context、重复 GUID、错 pointer 和保留剩余目标的致死边界。这些检查不新增原件验收案例。
- 私有export-only模块额外只导出global0；2976 次对外 entry/allocator 调用前后栈均为1048576。Global对象与setter不外露，未对内部callee逐个插桩。输入与旧轮逐字一致，旧轮计数未重复相加。
- 真实 UI owned80B 只用于迁入合成 fixture 的数据形状。此结果不代表自然 Game、880、完整一局或原真实场景重放；物理包、死亡掉落和非空来源继续保留为边界。NaN位置未纳入边界组。

G1256 是 racial80。旧 fixture 中带 real-basic 的组名仅表示该槽放入实际目录中的非空 canonical 记录；没有重放真实 racial 定义或计时状态。

原差分收据：[cleave135-comparison.json](../evidence/full0135-oracle-20261101T141458.138874Z/cleave135-comparison.json)；复核明细：[JSON](2026-11-01-cleave0135-independent-review.json)。
