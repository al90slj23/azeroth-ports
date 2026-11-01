# 官方0.134.0普通死亡→拾取→XP的独立组合验证

本轮将独立生产模块 `combat134 → death_loot134 → pickup_entity134 → pickups134 → progression134` 接成受控组合，**367例、每例4阶段快照，共1468份快照，0字段差异**。完整原件直接调用914和2862，实际到达的1417/1820/4630等内部callee保持原样。不是把多个模型彼此往返当成原件验证。

同一轮扩展的完整1417/2862单独对照为 **382例，0差异**：56例XP创建/合并、32例金币创建、294例吸取/到期处理（含5个未触发真实收取guard的idle外来记录）。它包含旧345例回归；不同版本案例不相加估算覆盖率。旧基线已保存在提交fb74fdb及[345例报告](2026-11-01-pickups0134-spec.md)。

## 实际原件与状态范围

官方 **0.134.0 / 983346a7** WASM SHA-256 `2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52`。两个研究模块分别只新增1417/2862或914/2862的两个导出，原36 exports和所有非export节逐字节保持；全878导入均throw，实际调用0次。使用原91940分配器，不调用应用start，不访问UI、网络或用户存档。

| 验证 | 原件次数/阶段 | 实例与WASM内存 |
| --- | --- | --- |
| 混合拾取 | 382例 | 12实例，最大14,942,208B |
| 普通死亡组合 | 367例×4快照 | 23实例，最大20,578,304B |

每例从人工8192B G、424B单位、128B flat world构造。普通原72B定义来自Kobold Vermin；按语料显式复制到原分配器内，仅改baseXP为0/1/25/u32MAX。flag68=0、U40/U64/U244=-1、duration344=+0，empty items/abilities/modifiers/claims，mode0。position为region0中心(-9396,-633,0)，币位置为已解析的(+.8,+.8,0)；不把已给placement当成完整地图求解。

四个比较时点是死亡后、首次吸取后、**独立预测arrival前1 ULP**、独立预测arrival恰好到期。原件按预先生成的预测时间执行，未从原件结果反取时刻后再匹配模型。比较单位HP/死亡主字段/有效伤害、XP/level/pending/phase、完整已知56B词、容量/计数/nonce、G2412及完整四字RNG。新pickup未写的arrival+4仅在尚未定义时mask，其他词逐位比较；物理指针、所有消息/实体字段不在该投影内。

自然phase1使用level120避免2159。12例成长输入在914完成后显式由harness将phase改3，以原4630守卫阻断候选生成；这是一项控制变量，**不代表独立主循环或暂停命令已经实现**。

## 随机链与语料

普通flag0 XP按f32(base×1.65)的分数和high24严格比较，即使base0也消耗一抽。随后金币概率始终再抽；成功后bounded3拒绝product.low32>0xbfffffff，返回high32+2。实际kind1消费者1820还多抽一次23位随机角度，且其最大角度小于上界，正常返回域固定一抽。现在完整ordinary fixture的最终RNG把这一步计入，未把914直接抽数冒充最终状态。

| 普通组合语料 | 数量 |
| --- | ---: |
| `XP_fraction_strict_boundary` | 3 |
| `bounded3_exact_low32_boundary` | 2 |
| `currency_probability_grid_boundary` | 2 |
| `death_append_or_merge_before_collection` | 6 |
| `death_reward_counter_guid_wrap` | 6 |
| `nonlethal_no_reward` | 4 |
| `phase3_growth_after_real_death` | 12 |
| `seeded_complete_ordinary_rewards` | 332 |
| **合计** | **367** |

其中87例实际触发金币路径，276例死亡但概率失败，4例非致死；17例触发bounded拒绝。最终独立预测的抽数分布为0/2/4/5/6抽，对应4/276/70/8/9例，原件四字状态逐位一致。包括XP分数严格边界、金币概率网格相邻值、bounded低32位精确接受/拒绝端点、44/45 idle经验合并、counter/GUID低24位绕回，以及XP相加绕回。

## 未知边界不会继续假算

`ordinary_pipeline134.collect_at`按原逆序移除后逐笔投递XP。首笔若使2159守卫成立，立即返回 `pending_choice`，保留后面的记录；不先清空全部记录再声称停在选卡前。若升级后还有下一笔due XP，则在未恢复1513可能改变XP倍率的地方返回 `pending_stats`。即使升级的是最后一笔，也标记 `stats_dirty`，阻止下次hit/collect复用旧快照。

本轮367个终态有363个core字段投影、4个明确的pending_stats。它们的已列字段一致，不代表这些pending已完成。清除dirty要求调用者显式提供已解析的XP倍率/radius；该输入接口不是独立1513实现。5个纯Python边界/生命周期契约核对首笔停止、保留剩余记录和跨调用拒用旧属性，**原件案例数0**，不混入367。

## 独立复核与剩余范围

独立只读复核重新读取原体/exports/非7节、源码/产物hash，并纯Python重算382例和367×4快照，0差异。曾发现的多笔XP未知边界已修复、重跑并复核；中间实验和其问题记录仍保留于忽略区，不冒称最终通过。

| 最终证据 | 差分回执SHA-256 | 独立review SHA-256 |
| --- | --- | --- |
| `evidence/full0134-oracle-20261101T015951.533992Z` | `6b9e7cdbe0fe5253ec3dd0ccbda009b83a9c5156383ac405fee02cb964233f17` | `491621bc2d99a7de523b593d08227ce617616c4b08ee9f7cfc9855f1adcffdde` |
| `evidence/full0134-oracle-20261101T020143.890376Z` | `5a0b99e7e4b772125ae6480f0827847b604404bb20474f36cbd4a58e38df016b` | `16f5b755e700c09db8d2eaeb573ce49b7afea4a7cfa74d7f1e31c575c46e5158` |

每目录还保留本轮所有源码的逐字节snapshot与SHA，便于后续实现更新后复核。完整静态原链见[死亡/拾取报告](2026-11-01-death-xp0134-chain.md)。

剩余包括flagged/kind2、U244/U64奖励、可收取外来kind回调、全部物品/被动/递归死亡效果、完整1513/2159、地形/碰撞/移动、真实消息与主循环调度。玩家技能施放到该链和独立完成一局仍未验收，未执行Windows原生EXE。

```sh
python3 reverse-engineering/scripts/check_pickups134_full_spec.py
python3 reverse-engineering/scripts/check_ordinary_pipeline134.py
```

这是有限域可执行组合规格，尚不能替代完整原作核心。
