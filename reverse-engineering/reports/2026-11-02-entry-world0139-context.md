# fixed139 匹配world与开局原件上下文

**0.139.0 / `f79c5e2b4` 的原件2917→2945→6786→1108已完整返回，保存了本版phase0与phase1全量内存。** 这是受控组件输入上的真实上下文观察，独立开局模型用例数为0；没有宣称自然App、菜单/profile全链、独立world producer、完整游戏或native Windows验收。异作者只读复核待完成。

## 身份与真实调用

原WASM SHA `71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299`。本次仅在export section7追加2917、2945、6786、1108和global0，其余原段逐字不变。官方JS SHA `d08ade052f40bcca1da93b559e9e10397ec240ba4975a467d6089ff5407bf3bd`为未修改的前缀，末尾仅追加研究绑定接口，不替换宿主函数。

[静态证明](../evidence/opening139-context-static-20261102T022955.014560Z/proof.json) SHA `689fce19563120ee4a1e7b8c0779591460794f4569dc2b0dee830e63146297f8`，从唯一139只读索引有限seek20个函数、1,424,751B WAT，没有第二次全profile。实际Storage `getItem` import640→66941→48446、静态字符串`rogue.characters`指针1758543及其caller2917锚定账号入口；App884真实callsite与empty flag分支锚定2945随从选择，而非按旧索引偏移认函数。

完整原件6786产生world/cache并内部调用1600，再执行1108。1108开头写phase2587=1，随后包括companions1795、普通NPC5719四次、13563→1446两次kind2、事件窗、40B特殊声明和边界对象。NPC5719明确stride432，新416/420置0、classification在424、425/426置0；427..431未写，不能由观察值补成独立已知。

4562应称Spell.DBC/spellID resolver，不能称locale producer。locale查询经20060→83304，83304解析14项内嵌JSON。当前两份原件上下文的Once14476488均为3，map count14/pointer21017688；这些仅是观察。其独立初始化/语言选择验证由另一批负责，不用本收据把观察到的pointer回填模型。

## 明示组件输入与真实producer边界

使用新建、独立的loopback浏览器origin、空localStorage/sessionStorage/IndexedDB，不接触用户浏览器或存档。App5168与输出G8192初始为A5。App中被6786读取的选中profile、seed、缓存空态、transport和模式字段是明确的研究输入，没有运行自然App4339或菜单生产链。

selectedProfile376的空rank/装备/成长及class1/race1/elwynn/GUID0为声明的组件域。它不冒称自然账号自动选定的角色。真正原件2917从空Storage产生account368；真正2945读取其flags并产生两个tag255缺省随从。2945输出16B先以A5污染，再复制至profile224..239；未活动payload不强制清零。随从缺省结果有真实producer，profile其余字段仍是组件输入。

研究transport使用本版4339真实store所引用的vtable1410440，9word为`284,24,8,285,286,287,288,289,290`；element slot290实际指向177894，完整函数为`i32.const 0`。这满足6786该调用的研究输入，并不意味着完整transport、App或网络层已经重建。

没有写入world/cache/locale Once内存来强行通过。world/cache由原件6786生成，原件Game与App均引用同一Rc。没有加载任何135/138 snapshot或旧版资源字节。JS/externref表和生命周期也没有被宣称可从线性内存完整恢复。

## 新官方资源及失败保留

最终[资源获取收据](../originals/entry-assets139-20261102T022818.157124Z/receipt.json) SHA `7aec47c1ce5b6d58f2374878e2f6877e95de4784aed7837a21a2075ecf97ea92`；`resource-map.json` SHA `3a794c2e35873852cc8f6661fb93ec9edae9a06626277ff123f1612495927ec2`。453个候选资源加本版`__index`合计454项、85,332,479B，均从官方HTTPS新下载，逐项记录原URL、HTTP状态、SHA、文件路径和curl进程终态。资源路径来自旧请求集合作为候选，不复用旧文件内容；本次139原件实际读取集合另有561次loopback资源请求，全部200，包含重复请求。

下载前后官方manifest逐字一致，版本0.139.0、HTML stamp `f339dd20e0fe`一致。新下载的官方snippet也冻结SHA。浏览器执行时只允许自己的精确loopback origin；没有借官方外网填补遗漏资源。

前两次获取均保留failed收据和当时源码快照：第一批308请求、66,319,760B；第二批147请求、20,481,621B。实际阻断是路径检查过严，拒绝10个文件名含合法空格的请求；第一批在等待其他已排队工作时也达到180s总预算。修正为逐段安全URL编码与禁止空/点/父目录及控制字符后，仅补剩余10个文件并重核metadata，最终16请求、2,049,777B。三批fresh139来源链显式保留，不把失败目录覆盖为通过。

## 原件结果与可消费输入

正式[原件收据](../evidence/entry-world139-probe-20261102T023815.931445Z/receipt.json) SHA `5d940f9d00f0428327791132f5b9f60df7787348d6fd5a1d50ad840aea1a2964`。App=14680072、G=14685248、worldRc=20544640：

| 阶段 | 原始内存文件 | 字节 | SHA256 |
|---|---|---:|---|
| 原件6786后 | `after_real_world6786.memory` | 111,804,416 | `f2cc1e0e1b336e9e923e4cda4401853a380a2c3ad769a3b73805e153a2114b8c` |
| 原件1108后 | `after_real_begin1108.memory` | 177,078,272 | `464c2f08f265196b08685633416c42c0e0e480830d8a35787d3f7f82c870cf32` |

[只读解析观察](../evidence/entry-world139-inspection-20261102T024328.416207Z/observations.json) SHA `92367b368fc46666ae75e7e4ffd156209704b4967c1e9732d1688a027b6600db`保留完整Game/App/worldRc、六种向量backing、全部队列metadata和payload。全部为原件观察，不是期待或独立已知值。

phase0六种向量均空、消息与通知空。phase1为4个Kobold Vermin、0随从、2个pickup、4个special、2个window、69个boundary，counter85，76个完整packet和1个start通知。NPC名字这里是definition中的fallback UTF8，不冒称全locale显示已经还原。

882个准确原件import中，仅24个已明确资源/Storage语义的真实JS函数允许，其余拒绝。实际调用3396次、16种import id（498/522/640/642/643/644/657/658/659/804/831/839/849/852/855/881），无deny命中。这里有真实资源宿主调用，不能把它写成all882-denied Node差分。存储始终为空，没有账号写入。

包括6个allocator在内的10次入口前后stack均1048576。独立256MiB内存预算、90s浏览器和120s外层期限，Node85054/browser85059均exit0；Node PID/PGID均消失，浏览器终态日志exit0。实际37.3709秒。两份完整内存以1MiB分块保存，未以巨型CDP消息传输。

prepare-only目录`entry-world139-probe-20261102T023739.447091Z`独立保留，目标执行为0。更早的一次preflight停在已移除的Chromium1243路径，未创建目标实验目录或执行原件；实际使用本机现有Chromium1248，没有安装或下载浏览器。

## 后续验收

这些是匹配139的受控输入，可供下一批完整5719或1108组件实验。消费者需逐一证明自己的WASM身份、原件callee、snapshot输入、宿主边界和已知字段，不能把本次phase1观察直接写成独立模型结果。真实自然开局position/world查询、完整432NPC独立写集/169消息、完整1108独立组合及完整游戏流程仍待完成。没有更改安装包、原件固定输入、公共登记或存档。
