# fixed135 incoming回调源：空profile构造与普通选卡保留

新 `reconstruction/core_spec/callback_source_owner135.py`恢复显式空研究profile的两个物理向量owner。它不把`level.sources`空tuple或原件观测0当成生产依据；headless、旧reader、AI拆分、计数与此前事件观察文件均未修改。

```python
owner = empty_research_callback_sources135()
items8 = owner.items8
modifiers36 = owner.modifiers36
# 在真实accepted ordinary selection事件处：
owner = retain_callback_sources_after_selection135(
    owner, actual_candidate, phase2587=2, selection_kind2585=0)
```

两个输出分别为 `CallbackVector135(8, 0, (), capacity_word=0)` 和stride36对应对象。cap0来自原件显式构造写，不是从storage长度推算；原始header的ptr4是align4 dangling sentinel，回调在count0时不消费该指针。callback谓词可以直接消费这两个typed owner，不再从semantic空源反向制作physical vector。

## 静态生产链

固定原件SHA256 `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。以下相对行号指各函数定点WAT。

1. 1560:194–206调用25765，返回值写入constructor scratch24起的60B。
2. 25765先调用9868，输入是selectedProfile+152。9868显式初始化五个Vec header为0/4/0；输入count P160=0跳过ranked-effect遍历及其40B队列，P164=0跳过flag条件改写。
3. 25765再检查装备套装。20363扫描P260..332的19个item ID。全0时1976(0)沿真实范围分支返回notfound：默认分发表后`u32(0-1)<99999`为false、`0<100000`为true，最终1976:1341–1344写-1。
4. 20363各套装计数保持0并返回tag2；25765跳过附加gear effects，返回原五个空header。
5. 1560:1246–1278将60B复制到scratch2112..2171。Game来自scratch+88，因此item8为G2024cap0/G2028ptr4/G2032count0，eventdef36为G2048cap0/G2052ptr4/G2056count0。空event sort和1512不产生新条目；1512对这两个header只读。

生产器输入 `CallbackSourcesProfile135(count160, flag164, equipped_item_ids260)`必须显式提供0、0和19个0；任一unknown、非零或装备变化返回边界。命名便利入口`empty_research_callback_sources135`声明与研究零填充376B profile相同的输入域；它不证明自然6730 App/account/menu提供的真实档案为空。非空账号不能调用该便利入口代替真实producer。

## 1072普通选卡

- `upgrade`只改已有owned80及其升级计数，经25368计算值后跳到公共结束；不经过2435装备重建。
- `new`通过26967只读既有ability20 modifiers，初始化/追加owned80，再由24129重排owned priority；这一步不重建item8/eventdef36。
- `gold`调用28796改变货币，源向量保持。
- 公共1512/4600继续读取既有源。kind1/2、装备、trait、summon、item等其他变体一律拒绝；2435及非空profile/gear的完整生产仍待恢复。

该保留API只描述选卡对这两个源owner的影响，不自动证明未恢复技能执行、装备变更或未来事件没有其他副作用。当前7次普通升级可沿真实accepted card事件保持这两个空源；不能由“末状态仍空”倒推出该链已发生。

## 新原件组件差分

新 `check_callback_source_owner135.py`先冻结独立expected和完整源闭包，再执行新reader `run_callback_source_owner135_oracle.mjs`。不安装App、externref、旧snapshot或原件输出输入。

- 9个fresh实例执行完整1560，覆盖9个class，明确blank376B profile、Human、Elwynn、seed0。这里只是constructor输入域，不宣称这些组合都能从UI选择。
- 同一Game随后执行64次完整1072：每class五种ordinary upgrade、empty upgrade与gold，Warrior另有new cleave。phase2/kind0/candidate是明确受控组件输入；没有声称自然XP/选卡producer执行。
- 预测并比较两个完整header、入口profile的count/flag/19装备ID前后切片、构造incoming48 header，以及选卡后phase。0差异。完整函数执行次数不等于函数全部行为已经独立实现。
- 17源、32条本地import边，通过跨core/resource及package入口强核；expected先于原件，所有来源和冻结artifact前后相同。
- 256MiB Node heap上限、32MiB WASM上限，最大20512768B。878个host imports拒绝、实际host调用0。PID/PGID34437，60秒deadline，0.473秒exit0，回读PID与PGID均不存在。
- 此批复用完整来源校验的full135 host，没有增加stack global export，因而没有逐call stack收据；报告保留这一限制，不借别批的stack通过补齐。

收据 `evidence/full0135-oracle-20261102T003504.117627Z/comparison.json`，SHA256 `d4d48ab268e42a5b6abb9bb826cdd3238c2832736ba0d22536d112a9f27ba354`。这里只验证源header投影及上述控制字段，不是完整fatal、完整1072语义或自然游戏流程验收。

## 另补真实构造字段

同一1560 body SHA256 `064fd2a7ae947b934f9a398c75aaf17923188e8fad36ddf60849f69f960837fe`：

- scratch1056写i64 `4<<32`、1064写i640，经+88复制后得到incoming48 G968cap0/G972ptr4/G976head0/G980count0。
- 相对816–818的scratch1720 i32store0得到G1632 lives0。
- 相对1170–1172的scratch2655 byte store0得到left2567=0。
- lives/left是成功constructor公共常量写，1512不改它们。1072另一个definition+36 tag16的trait分支能增加lives至上限2；它不是当前ordinary owned80升级路径，不能把初态0推广到该未恢复分支。

这些字段的单独静态依据已交root供RunLedger使用，没有将原件观测0回填为独立输入。

## 更正与剩余缺口

此前fatal-dependencies报告提到的tail.secondary112是G1856域；真实movement-stop辅助112B向量是G656/660/664，不能因为stride相同直接替换。其新owner正由另一作者恢复，root已收到该更正。1560的G656cap0/G660ptr8/G664count0对应scratch740 i640与748 i648，但其后续entry/技能生产需单独证明。

静态定点收据 `evidence/callback-source-owner135-static-20261102T003650.844444Z/proof.json`，SHA256 `3505a7d7a0245326575d1ad4350d8e626a4958b697e70e9f4b6d9fa22d576833`，9函数完整定点读取、SQL只读、无1.3GB全文扫描、0原件执行。生产模块SHA256 `ea272da71a786cba5846539a307ac6761438674d7c7b6f9f1b9722149bf734eb`。

下一步由root在真实opening ledger持有这两个source owner，并在accepted selection时投递保留事件；随后将canonical live32及这些物理源交给已恢复的post-history callback窄谓词。尚未得到完整同状态921→5620→1938原件差分，本轮不宣称自然致死闭环完成。
