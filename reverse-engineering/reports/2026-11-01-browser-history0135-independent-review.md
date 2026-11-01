# 固定0.135.1：真实资源受伤日志独立复核

[原件收据](../evidence/full0135-oracle-20261101T093136.935919Z/browser-history135-comparison.json)的9个fresh实例、37次完整1073入口及声明投影0差异已通过[独立只读复核](../evidence/browser-history0135-independent-review-20261101T093816.554900Z/review.json)，最终review SHA `493a8735aa88bd1ccb79753caab064629c023e14e4785f373cbabcb9ed4cfe8b`。复核未启动浏览器、重跑原件或修改作者源码。

独立WDBC读取器从真实Spell第0/117/120列与SpellIcon第0/1列恢复三个ID的姓名及完整icon路径：5568 Trample／`Interface\Icons\Spell_Nature_NaturesWrath`、28783 Impale／`Interface\Icons\Ability_BackStab`、28308 Hateful Strike／`Interface\Icons\Temp`。逐字段、原始DBC记录与资产SHA均一致；expected和这份独立metadata没有送入浏览器输入/config。资源数据本身由原件4546真实解析。

每个实例第一笔真实1073都令原Once从0变3，其后保持3；真实SELF/XHR在该入口中完成27次本地GET。明确的原件调用日志只含31次malloc和37次1073。原WASM只增加1073研究出口、其余section逐字节保持；官方glue整个前缀保持，只追加取imports及bind-only桥，没有调用finalizer或start入口。该排除依据是显式调用面、无隐式start节和日志，不冒称穷尽内部所有间接调用。

独立重算37阶段的护盾、HP和48B环形记录，覆盖真实资源姓名、增长搬移、10秒边界及最低1HP前的真实日志值。14,208B实际history backing分为8,870B严格字节、1,408B真实name/icon指针语义观察和3,930B新分配未写字节；其中3,175个未知字节实际非零。112B旧槽padding严格保留，201条active记录的字符串与UTF8长度严格一致，source指针1仍逐字节比较。95,904B rawG及变化清单核对；3次首次增长前缺失的旧堆指针另列观察。

宿主仍独立声明17项真实资源绑定允许、861项拒绝；实际333次调用涉及14个名字。128MiB浏览器上限的2049页负例已核对，峰值86,310,912B。Node/server与Chromium均退出0，复核时两个PID均已不存在；使用全新本地origin/profile，记录请求全为回环地址，无用户tab、存档或外部网络。它与878全拒绝／32MiB的Node批分开验收。

初次复核遇到内存中的Python tuple与JSON数组的表示差异，已保留[复核开发失败](../evidence/browser-history0135-review-failed-20261101T093815.845825Z/failure.json)，采用严格JSON序列化重放纠正，没有放宽数据内容。本批仍只验收无source单位、空proc、非致死／minimum-one域的history和标量；完整registry/keyed/proc、真实进场、主切片整合与完整一局未完成。详情见[JSON](2026-11-01-browser-history0135-independent-review.json)；复现：`python3 reverse-engineering/scripts/review_browser_history135.py`。
