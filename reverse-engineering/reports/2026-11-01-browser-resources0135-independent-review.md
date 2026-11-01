# 0.135.1 真实浏览器资源桥接独立复核

独立只读审查通过。[审查证据](../evidence/browser-resources0135-independent-review-20261101T084320.657099Z/review.json) SHA `810135b220315dd30a04ba54d72cba71198306025da58d47f8ee6a29e049fcc8`；[机器报告](2026-11-01-browser-resources0135-independent-review.json)关联源码、真实请求、Once、进程终态与已知投影范围。本次没有启动浏览器、执行原件、联网或改作者源码。

最终原件批 083300 收据 SHA `e9affcc1707f381334c8f007eec207ae52014ebbe926539a623909056c6563f7`，33 份源码快照前后及当前一致，含包入口和全部纯预期依赖。从冻结几何模型重新生成 pilot 并筛选原案例 0/3/6，严格等于浏览器固定输入；三组共 15 个状态快照的全部已恢复字段独立重比较通过。它们是 **15 个阶段投影**，不是完整原件状态或全部资源后逻辑的独立重建。

WASM 与固定原件的非 export section 逐字节相同，无 section8。原出口保留，只有 2785、910、915 及 4546 四个批准研究出口；4546 `(i32)->i32`、body SHA `073d44f4…2e00f` 核对一致。官方 glue 整个前缀 SHA `636bcd5a…9945` 保持原字节，仅追加 GetImports/BindOnly。后者赋 exports 并复位原 typed-view 缓存，不调用 initSync/default/finalizer；资源 import 的官方函数体未改写。

“未进入 app start”的可核查依据是：无隐式 start section；全部 42 条显式入口日志仅有原分配器、三个游戏研究入口和独立 4546 查询；手动绑定没有走 finalize；原 176107 body 为 `851 → 4253`，4253 在完整直接调用索引中的唯一 caller 是 176107，且未调用这两个导出。851 的原 externref import 单独初始化。运行记录中写死的 false 字段本身不作为证明；本审查没有穷尽所有潜在内部 `call_indirect`，也没有通过改写 4253 安装运行 hook。

三份本机真实资源逐字节 SHA 复核：`__index` 1,699,694B、Spell.dbc 16,305,013B、SpellIcon.dbc 46,442B。每个 fresh instance 都经官方资源绑定和原生 XHR 请求三份文件，九次均为 200，响应长度/SHA 与文件一致；没有直接填入 Once/cache 或假造 SELF。原 4546 解析的 Trample5568、Impale28783、Hateful Strike28308 与事先从真实 WDBC 第 120 列提取的名字一致。24B record metadata 另作原始观察，不能因此宣称图标指针和完整 DBC schema 已重建。

case0 先独立查询 4546，命中前 Once 已为 3；case3/6 的命中前 Once 均为 0，实际 `research135_effect_tick` 调用内触发 SELF/XHR，调用后 Once 为 3 且原入口正常返回。由 entry sequence 关联的 host 日志可确认这两个是真正冷加载，不是把预热结果换标签。三个实例的全部游戏入口返回，原 pending 几何模型保持原样。

资源环境允许 17 个明确的原始绑定，其余 861 个配置为抛错；实际 111 次 import 调用触及 14 种，全部在批准集合。它与 Node 的 878 全拒绝 / 32MiB 数学环境分别记录。浏览器启动参数限制 2,048 pages / 128MiB，原件前的 2,049 页 Memory 负例实际拒绝；最大 WASM 内存 92,143,616B，未将 JS heap 或整个浏览器进程内存混算为 WASM 上限。

新 headless context 使用 4T 专属临时 profile，未用现有 tab/profile；localStorage 与 IndexedDB 读回为空。请求策略只允许确切回环 origin，服务器只收 loopback GET，同时有 CSP、DNS 和关闭端口代理限制；记录中没有外部请求。该结论是受控路由及记录范围，不冒充操作系统级全网抓包。Node/server79922 与 Chromium79938 记录退出 0、context/server 已关闭；额外只做 signal0 进程存在性查询，两个 PID 均已不存在，没有发送终止信号。

15 阶段保存并复核 raw G38,880B、128 槽单位 backing814,080B、120B 效果 backing115,200B、计时器260B、消息/通知 metadata246,624B 及全部 active payload。已知效果字节严格比较115,152B，48B scratch 保持原四字节 unknown；单位 +248 只归一化实际地址，原指针及完整计时器 payload 有交叉读回。metadata 的 active 长度/opcode/容量与实际 payload、原 G header 一致。原前缀包与通知在后续阶段完整保留。本三例没有超出已知 opcode/JSON 类型前缀的额外后缀，但完整 history/容器写入仍存在。

独立重算 rawG 的到期前后 word delta，与作者三个观察列表完全相同：[交叉核对](../evidence/browser-resources0135-independent-review-20261101T084320.657099Z/observations-check.json)。G968 history、1112/1120 来源容器、1196 系列和2476 keyed 容器/key22/28 的完整 payload、所有权和后续事件尚未独立恢复。不能因它们没改变已知投影，就当装饰字段省略；也不能仅凭最终快照将所有变化都归因于 4546 返回以后。

本批证明该资源桥接可以让三种受控非致死命中完整返回；不把原件真实执行成功等同于全行为已重造。旧 geometry390 的 277 正常 / 113 资源拒绝前缀、pending API 和所有旧收据未修改；真实世界 1089、完整 880、渲染、联机及完整游戏流程仍是后续任务。旧 snippet 为固定 SHA 的已有本机依赖，其 begin/append 入口未允许、未执行；并未将它或旧基础资产宣称为最新全部资源等价。
