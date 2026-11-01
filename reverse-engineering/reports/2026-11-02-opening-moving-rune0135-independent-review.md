# fixed135：移动→自然恢复符文→连续16帧的异作者独审

**限定通过。** 0.135.1 / `90898d5e3` 的一份新原件采集完整读至EOF：460受控14-tail帧、4次选择、44次完整968、6488阶段、6490原件入口，0差异。审查者未运行原件、生产模型、checker或builder。完整880、原生客户端、自然App输入生产者与完整一局仍未验。

## 证据身份与输入域

原件比较`evidence/opening-combat0135-oracle-20261101T232156.684647Z/comparison.json`，SHA256 `521db52b9d97637212460083a7ea88b9038d63871536d6635edc21645e0bd622`。117冻结源（production100）在运行前后、冻结副本及独审当前读取时相同。全部production静态导入闭合；脚本层另核72个可达module/function scope、合计555条本地导入边。

`check_opening_handoff135.main`中可选oracle导入check_opening135没有列入本批；该helper.main不在可达调用范围，本checker只调用load_independent_world及其纯读辅助。初版过宽的AST检查因此在阶段读取前拒绝，保留失败收据；最终没有把未执行分支补hash冒充历史冻结源，也没有忽略真实执行的导入。

App是明确的typed partial fixture：App14549000，Game直接为App+16=14549016；原始before App来自固定历史快照，完整核对tag16=2、network2608=2和明列class/race/seed/GUID/无同伴字段的写入。真实6730直接构造该inline Game，再执行1089。它不是自然4253/1371 App安装、fresh boot或externref VM恢复；模拟时钟是显式f32加到G2352。18函数+stack私有导出逐一核同；原模块全部非导出section及原函数体保持。

## 全流重比与传输

- CAS完整finish：6952记录、2,139,516,743逻辑字节，SHA `8e9e568814f20cb00a6f48f8a954b8745cd2b021a9373e368c300a8dca8f04f5`；21749个blob、123,474,051唯一字节、1,338,498次引用均核验。原始gzip索引是完整单member，未重排或重编码其字节。
- 期待gzip共396,624,522B完整读至EOF；所有clock/action/frame/stage/entry/selection顺序核对。32,127,425已知叶/字节重比一致，29,062,460未知cells保留，其中18,896,249原件值非零，没有将None补零。
- 每个raw Game、vector header/完整已分配记录backing、live/Aura/guardian所有者、packet与notification metadata/payload/backing及队列prefix按既有独审reader严格绑定。其它tail仅验声明投影和已知物理字节，未升级为完整Game行为验收。
- 复用已独审750/CAS/物理player方法、2328数值/terrain及306编码；新审独立实现968外层、持续motion owner、全部collect吸引/选择/移除与kind5消费观察，不称第二次独立恢复这些helper。

## 移动链

44条canonical24消息是181×1、238×42、183×1。首条在0-based frame401选择已由真实spawn产生的kind5符文，GUID `17370383913897164969`。逐条从实际前态独立核LE字段、u32毫秒→f32客户端时钟、G2496 flags/G440=1/G444、2328默认terrain接受、清G440；同样独立核测试路线以当前速度×dt逐步前进，未把路线当作恢复出的UI/摇杆物理。

全部44条motion的完整114,048 Game字节（44×2592）及227,392 App字节（44×5168）重算一致；world124、vectors、包和通知均未改变。这仅指44个motion转换的全字节比较。motion owner从构造器已证写集及其余None开始，位置/时钟/GUID/动作词临时绑定，6489份canonical owner快照一致；没有为纠正队列捏造容量。

## 自然符文消费

460次collect均独立重算entry半径、XP吸引（未满6秒且出半径则不吸引，aged使用32速度否则24，延迟下限0.12）、各类资格与逆序消费。kind0按到达时钟，kind1按半径/到达，kind3/4/5按平面距离≤3；移除后逐56B稳定memmove，完整187,040B已分配backing相等。共37次吸引、35个XP、16个coin、1个kind5被消费；全部170顺序逐GUID核同。

恢复符文在frame400/stage5615出现；frame443/stage6258，即人类计数第444帧，在距离2.560889时消费，reverse顺序仅`[index2, kind5, GUID17370383913897164969]`。它是原件连续状态中由spawn产生后走近消费的记录，没有额外注入符文。

- 消费前HP **266/266**，heal gate0，按50%最大HP计算请求 **133**，cap后仍为 **266**。这是满血上限见证，**没有实际HP增加的观测**。
- 170销毁后紧跟完整306（spell23493）及150（type6 `AZSBANNER`）；完整JSON为`banner/id1/kind rune/Restoration Rune!/boss false`，通知计数1→2，逐字节匹配。
- kind5不重建live/Aura，原件完整live32/Aura48保持；player物理审查器在collect路径保留这些所有者，并真实推进通知计数，没有临时删rune投影或把counter强制留1。
- frame444发送183停止。后续frame444..459共16帧仍在同一个Game连续执行全部tail，符文保持消失、通知计数2、HP266，位置稳定；没有另起状态接续。

## 运行与边界

原Node18056 exit0、33.4816s/180s、PID/PGID均消失，878 host imports全拒绝；166,395,904B/256MiB WASM、512MiB JS cap。未访问用户存档或网络。

最终独审收据`evidence/opening-motion-rune135-independent-review-owned-20261101T233504.827365Z/review/review.json`，SHA `a05110aaf4f483f3ea6f6648b970f9b64cda23b5cc05975cb5dd1513b0ae46df`。独审38193 exit0、33.1472s/240s、PID/PGID消失。13份审阅依赖源另存快照；两次早先reader尝试完整保留，均未新增原件执行。

此处自然近身资源仅kind5，未新增自然kind3/4、受伤回血增加、其它地图、mode1/remote/network/broadcast/199ACK或UI操作验收。live辅助词仍为原件观察加来源/copy绑定，没有恢复其内部读取值或把它反馈为生产模型输入。production、主报告与registry均未由审查者修改。
