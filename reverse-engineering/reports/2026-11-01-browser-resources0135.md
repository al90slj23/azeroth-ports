# 固定 0.135.1：真实浏览器资源链与正常命中返回

**已实际走通原件 4546 的真实 Spell/SpellIcon 懒加载，三组 Boss 矩形命中完整返回，15 个已恢复字段投影零差异。** 其中一组先独立调用 4546；另外两组不预热，由真实 phase1 的 `915 → 1073 → 4546` 首次加载。新实验执行了资源后的真实原件尾部，但没有把那些尾部行为全部恢复成独立模型。旧 [geometry390](2026-11-01-effect-geometry0135.md) 的 277 正常 / 113 host 拒绝前缀分类和 pending API 保持冻结。

最终收据：`evidence/full0135-oracle-20261101T083300.201197Z/browser-resource135-comparison.json`，SHA256 `e9affcc1707f381334c8f007eec207ae52014ebbe926539a623909056c6563f7`。[机器报告](2026-11-01-browser-resources0135.json)保存字段范围、请求、进程终态与未恢复项。

## 绑定方式和真实资源

新 [harness](../scripts/check_browser_resources135.py) 与原全拒绝宿主分开。WASM 只追加出口：既有 2785/910/915 与一个独立的 4546 研究出口；4546 的 `(i32)->i32` 和 body SHA `073d44f4…2e00f` 单独核对，所有非 export section 逐字节相同，原 878 个 import 完整保留，没有改任何原函数体。

官方 `official-wenilla.js` SHA `636bcd5a…9945` 整个前缀逐字节保持，只追加 GetImports / BindOnly 两个导出。手动实例化并绑定 exports，单独调用原 externref 初始化 import 851。没有调用官方 initSync/default/finalize；它们会经 176107 调到真正的 start 4253，不能用于本次“未启动应用”的研究。

“未调用 app start”的依据是原件没有隐式 section8、明确的 JS 入口白名单与 42 条调用记录、bind-only 不走 finalize；运行时写死的 false 字段本身不构成内部动态调用图证明。全局资源的 Once 状态由原函数自己从 0 写成 3，没有写入缓存指针或假造 SELF/XHR。

Playwright 使用本机已存在的 Chromium，全新 headless context/profile，不接用户 tab、profile 或存储。浏览器原生 Window/SELF/XMLHttpRequest 按官方 `__wenilla_data_base/layout/stamp` 配置请求本地 HTTP：

| 真实文件 | 字节 | SHA256 前缀 |
|---|---:|---|
| `__index` | 1,699,694 | `1ca98562…` |
| `dbfilesclient/spell.dbc` | 16,305,013 | `913d01c0…` |
| `dbfilesclient/spellicon.dbc` | 46,442 | `938e8c33…` |

三个 fresh WASM instance 都实际请求这三个文件，全部 200，响应字节 SHA 与已验本机 MPQ/Android 库存相同。原 4546 解析得到 `5568 Trample`、`28783 Impale`、`28308 Hateful Strike`，与原件前从真实 DBC 第 120 列生成的独立姓名预期相同。两个冷加载实例的 SELF/XHR 日志明确标注 active entry 为 `research135_effect_tick`，该次原函数调用的 Once 从 0 变 3，随后正常返回。

官方 glue 还静态 import 一个 FPS journal snippet。只提供本机已有的同路径真实文件、固定 SHA `a6d8b6cb…3f85b`；没有断言它与最新 135 的全部依赖等价。其 begin/append 宿主入口不在允许列表，没有被调用。

## 验收和隔离范围

独立预期和 33 项源码闭包在原件前冻结，包含包入口、传递数据和三个新脚本。三组各执行真实 Boss2785、动作910、三个915，共 15 个游戏入口；另有 9 次资源查询和 18 次原分配器调用。所有游戏入口实际完整返回；已恢复的单位/计时器、120B、HP/护盾/累计、计数器、RNG 和已知消息前缀零差异。资源后可能新增的消息或 JSON 后缀保留观察，不把后缀整体宣称为独立模型已经还原。

每个阶段另存 raw G2592、完整 128×424 单位 backing、64×120 效果 backing、完整计时器 bytes、消息/通知 metadata backing，以及全部 active packet 和 JSON payload。观察数据分别为 G 38,880B、单位 backing 814,080B、效果 backing 115,200B、timer 260B；它们没有被反填成预期，也没有新增零值预测或 mask。

此宿主**允许 17 个经静态核对的原始资源绑定，其余 861 个仍抛错**；实际触及 14 个不同 import、111 次调用。它不是原来“878 全拒绝”的纯 Node 环境。独立浏览器 V8 上限为 2,048 pages / 128MiB，实际最大 WASM 内存 92,143,616B；创建 2,049 pages 的负例确实拒绝。主 Node 的总上限仍为 32MiB/512 pages，单次 allocate 的 4MiB 上限不代表总上限放宽。

页面仅允许确切回环 origin；CSP、请求路由、指向关闭回环端口的全局代理与 DNS 限制共同封锁非回环访问。所有记录请求都是本机 127.0.0.1。没有下载、用户存档、已有安装包操作、完整游戏 start。最终 Node/server PID **79922** 退出 0，Chromium PID **79938** 退出 0，context 和 HTTP server 均在 finally 关闭；外层期限 120 秒，浏览器 watchdog 60 秒，本次运行约 3 秒。

## 资源后真正发生的额外状态：尚未独立恢复

完整 1073 保留于 `evidence/effect-geometry0135-static-20261101T081015.075418Z/1073.wat`，body SHA `ae8055c9…f9e076`、WAT SHA `7dafc834…24ab62`。从 4546 返回后的实际顺序包括：

1. 相对行 3133 获取 Spell 姓名/图标，随后构造元数据；3269..3445 对 48B history ring 做过期/数量限制、扩容并追加时间、伤害、护盾、HP、分类等字段。
2. 3446..3805 包含 raw buff13、item22 的条件性反击 914；3806..3875 的调用者控制流包含两个 984 事件生产入口。当前空来源/critical0 的成功不能扩称任意 buff/item/proc 来源都支持。
3. 3877 重读 HP、检查 minimum-one；3899..4990 包含致死、复活、种族 922、modifier/live 和多种包/事件分支。当前 HP 为受控的 1,000,000，未进入致死域，完整玩家构造/复活条件没有因此恢复。
4. 4998..5414 还含条件性 914 fanout；5435..5710 对当前 HP/最大 HP 做 ceil/clamp，并通过 3735 输出 key22/key28。

新 fullG 观察揭示下列真实变化，不能当作装饰字段忽略：

| G 域 | 已有指令依据 | 观察 | 独立规格状态 |
|---|---|---|---|
| 968/972/976/980 | 48B history cap/ptr/head/len | 空→cap4、len1、真实分配 | 未恢复全部记录所有权、剪裁和字节生产 |
| 1112/1120 | 4546 之前的容器处理 | 空→真实 pointer / count1 | 容器语义与生命周期未恢复 |
| 1196/1200/1204 | 1374..1586 去重扫描后 append4B，由来源声明 +32 派生 | 空→cap4、ptr、len1 | 仅结构与指令事实，完整用途未知 |
| 2476/2480/2484 | 最后 key22/28 的容器入口 | 空→真实分配、count2 | 完整 keyed 容器和原字节规格未恢复 |

[`browser-resource135-observations.json`](../evidence/full0135-oracle-20261101T083300.201197Z/browser-resource135-observations.json)记录三个用例到期前后的完整 G word delta。该差分包含受控 now 输入、已验标量/队列变化与上述未知项；源容器也可能在 4546 前已经变动，不能仅因最终快照出现便归因于资源后的代码。rawG 中的指针不等于其所有指向 payload 都已有独立规格。

因此，本批证明“合法真实资源 embedding 可完成这三种非致死命中”，同时暴露下一批应恢复的 history/容器/事件尾部。没有修改原 `effect_geometry135.py` 的 pending API，没有把原件执行成功等同于完整新独立模型验收，也没有接入完整 880、1089 世界进场、渲染、联机或完整游戏流程。

历史失败保存：082459 是沙箱 localhost EPERM（未启浏览器）；082614 是过严 DNS 规则也封住回环；082707 是真实 glue 依赖 snippet 缺失而 404。均以原 handle 确认终态后才修正并重跑。

[独立只读复核](2026-11-01-browser-resources0135-independent-review.md)已通过，最终 review SHA `810135b220315dd30a04ba54d72cba71198306025da58d47f8ee6a29e049fcc8`；未重跑原件，既有验收范围与未知项保持。
