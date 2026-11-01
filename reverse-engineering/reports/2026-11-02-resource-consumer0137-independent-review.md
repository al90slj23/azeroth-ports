# 最新137资源消费只读独审

**通过声明范围的独审。** 固定0.137.0 / d171b8f9f，156个fresh实例、250阶段：171次完整10291直接调用及79次完整2862调用，声明投影0差异。本次没有执行原件、模型、checker、builder或toolchain命令，0新增original case、0完整880、0native Windows。[最终独审收据](../evidence/resource-consumer137-independent-review-20261101T191616.444214Z/review.json) SHA256 `ccffb6c554356e6cb6eeaa6b75ae3310812dfb819a2c9d9ec3629f8c8481b001`；[结构化报告](2026-11-02-resource-consumer0137-independent-review.json)。原[comparison](../evidence/resource-consumer0137-oracle-20261101T190800.110757Z/comparison.json) SHA `5797efa62a4852134823656d80c92644b865234f975ab135ab456e217ba065b8`，范围见[主报告](2026-11-02-resource-consumer0137.md)。

32份冻结源与审阅时当前源SHA全部相同，23份production恰好构成完整导入闭包，82条本地Python/JS边独立核对；未发现生产直接文件或动态代码执行调用。私有模块只追加10291、2862和global0三个export，所有非export section、code/data和callee保持原件字节。10291真签名为(i32,i32)→void，2862为(i32)→void；11个静态函数通过RO SQLite、原body范围与SHA交叉核验，有界读取340,881B WAT，没有全读大WAT。

独立重比33,127个已知值及13,650个physical未知byte，其中964个原件byte非零。审阅器另从冻结输入重建每次live32的同spell稳定删除、完整32B移位、append写集与容量增长，以及pickup56的完整反序压缩和inactive尾部。+12/+16的已知部分及None随原槽/移位记录保留；新分配的真实未写字节保持未知。独立重建结果必须同时等于事先冻结的expected，再与原件逐byte比较，没有扩大None到标量或整行。

kind3写effect0/spell23451、expiry=f32(now+10)，激活速度倍率+0.6；kind4为23505/15秒、伤害倍率+0.5。同spell清理包括所有64-bit owner与已过期记录，稳定保留其他记录。kind5按f32(maxHP×0.5)请求治疗，G387>4再乘0.5，HP封顶maxHP；不调用1514/1151。本审从显式输入baseline23词独立应用active去重spell增量、速度阈值与G1644、治疗与ceil对象HP字段，未执行共享数值producer；其余baseline词是声明输入，不能扩称完整137统计或constructor已恢复。全部23派生词、HP、speed、G764等4个辅助词及已声明的key22/28/1109均严格重比。

独立XY f32平方/加法/sqrt≤3确认27个近身资源，不读取其Z或amount作为奖励。按原下标反序调用的静态路径先31727、后10291；所有170 little-endian GUID8B payload及其累计队列顺序与独立预测一致。171直接effect加27个full2862内部effect的输入/状态推导，共198次效果对应kind3×75、kind4×74、kind5×49；这些27项不另作case或被instrument的外部10291入口。50次同spell删除、97次live容量增长、62次速度序号变化、16次门限减半和24次治疗封顶均独立核对。RNG四word、G2408和G2412全程保持声明输入值。

每阶段raw Game8192与已声明标量/vector header、physical storage、selected keyed fields、packet/notification metadata及payload长度重新绑定。raw aura48×16B、其余keyed字段、722相关通知和其他wire语义仍是观察；没有用非空payload的存在冒称预测完成。789 packet和318 notification是累计队列在不同阶段的snapshot计数，不能当作新增消息数量。

原件没有注入Once或locale：每例prestate28B为真实初始零状态；138例经未修改的19971→82064从0初始化为3，14项dictionary header及effective English index0可核；18个全远处用例未触发效果，保持0。只证明该宿主域中的原初始化正常运行，不等于14语言行为全部验证。

marker2的174输入旧批与单例均exit1且runtime为None，原错误栈保留2862→31727→80657→90663→49510。`differences:0`来自未执行比较，不是通过；这两批host调用次数未知，未标0host。31727先memory.copy/减count再走marker2 panic的次序有静态依据，但失败批没有trap后完整Game捕获，本审不宣称partial字节已动态验收。最终阳性仅live marker0/1，模型对marker2与非空claims的拒绝只读核对，未重跑拒绝测试。

最终原件PID/PGID75893退出0、9.256秒、审阅时均missing；32MiB WASM cap，峰值20,578,304B，512MiB heap，878 imports全deny且实际host0；625条入口/allocator栈检查均正常返回并恢复1048576。本审[owned终态](../evidence/resource-consumer137-review-owned-20261101T191616.364174Z/process-terminal.json)为PID/PGID96190、exit0、0.709秒、无timeout、两者missing，符合60秒预算。

Game8192、空来源向量、初始BTree与backing为手工受控输入，不是137 constructor；只覆盖mode0/effect0及空外部装备/天赋/timed来源。producer1420与consumer2862尚未在同一原件完整游戏循环连接，其他近身kind/XP/金币、claims/auxiliary、完整aura/UI/wire、完整world/boot/整局仍pending。135的headless集成变化与本32源审阅互不混算，未改任何生产或原证据。
