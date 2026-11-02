# fixed135普通AI：规划与incoming消费拆分

`ai_world135.py`新增显式计划边界，旧 `update_world_ordinary_units135` 保持原非致死接口和行为。本轮没有修改headless或原件reader；没有恢复完整fatal921，也没有把死亡后的910统一跳过。

## 接口

```python
plan = plan_world_ordinary_units135(frame, world, distance_map=distance_map)
# 此处没有运行1073，也没有改变HP/shield/taken。
# 上层随后规划guardian、合并canonical records并按原队列消费攻击。
result = finish_world_ordinary_plan135(
    plan, actual_post_drain_incoming, records=actual_post_callback_or_stop_records)
```

`WorldAiPlan135`保留：

- `records`：普通向量的完整规划后backing，含早期U360到期清理，保留byte/None。
- `incoming`：输入HP/shield/totals不变，绑定此次clock/playerXY及普通规划后UnitPosition。
- `attacks`：原顺序`(guid, amount_bits)`，没有合并、执行或丢弃。
- `movements`、`movement_geometry`、`routing`：全部规划结果，逻辑坐标与包坐标仍分开。
- `demo_bindings`、`demo_expirations`：GUID绑定原声明及晚期Aura移除队列；plan时不执行late4543。

`drain_world_ordinary_plan135(plan)`是原有非致死标量域的消费器，逐个调用原有incoming prefix，遇真实fatal/callback边界仍抛出。旧update现在只是plan→drain→finish，返回字段和pending列表不变。

`finish_world_ordinary_plan135(plan, incoming, records=...)`只做晚期demo清理。显式records必须与计划的count和GUID顺序一致；集合变化返回未恢复边界。清理直接作用在该backing上，不从plan覆盖停止后的坐标。`records=None`仅用于旧默认适配器保留原计划backing的路径；fatal上层必须传实际停止后的记录。该接口不证明任意callback、NPC生命周期变化或terrain stop已经实现。

plan的`incoming.units`与旧接口一致，只包含传入的普通子向量。完整普通+guardian组合必须由上层从合并后的canonical向量绑定真实units，尤其当1073近邻减伤或armor54会读全部单位时。

## 相关原件回归

未修改的 `check_demo_ai135.py --phase full`重新生成expected，然后执行完整原件921。58个既有case、66次full921、0差异。`input.json` SHA256为 `cf81ea5bf73ecabe8eeaa865c3b4b4343c0273c60753fdbdc57ca1ae42f9abd8`，与此前demo-AI报告完全相同；48项来源中只有本轮`ai_world135.py`改变。因此该批只计回归，不增加逻辑覆盖数量。

- production closure跨core_spec/resource_spec并含包入口，通过强核：48源、145边，前后哈希相同。
- 原件SHA256 `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`，58个fresh实例，所有原函数体及callee不变。
- 878个host imports拒绝、实际host调用0；WASM内存上限33554432B、最大20578304B；全部stack检查恢复。
- Node PID/PGID17131，60秒deadline，1.808秒exit0；PID和PGID回读均不存在。
- 收据 `evidence/full0135-oracle-20261102T002251.103421Z/comparison.json`，SHA256 `adf5f46407e73e012992175b43516841ab8dafbac0b9f72db19ee3662c624269`。

## 新结构自检

`check_ordinary_ai_plan135.py`明确属于模型结构自检，0原件，不累计原件case：

1. 在incoming prefix被替换为禁止调用的观察器时，plan仍完成；输入对象不变。
2. 两个接触目标的攻击均按GUID原顺序留在计划中，输入HP/shield/totals不变，clock/player及planned units正确保留。
3. U360在plan清理，但Aura1160仍留待finish；默认drain在致死时保留原有边界。
4. 显式提供的受控位置变更backing经finish后完全保留坐标/timer及非Aura字节；只执行晚Aura清理。
5. 不同count或GUID顺序被拒绝，不重建集合。

这里的位置字节是结构测试的显式输入，没有执行或验证真实terrain stop。收据 `evidence/ordinary-ai-plan135-selfcheck-20261102T002248.989301Z/selfcheck.json`，SHA256 `aaa9dab0045b395f2d8fc824950250652d2391bd2aa19a6dd7af4d8f0447202a`；49源、155边完整闭包。

## 给callback恢复的独立输入观察

新 `probe_incoming_callback_sources135.py`观察进入AI前的921组typed state，包含level.sources七个源、owned80、racial80、完整live cap/count/byte-or-None backing、原始live与unknown词、stats/progression/phase/flags。新AI默认路径重放仍920帧完成，第921帧停在同一fatal边界，109次普通死亡、267次incoming prefix；此项仍是模型观察，不是原件差分。

`original_G2056_36B_vector`与`original_G2028_8B_item_vector`显式为null未知。观察到的empty tuple不证明原版producer为空，且报告明确标记headless当前强制`modifiers=()`和`incoming_item_effects=()`的缺口，不能据此设置callbacks_complete。输入已交另一作者恢复窄谓词。

成功收据：`evidence/incoming-callback-sources135-model-observer-20261102T002438.264636Z/sources.json`，SHA256 `880fc4c769ee4da33a2261ea632bf021c873b32188d8dcbee70b92f31f77f59c`。PID18571，120秒deadline，18.600秒exit0且回读不存在；所有source before/after相同。首次observer因ability_id实际为str而误用bytes.hex，在frame1失败，失败收据保留，修正后另起新批，没有改写旧证据。

本轮生产文件SHA256：`ai_world135.py`=`379a4e33d987ae6d6cf5344fba35ccd1567366720d106b2d58bdaddad613e078`。先前run_summary与109事件追踪文件保持冻结，未修改。下一步由root连接全owner规划、ordered incoming、真实callback谓词和world stop，再做同一状态fatal全链原件差分。
