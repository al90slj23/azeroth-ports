# 固定0.135.1：真实世界生产与1089开局观察

**在一个明确的空selected-profile输入下，原件真实完成了 `2902 → 6959 → 6730 → 1089`。** 原6730自己读取VFS、WDT/ADT和模型、生成world Rc并调用1560；随后同一G、同一world上的完整1089正常返回，phase从0变1，实际产生4个NPC和2个kind2拾取物。这是原件受控观察，**新增独立模型差分用例为0**，尚未恢复独立真实世界或完整游戏。

[最终收据](../evidence/entry-world0135-probe-20261101T092959.623703Z/entry-world135-probe-receipt.json) SHA `530f079d322365691ce897120ac0014be0da416eb048861b4d42ab988160556c`；[机器报告](2026-11-01-entry-world0135-probe.json)和[只读观察提取](../evidence/entry-world0135-probe-20261101T092959.623703Z/observations.json)保存范围、SHA与未知项。观察提取SHA `931d4d9990408f5a74cc8b55f1d2ea6c9767f5d2bb0b09687eb3f38384304061`。

## 真实生产链与显式输入

world完整producer内联于6730，而不是一个可直接导出的独立world构造函数。本批只为完整原2902/6959/6730/1089增加4个browser专用出口；原导出保留，全部非export section逐字节相同，所有函数体和内部callee不改。官方JS glue SHA `636bcd5a…9945`前缀保持，只追加get-imports和bind-only。只执行原externref初始化import851，不调用finalize、176107或app start4253。

全新回环origin初始localStorage、sessionStorage和IndexedDB都为空。原2902实际经官方Storage绑定读取 `rogue.characters`，得到真实的缺失记录，再由原函数生成368B默认账号；原6959继续应用初始解锁，参数为声明的两个u64零。没有伪造Storage返回值，没有写入用户存档；setItem649在拒绝列表，全部结束时该origin仍无存储键。

selected-profile的372个live字节属于明确研究输入：class1、race1、elwynn、对象ID0、App LCG seed0及空装备/天赋等来源。App+3376与既有1560输入P376同live布局，6730真实克隆其向量并用自身LCG产生本次seed。此前[151组1560](2026-11-01-initial-state0135.json)支持该空输入的构造域，但不证明菜单/selected-profile producer已还原。未把未知App整块零填充：5168B外围App先填A5，只写声明输入，账号交给原2902生成。

App5116初始为真实的“无缓存”空Rc；没有注入world、terrain、栅格、Once或VFS缓存。原6730依次构造FileSystem、读取资源与解析几何，自己分配124B world Rc，写入App5116，再把同Rc交给1560。所需transport仍用原4253静态布局和vtable1495776；6730的+32槽实际element1727→原176109恒0，未替换回调。App4776保持原构造值0，真实6777继续读取账号，未用sentinel跳过它。

本批在6730生成phase0后直接调用完整1089，保留其内部1744、真实位置采样、四次5736、两次13516/1417和后续调用。未手写phase1或flat-world。完整App4253、用户菜单/移动2328与主880仍未执行。

## 实际文件读取与世界输出

资产全部来自4T已有MPQ，无新增下载。server按原件实际请求名查独立MPQ reader；没有服务端MDX→M2别名、空模型、合成文件或补默认。每个实际payload逐项对照先前独立/StormLib一致的index行、archive/block/hash-slot、表SHA和decoded/reference SHA。不同字节重复归属会明确500停止，不猜覆盖优先级。

| 实际唯一MPQ文件 | 数量 |
|---|---:|
| WDT | 1 |
| ADT | 9 |
| M2 | 31 |
| WMO及组文件 | 410 |
| DBC | 2 |
| 合计 | 453 |

唯一payload总83,632,785B。实际data GET共561次，全部200：其中2次为真实 `__index`，其余559次为MPQ文件读取，包含原件自然重复请求。6730触发558次XHR，1089触发3次XHR（自身索引和Spell/SpellIcon）；真实新世界不再停在SELF边界。名称索引仍是本机已有Android字节SHA `1ca98562…aad8`，不据此称新版全部资源等价。基础MPQ包内程序版本为0.102.3；本批只证明当前0.135.1原函数在这个实际read-set中正常返回。

原6730产生Rc指针26204808，strong/weak原字为2/1，124B完整保留。G2348确实指向该Rc，world+120的flat开关为0；1089前后指针相同。原件运行后的世界包含真实地形/模型和栅格状态，但这些结构的全部独立语义、所有权和生命周期仍未知，不能以正常返回代替其还原。

## 同状态真实开局的观察结果

| 时点 | phase | NPC active | pickup active | WASM内存 |
|---|---:|---:|---:|---:|
| 原2902返回 | G仍为声明poison输出区 | 未构造 | 未构造 | 14,614,528B |
| 原6959返回 | G仍未构造 | 未构造 | 未构造 | 20,578,304B |
| 原6730返回 | 0 | 0 | 0 | 117,440,512B |
| 原1089返回 | 1 | 4 | 2 | 166,395,904B |

4份NPC完整424B记录均指向definition284=5415572，位置由原件在实际世界中生成；2份完整56B拾取记录的kind8都是2，amount12按原顺序为2、1，visual36为9005。它们没有被清空或换成普通经验球。玩家最终XYZ原位为 `[-9396,-633,68.02375030517578]`；原RNG、计数器、未写槽字节和所有其他状态一起保留。

原件输出队列有78份完整packet：150一次、169七十七次；另有原始JSON通知 `{"type":"start"}`。这些是排队数据，没有调用网络发送。其完整metadata、capacity、payload、NPC/拾取backing与世界全部指针目标保存在4份完整WASM线性内存文件中，总319,029,248B，逐份文件SHA已重新读回。post-run观察脚本不修改原件，也不把输出反填为独立预期。

## 运行隔离与失败历史

允许24个经审阅的原始资源、Storage读取和console绑定，其余854个抛错；实际触及16个不同import、3,396次调用，均在允许列表。它与878全拒绝/32MiB的纯Node差分批分开：本批独立浏览器WASM上限4,096页/256MiB，4,097页负例实际拒绝；峰值166,395,904B。Node与浏览器JS heap各512MiB，浏览器90秒watchdog，外层120秒独立进程组；本次约41.79秒。

所有浏览器profile/tmp、资产、full-memory和证据位于4T。CSP、确切origin请求路由、禁外部DNS和关闭回环代理限制外联；实际无非回环请求、浏览器错误或下载。最终Node54944 exit0、Chromium54950 exit0；资产worker54946关闭时SIGTERM。三个PID均经独立kill0读回为missing，HTTP/context关闭。9份源码在原件前后SHA一致，源码快照和完整原件身份保留。

第一批[092647失败](../evidence/entry-world0135-probe-20261101T092647.702804Z/post-exit-diagnosis.json)保留原样：外层Python exit0，但Node52868实际-6；一次巨大full-memory POST被CDP转成JSON，导致Node512MiB heap OOM，不是原件256MiB WASM上限已经耗尽。该批256-file研究限额还在成功读取41,097,386B/256文件后返回156个预算500，不能说成游戏缺资产。确认旧Node/browser/worker全部missing和原件前后源码一致后，才改用1MiB分块capture，并据实测412请求/静态617候选将文件数限额提高到1024，总decoded256MiB及WASM256MiB不变。新批也明确在world返回后检查server，任何非200都会阻止1089；最终本批没有触发这一边界。

尚未验收：独立VFS/world/几何栅格生产与所有权、真实菜单/profile/初始App熵、各地图/模式/非空来源、kind2消费语义、全部packet/UI、完整880与独立一局、保存和联机。本批是恢复这些行为的新原件依据，不能计为完整重建完成。

[独立只读复核](2026-11-01-entry-world0135-probe-independent-review.md)已通过，最终 review SHA `0675b4c87874e00e622a899af3c06b164a180cadb70a83f3d95815ee70628f8f`；未重跑原件，原批范围与未知项不变。
