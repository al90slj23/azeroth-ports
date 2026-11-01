# fixed135 opcode199校正确认组件

新增独立[`player_correction135.py`](../reconstruction/core_spec/player_correction135.py)。**88例完整原件968(opcode199)差分，0差异；[异作者只读复核通过](2026-11-02-player-correction0135-independent-review.md)。** 固定0.135.1 / `90898d5e3`、WASM SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`，没有改动已冻结的移动38例/33例源。

接口为`encode_player_correction_ack135(guid,sequence)`、`decode_player_correction_ack135(payload)`和`consume_player_correction_ack135(Game,payload)`。输入域明确限定为mask1B、按mask位序排列的packedGUID字节、紧随u32小端序号的精确长度5..13B；截断、额外尾部和原件容错默认值未接纳。Game可为完整bytes或`tuple[byte|None]`，结果保持表示形式。

默认本地路由的规则是：

```text
decode packedGUID and sequence
if u32(G416) == 1 and u32(sequence) >= u32(G432):
    store u32(G416) = 0
full17726(G)                  # 本批mode2582=0，原件自然返回
```

GUID被解码，但此本地分段不比较它是否为玩家GUID。G416不是1时，不消费G432；XYZ420/424/428、时间436及其余未知字节均透传，不补0、不修改。比较是无符号`>=`，不做序号环绕解释：pending=`0xffffffff`、ACK=0会保留；pending=0、ACK=`0xffffffff`会清除。该规则不意味着所有联机入口都缺乏GUID或权限检查。

有效新收据：[correction-comparison.json](../evidence/player-motion135-oracle-20261101T232552.862423Z/correction-comparison.json)，SHA `463deadc49cb34222e92854de1a17116fbf16a78d0952d3f49ad0e14456415ea`。17个真实完整来源、31条本地导入边，在期待生成前通过跨core/resource闭包强核；此17源包括entry_resources135/dbc，和早期漏冻的旧17源移动批是不同来源集合。

每例原件恢复真实after_begin快照，保持真实worldRc26204808。部分App组件只声明4253已证明的空Game/网络tag2，再让完整6730直接写App+16=14549016、完整1089进入phase1。先独立进行1次setup-only观察、冻结pre968物理状态为显式输入，再生成独立期待。目标阶段每例重放同一6730/1089并逐字核对prestate后才调用**完整968(route0,peer0,opcode199)**。88次target968、88×6730/1089 setup、以及最先1次setup-only分别计数；setup不算独立构造验收，更不算自然App4253/1371生产。

本批覆盖tag0/1/2，pending序号0/1/17/`0x7fffffff`/`0x80000000`/`0xffffffff`及其ACK低于、等于、高于、极值组合；另测空GUID、每个单字节mask、高位单bit与全部8字节GUID。结果为28次实际清除、60次保留，其中15次不同于玩家GUID的ACK仍触发清除。

比较全部2592B Game、5168B App；完整原有包前缀保持且没有新包，世界124B和2,318段查询来源不变。878宿主导入全部拒绝，实际调用0；256MiB上限，实际166,395,904B。自有Node PID/PGID23951退出0，8.4782秒后两者均消失，期限60秒，无遗留进程。

另有88次canonical cells**模型自检**，保留227,592个None字节，证明tag0/2时G432可保持未知，未知G416明确拒绝；4个非规范payload主动拒绝。不将这些自检累计为原件差分。

模块SHA `fd2b512963d3c32013e3105260daae171fd804ab83189eb8c8e7ab8774605b40`，checker SHA `b058b966280ed1f7793702a3c2cc259713601262f014ee4eb99b7a48c820213e`，独立runner SHA `1e2819ae963c5bb0becf7ea05cad3bdfd68f8311d38720e1bf1c45fd17892182`。期待及输入分开，原件不会收到期待、诊断或fixture标签。所有来源和冻结工件执行前后SHA一致。

仍未闭合：ownerRoute1的2080切换、mode1转发/广播、自然键盘摇杆生产ACK、自然App安装、截断ACK容错、phase0入口，以及真实pending状态穿过完整915和后续连续游戏帧。915不读/清416的静态依据见[只读报告](2026-11-02-player-correction0135-static.md)；下一步应保留真实payload实测连续链，不清tag来绕过guard。

## 独立复核

[88例只读独审](2026-11-02-player-correction0135-independent-review.md)已通过：独立重算1,365,760B前后Game／App及21,824B world record，0差异；确认28清除、60保留、15个不同GUID仍清除，以及8个必须按unsigned处理的边界。None与短路读取另作独立参考检查，不新增原件case。旧78包前缀与完整world ranges只由冻结runner断言不变，没有落盘的raw部分不称独立逐字节对照。
