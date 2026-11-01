# 固定0.135.1：真实受伤48B历史队列

新增[独立组件](../reconstruction/core_spec/incoming_history135.py)从已恢复的受伤标量延伸到真实 `1073` 的历史记录：**164组、924次完整原件调用、0声明字段差异**。[最终收据](../evidence/full0135-oracle-20261101T092259.307993Z/incoming-history135-comparison.json) SHA `378bd6c29ccaeb887ab6e25ec39c982e9ee25842e47591b76ac544c81e3c8b63`；[机器报告](2026-11-01-incoming-history0135.json)列出12份冻结源码、所有来源与未知项。原件入口和内部callee均保留，仅沿用研究导出；完整函数执行成功不等于完整1073已独立实现。

## 已恢复规则

环形队列头为 `G968=cap、G972=ptr、G976=head、G980=len`，记录48B。每次真实受伤先逐头移除：长度大于399，或最老记录时间严格小于 `f32(now + -10.0)`；恰好10秒保留，NaN比较不触发时间过期。只检查最老记录，不跨过未过期头去扫描后面的旧时间。随后追加一次，最终最多400条。

满容量时 `cap=max(2*oldCap,4)`。真实 `55797` 区分wrapped前缀与后缀：只有 `prefix>suffix` 的严格条件才把短后缀搬到旧cap后；相等时搬前缀到新尾并改变head。语料包括两种搬移、相等边界、421次连续受伤的400条裁剪、240次跨10秒窗口、完整backing复用，以及护盾耗尽和minimum-one下的历史记录。

| 记录偏移 | 真实内容 |
|---|---|
| 0/4、8/12、16/20 | 来源姓名、攻击姓名、图标的UTF8指针/字节长度 |
| 24/28/32 | 时间、减伤/护盾后伤害、吸收量，均binary32 |
| 36/40 | 扣减后的HP与最大HP；36在最终minimum-one修正之前写入 |
| 44/45 | 来源分类；category是否等于2 |
| 46..47 | 原件未写，保留该物理槽原字节 |

`spellID=0` 的真实fallback分派已对照：category0为 `Melee / INV_Sword_04`，1为 `Spell / Spell_Shadow_ShadowBolt`，2为 `Boss mechanic / Spell_Fire_SelfDestruct`，其它值回到Melee。没有用 `category0` 冒充Boss文字；`param4-1` 的br_table跳出层级决定这个映射。sourceGUID无匹配时空source切片、分类4；实际每条active记录的三个UTF8切片均解引用并比较。

## 严格字节与未知字节

924阶段保存并观察8,408,160B完整history backing。其中4,613,870B可预测字节严格比较，包含33,030B旧槽未写padding，不能把46..47一概当零或全部豁免。新grow分配区尚未写过的bytes明确为allocator unknown；当新槽成为active时，只剩真实未写46..47可保持该未知。新增指针word按解引用字符串验语义，原物理指针仍完整保留。

显式未知包括1,354,632次资源pointer字节观察（790,202非零）与2,439,658次allocator未写字节观察（981,581非零）；这些都没有被模型预测成零。每阶段还保留完整rawG2592（合计2,395,008B）、全部packet/notification payload和metadata backing；注册表、keyed容器或消息的保存并不等于它们已被独立恢复。

独立expected先生成，原件只接8个精确白名单输入字段，169,669,942B expected从未传到Node；实际输入1,717,496B。21个fresh instance，内存峰值20,709,376B，总上限32MiB；878个导入全部拒绝，实际0调用。原件PID50002在60秒deadline内正常退出0。没有app start、浏览器、下载、联网、安装包或用户存档操作。

## 验收边界

本批明确使用无单位/sourceGUID0、spellID0、英语fallback、空buff/item/modifier/proc、非致死或minimum-one输入；9组phase/protection guard不追加记录。真实Spell数据库metadata、匹配来源分类/姓名、history的healing1848生产路径、完整registry/keyed/proc/反击/致死复活仍未知。该组件尚未接入headless14、真实1089或完整一局；既有924调用不加入主切片的帧计数。独立只读复核已通过，见下方链接。

复现：`python3 reverse-engineering/scripts/check_incoming_history135.py --phase full`。静态函数/分支证据见[定点trace](../evidence/history0135-static-20261101T091534.657526Z/trace-complete.json)，未重读整个WAT或修改原件函数。

[独立只读复核](2026-11-01-incoming-history0135-independent-review.md)已通过，最终 review SHA `62ed36f102d40876a84ab2f7c67bba2d5cbbaefecd1c2aaaba4de2aef709cf06`；未重跑原件，原批范围与未知项不变。
