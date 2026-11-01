# Fixed135 G2424波次25例只读独审

**通过声明范围的独立只读复核。** 固定0.135.1 / `90898d5e3`；原比较收据SHA `b02fcbe303c2058fee848c00b47f3389832690138cb6b99ab6386f38adeab555`。[最终审阅收据](../evidence/event-wave0135-independent-review-20261101T192947.072998Z/review.json) SHA `ac576e5668537ade78db54a2f45abebd1543aa8988c362ab4583f584c586f850`，审阅器与[结构化结果](2026-11-02-event-wave0135-independent-review.json)分别保留身份。

审阅未执行生产模型、原件、builder或原checker。只读取97份冻结源码、输入/预期/raw输出、完整原WASM字节、限定WAT、历史snapshot和独立query-world数据，并使用独立struct-f32、RNG、trig、terrain/secondary/nav/path谓词及wire解包参考进行核对。

## 通过内容

- **97冻结源码SHA全同**，Python/JS本地import闭合，生产源码AST未发现原件/文件/网络执行入口。当前仅`headless135.py`因root后续接60秒主链而有已声明漂移；wave核心SHA仍为`9c7c9bec1757df7717a9cbcf5b1be3b452fd1e1663978f22480b6f683314d0b6`，其直接依赖当前身份一致。没有把冻结prefix源码与后继当前主链混用。
- 重核**87,237已知值、62,137显式未知byte**，其中55,567个原件未知byte实际非零；None仅限物理backing合法未写位置。old active/inactive输入、guardian动态U68 owner和新普通单位/charge写入范围分别核对，未将未知补零或扩大到标量。
- 独立验证索引multiply-high rejection接受`low<=((n<<clz(n))-1)`，本批额外拒绝draw共69次；cheap pool、pack weighted choice、四种几何以及NPC角度/jitter后的全部RNG与counter一致。wave消耗433次draw，**145个wave NPC位置**逐bit相符；14个stampede GUID及U16/U20/U24/U28/U348 charge字段准确绑定，静止和移动stampede均有实例。
- 四style分布为swarm10、stampede2、wall3、pack10。独立terrain三角插值、secondary提升、nav/path接受谓词对157次candidate/anchor probe核对通过；消息绑定包括**169个完整169包＋25个完整150公告**，全部194包/31,639B及顺序严格一致，G2412未变。169内GUID、属性、HP、等级、display、六速度及朝向均与实际424B实体绑定，150的完整UTF8名字/公告/终止符逐字核对。
- G2586的255来自1560显式scratch+2674写入和scratch+88→Game2592复制；947先保存新2586，结束wave后写next2424，再进入Boss2456分支。两者是对应完整原函数/数据范围的静态证据，不是从输出猜初值。
- 默认第25例保持独立600帧prefix及原600/5选择身份，ordinary draw0、wave style0、8请求8成功、19 wave draw、unit16/cap16→24/cap32。4个guardian的GUID、实际timer指针/非别名、完整3word timer、132B ability和28B header均验证；静态内容按WASM初始零与全部active data segment叠加规则读取，不依赖错误的单segment连续假设。
- Game2592除明确947写域外累计62,875B不变；snapshot locale header/Once3/English0前后逐字相同，无Once注入。原件模块只有export section变化，947全部callee/code/data原样，未调用start。

原件owned65024收据退出0、PID/PGID missing，7.074秒/60秒，25 fresh完整947、878deny/实际0host、峰值166,395,904B/256MiB、全部stack恢复1048576。审阅自身owned22599退出0、PID/PGID missing，1.928秒/120秒；所有审阅源执行前后相同，原件/model/checker新增执行均为0。

## 边界

**本25组的157次world probe全部首个候选合法。** 它验证了实际生成点通过过滤；没有新增height/nav/path拒绝、缩半径fallback或pack anchor fallback动态验收。相关谓词已静态和独立参考核对，但不能以本批宣称拒绝路径全部运行通过。全部案例仍是zone0、last2586=255、mode0；旧事件排除、其他地图、无eligible/cheap回退、cap饱和和party路径没有新增动态覆盖。

ordinary前缀的draw/request记录、独立600帧上下文及distance-map是明确依赖，本审阅不重新执行这些生产器，也不增加600/601帧或独立world constructor验收。原件仍恢复历史完整snapshot以使用初始化locale/allocator；world仍是451独立资产查询数据手工packed Rc124。第25例把后续G2448从60显式设为1000隔离，因此它不是完整601或自然越过所有60秒分支；后继主链另验，不倒填本组件。

原比较收据没有单列raw结果文件SHA，本独审已将当前raw结果、输入、预期、runtime、终态、prepared、manifest及静态trace逐项绑定哈希，并在审阅前后重核，没有改写旧收据。首审阅尝试因审阅器known tally漏加25个已核case-id而退出1，无通过收据；修复统计后重跑全部只读校验，原件结果未改，计数不相加。

完整880、Windows原生运行及独立完整游戏均不由本审阅证明。
