# 固定0.135.1：真实Spell资源接入受伤历史独立模型

[真实资源读取实验](2026-11-01-browser-resources0135.md)之后，本批把真正的Spell姓名/图标与[独立48B历史模型](2026-11-01-incoming-history0135.md)组合：**9个fresh实例、37次完整原件1073调用、0声明字段差异**。[最终收据](../evidence/full0135-oracle-20261101T093136.935919Z/browser-history135-comparison.json) SHA `3ce007255c7063bd8955fe5d73a3f4e545ba818ecde999646859506403a1a638`；17份源码在原件前冻结，运行后读回一致。

没有调用4546的替代函数、写Once/cache或向原件提供预期姓名。每个实例的首个真实受伤调用都由1073自然触发4546，Once从0变3；后续命中复用真实缓存。三种资产 `__index / spell.dbc / spellicon.dbc` 每实例均实际GET一次，27次请求均为回环200且响应SHA匹配冻结原件库存。

## 独立资源列规格

4546通过41301读取Spell姓名列120。图标ID的真实指令是 `row*stride+488`；该指针包含WDBC的20B头，所以是 `(488-20)/4=117` 列，不能误作122。SpellIcon以列0的ID查询、从列1读字符串；原件1073直接保留实际全路径UTF8。

| Spell ID | 独立DBC姓名 | Icon ID | 独立SpellIcon全路径 |
|---|---|---|---|
| 5568 | Trample | 168 | `Interface\Icons\Spell_Nature_NaturesWrath` |
| 28783 | Impale | 243 | `Interface\Icons\Ability_BackStab` |
| 28308 | Hateful Strike | 1 | `Interface\Icons\Temp` |

[机器报告](2026-11-01-browser-history0135.json)保留独立行号、完整原始DBC记录、4546 body/WAT SHA与列依据。这些预期在原件前由独立WDBC读取器生成；浏览器config也不携带这些name/icon预期，页面只收到11,421B纯输入。309,517B独立expected另存，比较在原件正常退出后由Python完成。

## 实际组合与严格范围

37次调用覆盖两次真实资源命中、三种环形扩容/搬移、恰10秒与超边界裁剪、护盾耗尽、minimum-one前的负HP历史、16次连续混合Spell记录。每个active条目的source/name/icon三段UTF8都解引用严格比较；共201个active记录，14,208B完整history backing保留，其中8,166B可预测字节严格比较，包含112B旧槽未写padding。

新增指针由字符串语义比较并保留实际raw48；2,112次pointer字节观察中1,432非零。3,930次新分配未写字节观察中3,175非零，没有预测成零。旧padding不被整体豁免；新active槽只有真实未写46..47保持allocator unknown。37阶段的rawG2592合计95,904B，全部原packet/notification payload及metadata backing另存；它们的保存不能代替独立实现。

WASM沿用只加一个1073研究导出，所有非export section逐字节相同；官方glue完整前缀保持，只追加get-imports/bind-only，不调用init/finalize/start。JS白名单和68条调用日志只有malloc与1073，另直接调用原externref初始化import；这不是针对所有内部call_indirect的穷尽动态证明。

本批使用真实浏览器原生SELF/XHR，**17个资源绑定允许、861个导入拒绝**，实际333次导入调用、14种名称，和旧纯Node878全拒绝域分开。128MiB上限已用2049页创建负例验证；实际峰值86,310,912B。全新headless profile/TMPDIR位于4T研究区，精确回环origin、CSP、请求路由、关闭端口代理和DNS规则限制外部请求；未连接用户tab/profile、未下载或接触存档。Node/server PID56321与Chromium PID56323均exit0，context/server关闭且两个PID读回缺失。

本批只扩大到 sourceGUID0、无单位、category1/2、三个真实非零Spell ID的history/受伤标量组合。匹配来源、完整registry/keyed/proc/反击、致死复活、所有Spell和中文资源仍未独立恢复；没有接入真实1089/full880/headless或完整一局。旧fallback164组和geometry113组拒绝前缀的源码/收据不变，不反记为新域通过。

复现：`python3 reverse-engineering/scripts/check_browser_history135.py --phase full`。小pilot2实例/4入口先通过，全部进程确认终态后才启动full；两批源码字节相同。[独立只读复核](2026-11-01-browser-history0135-independent-review.md)已通过，最终 review SHA `493a8735aa88bd1ccb79753caab064629c023e14e4785f373cbabcb9ed4cfe8b`；未重跑原件。
