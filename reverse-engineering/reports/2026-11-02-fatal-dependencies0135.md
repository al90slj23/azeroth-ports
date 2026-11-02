# fixed135：自然致死整合前的事件顺序与统计来源

本轮仅新增模块、静态脚本及纯模型事件观察，没有修改 `headless135`、AI、原件 reader、primary 或 registry。新原件调用为0；尚未完成 seed0 第921帧的完整原件差分或完整致死实现。

## 可执行交付

`reconstruction/core_spec/run_summary135.py` SHA256 `71ee8897fa52669193dacd14de08bb53f2fbf987a9470516a4a455e27419f0d2`。

```python
owner = empty_constructor_counters135()
# 必须在实际 on_death 回调内消费该次 DamageResult，不能事后扫描存活/死亡列表。
owner = accept_ordinary_death135(owner, damage)
seven = summary_counters135(owner, canonical_level, canonical_currency)
```

`RunSummaryCounters135` 持有1084/1088/1092/1096/1104五个u32。初态来自1560显式写集。当前只实现普通死亡事件的1084和1088更新：`applied && dead`，三类标签40/64/244均为-1，目标已写marker1时，kills增加1，elites增加原始U416低位；加法按u32回绕。特殊目标返回明确边界。它不从当前records、怪物生成数、经验或掉落数反推历史。

其余字段的初态0并不证明一个任意运行状态中仍为0。1092/1096/1104的后续producer与本模块接线都尚未恢复；调用者必须保留这一覆盖边界。`summary_counters135` 是显式owner的组合接口，不是对缺失producer的完成声明。

## 921与致死的真实顺序

固定原件135 SHA256 `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。以下行号均相对各函数WAT。

1. 921先规划整轮单位行为、更新相应物理记录及临时队列；移动包的队列处理也位于incoming队列之前。
2. 921:7410–7510遍历scratch124/128/132的16B incoming队列，在7491逐条调用1073。第一条致死并不会使本循环提前退出。
3. 1073入口读取真实phase2587。第一条致死调用5620后phase成为4，后续队列项仍调用1073，但在其入口phase guard返回，不再扣血或追加history。
4. 921随后继续已规划队列：914调用位于8448，1453位于8521，910位于9280；不是重新开始一轮单位规划。910入口只有index/count及单位marker检查；其2587读取位于特定cast分支，不能概括为所有死亡后910均无操作。
5. 5620先写phase4、408=1、412=now。mode0调用17119，然后生成1938 defeat；17119尾部自身依次调用17217和16340，所以NPC→auxiliary→claim均在通知前冻结。5620中直接调用17217/16340的后续代码属于非零mode分支。

当前headless先完成普通AI及incoming，再规划guardian。这在致死域不能当作921的真实顺序。后续整合需要先规划所有受支持owner，再按队列顺序消费incoming及其他动作；原版fatal中的停止写必须作用在规划后的canonical backing上。不能用旧phase1重新规划guardian，也不能直接丢弃尚未恢复的910队列。

## 七计数与其他致死输入

| 输出 | 可继承的当前独立来源 | 本轮恢复及边界 |
| --- | --- | --- |
| 1432 level | `collection.level.progression.level` | 现有真实成长producer；不要用选卡次数代替 |
| 1084 kills | 新事件owner | 914:5733–5736，每次accepted newly-dead；本轮实现普通标签域 |
| 1088 elites | 新事件owner | 914:5737–5746，U416低位；不是从definition名称猜精英 |
| 1092 guardians | 1560初态；运行值需新producer | 914:7295–7298存在后续特殊分支；普通回调109次不能证明它仍为0 |
| 1096 bosses | 1560初态；运行值需新producer | 914:6901–6904存在boss分支；未恢复完整producer |
| 1100 gold | `collection.currency.earned` | 135函数28796累加实际award；不是可花费的`gold`余额 |
| 1104 chests | 1560初态；运行值需新producer | 20660:289–292成功消费增加，2862和38321可调用；不能仅因普通死亡回调没有该事件就确认0 |

1560的Game基址为scratch+88。1084..1104对应scratch1172..1195，其未对齐复制来源为scratch2807..2830；2795..2838的显式zero store先于这些复制。该依据只证明构造初态。

incoming48也有真实构造初态：1560 scratch1056写i64 `4<<32`、1064写0，形成G968/972/976/980的cap0/ptr4/head0/count0。已存在的 `incoming_history135.append_incoming_history` 可沿每次实际reduced incoming追加；`incoming_source135.resolve_incoming_source135` 能解析当前普通怪的源名/U416。1073先写HP1440与f64 taken992，然后追加history，之后才进入rawbuff13/item22/984及最终HP重读。因此历史应保存callbacks前HP，不能在5620后用HP0重造。

当前headless尚无history owner，也没有完整incoming callbacks continuation。能继承HP、armor、shield、time、player/source GUID、RNG、physical units、secondary112和claims88等已有owner；不能凭这些值将`incoming_callbacks_complete=True`。普通源的首次registry分支在U244==-1时跳过；其他registry/source类型仍需真实producer。hero文本由独立的 `profile_hero135` 工作交付，不能由输入类缺字段推出空字符串。

## 纯模型事件重放

最终观察脚本 `scripts/probe_run_summary135.py` SHA256 `4c4874be44e80747fc66c53bdabe94fed2e23da8107e8afb10598d4156d99600`。它只在进程内包装既有函数，保留所有原返回值与异常，不改任何源文件；新counter/history owner不反馈给冻结模型。

输入为研究empty-profile的 `EmptyOpeningInput135(1,1,0,0,42)`，原有 `FirstRuneRoute135`，dt为f32(.1)。实际 `consume_ordinary_death` 调用逐次记录frame、phase、GUID、rawU416、definition及更新后计数；包括同一阶段内的连续死亡。`cast_events135.apply_hit` 对每个applied+dead立即投递该回调，headless `on_death` 在继续下一击前调用它；因而该观察不依赖阶段末records是否压缩、删除或复用。

- 前460帧有38个实际普通死亡事件；920帧有109个，全部在owned（对应player阶段）。存在同帧2至3次事件，均单独保留。
- 920帧顺利完成，921帧停在原有 `before_unresolved_death` 显式边界；没有宣称完整921成功。
- 267次incoming prefix调用，包括第921帧fatal。最后一条源为Young Wolf，HP从1066216559变为3220333819（均为binary32 word）。history cap128/head48/count72，保留该次callbacks前负HP。
- `summary_counters135` 组合结果为level8/kills109/elites0/guardians0/bosses0/gold115/chests0。后3类事件覆盖仍未完成，这些数只是此观察owner的状态，不能作为原版数值已一致的证明。
- 106项来源哈希前后不变；0 original、0 native。PID7172/PGID7172在180秒deadline内正常exit0，17.724秒，独立回读确认PID不存在。

此重放属于独立模型事件观察，不是原件差分。根代理另安排将新owner与已有moving460原件raw Game七计数交叉核对；本报告不提前计入其结论。

## 收据

- 静态函数seek与原件body绑定：`evidence/fatal-dependencies135-static-20261102T001521.877775Z/proof.json`，SHA256 `b237777fcf3098aefe496a38f11b9694c6682c4926533bcad1c21e5811a4ceb1`。9个完整定点函数，无1.3GB全文扫描；SQL只读。
- 最终事件观察：`evidence/run-summary135-model-events-20261102T001522.269306Z/trace.json`，SHA256 `703e0069f2c835a00e7f8c0569fe41e1990a156df5f10d7ec48ab8b4682ce0ad`。
- owned receipt：`evidence/run-summary135-model-events-owned-20261102T001521.808056Z/receipt.json`，SHA256 `d967f548983bd12bba3f0ff5793fec04376d099433ad64306f41a4027fbccc27`。
- 较早没有精确phase标签的观察和较早静态收据保留原样，不累加case数，也不以最终源码hash回写旧收据。

下一最短闭环是把counter/history owner接到真实ordered incoming/death事件中，恢复当前源域可证明的1073 callback分支，按921原顺序冻结同一物理世界，再以完整921及5620/1938原件结果验证；仍未恢复的910、特殊死亡、宝箱和非空回调必须停在真实边界。
