# 0.139.0 首次升级与新技能选卡：异作者独立复核

24 个 fresh fixture（21 种不同输入）通过独审：24 次完整4677与18次完整1093的声明投影一致，19例确实由phase1进入三卡phase2。1600与真实83304各24次是setup；独审没有执行作者production、checker、builder或原件。

独立参考直接读取当前WASM静态职业／种族／技能声明与稀有度表，重算默认属性、XP门槛、加级／回血cap、候选权重抽取、稀有度／upgrade kinds shuffle、选择后的80B新技能记录和phase2→1。57条候选元数据及顺序、6720B完整owned记录、1518项derived数值、319项声明keyed字段、RNG均一致；18次选择覆盖new card tier0..4。

66份raw keyed-tree用node+4的value偏移独立解码，全部与原件capture相符；只有22／28／1109／34／716／717字段子集独立建模，其余键不据此宣称恢复。live32有432个已知字节一致，144个None保留，其中16个原件非零值没有反填。constructor只核每例502B已知投影，50160B其余构造字节仍未建模。

21个实验源／12个production源／40条导入边保持冻结。全部非export WASM section逐字相同，20个作者静态函数加6个补充函数均绑定当前139原件body与索引WAT，含33028 RNG、29912借用查询、30628／25511 kind过滤、1677及1038。构造输出中的空来源header另从原raw Game核对；这是输出观察，不替代完整initializer归属证明。

本域使用明确的空P376、borrowed flat V128与phase1组件输入，真实执行83304／2181／1093；没有清除非空世界对象规避暂停／恢复。非空NPC／aux／claims场景、接受upgrade／gold卡、跨多级、u32 wrap、完整UI／消息包／Aura拓扑、自然App／Rc／主循环／Windows原生／完整一局仍未验收。

两次3例pilot与旧24例格式重跑批完整保留，不加算正式覆盖；作者研究实际累计54 gain／40 select。本次独审进程PID46732正常结束，双missing，9.72秒。精确SHA与收据见[JSON](2026-11-02-growth0139-independent-review.json)。
