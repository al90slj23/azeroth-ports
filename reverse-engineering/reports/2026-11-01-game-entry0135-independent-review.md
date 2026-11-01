# 原UI进入运行Game：独立只读复核

**限定原件观察独审通过，版本0.135.1 / Web0898d5e3。** 最终批次是[135403收据](../evidence/game-entry0135-probe-20261101T135403.797895Z/receipt.json)，SHA256 `1a388679c0418f2fa2746c91ca8d3f7e91428563d05c1935f73ca09425e5b49e`。[独审证据](../evidence/game-entry0135-independent-review-20261101T140010.137361Z/review.json) SHA256 `279066728b8254cc3fffe630483a5162df45abfe7fb73f108dc303552703c1c5`。这证明真实原UI、自然Game安装、真实移动和有限运行观察；不证明独立重建已完成。

[复核脚本](../scripts/review_game_entry135.py) SHA256 `60929f20c5859b4db700ce80ec10d8984fcb4ec0684809c0149b5a623e91c486`。复核只读取终态文件、索引和源码，不重新启动WASM、Windows EXE、浏览器或游戏。新增原件执行0、独立模型案例0、独立主循环帧0。

## 重新核实的结果

| 项目 | 独立重读结果 |
| --- | --- |
| 原主循环 | 603次原回调完整返回；其中frame595..602为8次running返回 |
| running门槛 | 从实际mode及phase2587/globalPhase2588重新计算，未依赖作者布尔标签 |
| 时钟 | 7次正向推进，最终f32值0.26590001583099365；逐帧App墙钟与真实now/1000相符 |
| 回调边界 | borrow前后均为0、原closure返回、stack前后相同；观察器及原回调异常为空 |
| 一致快照 | 1,378,877,440B，SHA256 `c461b2f5efb1399127d22c04fbe5efed15f8b8411ceeefe22a05b4dce45bfd15` |
| 提前保存的小证据 | 3,375,507B，SHA256 `751c4d251eeea95b6211069f295ac251ff9bb83cc78147255fcdb739f34071cb`；明确不声称bulk完成 |
| HTTP | 4,524次：4,522个200、2个单列的favicon404；素材请求无失败 |
| bulk上传 | 1,315个1MiB或末尾余量POST；顺序、长度、总量和完整文件hash均核实 |
| 素材 | 2,418个唯一payload文件、164,823,373B逐个重新计算SHA256 |
| 实际Game | selected-profile tag0；7条424B单位记录、2条56B拾取记录 |
| 实际world | 9个tile、280×280 nav、560×560 secondary；均直接来自同份冻结bytes |
| 进程终态 | Node、worker、Chrome的PID和已归属PGID再次只读检查均不存在 |

## 原件身份与宿主边界

独立解析原WASM和研究module的section及export，确认仅section7追加global0的只读观察入口：36个原export保持原序，函数body、imports、table、globals、memory及data等所有非export section逐字SHA一致。原mutable global仍可变；研究代码只读取其value。原件没有新增隐式start，没有新增可调用函数role，没有将共享52角色扩展成新的执行宿主。

12份本地项目源码同时绑定当前文件、冻结source-snapshot、config和原件收据before/after字节身份；本地Python import闭包另行AST遍历。原WASM、module、Node、Chrome、Python、官方JS前缀、字体、辅助JS、名称索引和资产SQLite的实际hash重新核实。官方版本收据、module manifest、原模板config及validator身份分别绑定。Playwright检查的是包元数据，不能扩称整套node_modules、Python标准库或OS实现均冻结。

经SQLite只读定点seek重新读取12个原函数窗口，包括4253、104471、83825、880、6730、24129、2328、1089及45626；保存了查询范围、实际WAT片段、WAT片段SHA和原binary body SHA。没有全文读取1.3GB WAT，没有把静态窗口当成新增差分案例。

新宿主完全没有安装Playwright route。实际Chrome临时profile在该批4T目录的tmp下，启动时检查隔离origin的Storage为空。原件随后在这个新隔离站点写入8个localStorage键是实际行为，不能误解为读取了用户旧存档。禁止SW、下载与外部转发的策略及独立拒绝代理、DNS、CSP均在冻结源码和实际启动参数中保留。

## UI、移动和命令来源

实际输入是点击`(475,490)`，等待原场景素材安静至少3秒且安装后至少10秒，再点击canvas及真实W键按住1,500ms。捕获的DOM事件均为`isTrusted=true`，没有研究代码写入App、Game、world、profile、原mutable global或命令队列，没有注入Enter。

本轮自然Game安装出现在frame16。pre-poll的真实Vec232仅捕获frame1的raw30/31/33及frame6的raw11；原232B字节、tag、长度、队列地址及所属callback均核对。**没有捕获raw23，因此不能宣称Start按钮已被证明是raw23→Vec232→1371。** 真实UI到自然安装与运行已观察成立；按钮的具体producer、peer消息与反序列化投递仍是需要继续恢复的细粒度链条。嵌套指针payload保持opaque；最终队列为空不抹去历史消息。

独立查看了[移动前截图](../evidence/game-entry0135-probe-20261101T135403.797895Z/scene-before-movement.png)：原艾尔文场景和角色已出现，中央明确显示“移动以开始。”；[最终截图](../evidence/game-entry0135-probe-20261101T135403.797895Z/original-game.png)显示原树林、角色、地图与技能HUD，开始提示消失。这是原件画面，不能称为独立重建UI或渲染性能验收。

## 冻结后的生命周期与联网证据

完整线性内存先同步复制，之后才对原import507观察到过的919个RAF handle调用cancelAnimationFrame，copy到cancel之间无await。919不代表当时仍待执行的callback数量；来源和静态时序已核实，但没有持久化逐ID清单，因此本复核不声称逐handle独立验证或Rc析构等价。停止renderer安排是采集结束后的宿主生命周期操作，不计作新增游戏行为恢复。

小证据先于bulk上传持久化；其中frames、commands、checkpoints、contexts、stack及运行计数与最终result逐项一致。小证据中的`bulk_memory_capture_complete=false`是提交时事实，完整性只由最终bulk文件、总字节和SHA另行证明。线性内存一致副本不包含JS对象、externref、GPU/browser状态，不能当成可恢复整个VM的存档。

没有pageerror或匹配renderer panic/device-loss的console错误。保留了2次被CSP阻断的官方`/presence`意图，以及16次独立代理拒绝的浏览器进程请求；后者明确为未归属请求，均未转发。没有被动观察到游戏页面的实际非loopback请求。不能把这些阻断改写为“没有联网意图”，也不能据此宣称联机可用。

本轮WASM2GiB、解码素材512MiB、JS heap768MiB、额外冻结副本及240/270秒内外期限均为独立分项预算，不能合并称为进程总RSS上限。先前失败、资源预算边界与partial-upload批次保留原收据和事后诊断；不与本轮计数累加。复核脚本调试只修正审计侧假设，未重跑原件或改变12份冻结生产/宿主源码。

完整独立880、全部App所有权、按钮到peer/ECS事件的完整生产链、完整一局、性能、存档与联机仍未完成；目标继续保持未完成。
