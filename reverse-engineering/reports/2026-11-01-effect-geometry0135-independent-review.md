# 0.135.1 Boss 矩形效果独立复核

独立只读复核通过。[审查证据](../evidence/effect-geometry0135-independent-review-20261101T082802.603501Z/review.json) SHA `9b0f1a3bd7332c4f571c07250241ddfd79081784cdac5aa5f775c61d0d326a3f`；[机器报告](2026-11-01-effect-geometry0135-independent-review.json)保存指标、源闭包与限制。未运行原件、修改作者源码或旧收据。

最终 080844 原件收据 SHA `94cbbfaf8d629037ac4739b334e1b6eda6642f4485467218d29a4d66508177b8`，390 组、2,883 阶段。28 份 source snapshot 含 core 包入口及完整传递依赖，与当时前后 SHA 和当前源一致。角色 2785/910/915 签名与原始 body 独立核对，只有 export section 追加批准角色；manifest/module SHA 与收据一致。重新从冻结纯模块生成全部 390 fixture 和 11 guards，严格等于保存输入/expected，再重新比较全部原件结果。

**277 组正常完成、113 组真实 host 拒绝前缀分别通过**，不能合并为 390 个完成命中。113 组最后阶段均为 `pending_original_spell_database`，有且仅有一次真实 SELF host 拒绝；此前 stage 没有 host 调用，拒绝后没有后续 op。98 组实际 HP 已变化。原 runner 对 exception message、4546/1073 stack 和 host 次数均有限定，没有用 fixture status 标签代替原件实际拒绝。纯模型的 interrupted state 再次调用会拒绝，未把前缀当可续跑游戏状态。

逐个核对 64 槽、120B 完整物理 backing：22,128,144B 严格一致；只有真实 producer 未写 scratch 再复制而来的 +20..23 被显式标记 unknown，共 13,296 个观察 byte，其中 3,324 个非零。允许的未知集合必须恰为这四个位置或空集合，不能扩大 mask；+4..7、+119 和所有其他 byte 严格比较，未知标记随稳定压缩和旧末槽保留一起传递。完整原始 sidecar 与逐槽输出逐字节相同。每阶段完整 424B Boss 记录只将 +248 实际计时器堆地址归一化；原实际指针单独保留，完整计时器 payload、其余 420B 与 shared counters/RNG 均比较。

原件阶段新增 opcode 顺序复核为 522 个 221、522 个 305、477 个 306；JSON type/id/kind/shape 与真实顺序为 498 hz、1,224 hzt、477 hzend。逐阶段 sidecar 重新解析并核对，没有从最终总数推定顺序正确。完整编码包和 JSON 字符串保存，但本批未恢复其所有 wire/小数编码，不能将这些 sidecar 误称为逐字节独立预测。

2785 初始就有 Boss 创建/战斗提示等 packet 和 banner JSON。审查保留它们为既有前缀，检查每个后续阶段前缀逐字节不变，再核对 910/915 新增消息。最初审查脚本将首阶段前缀也当新增 delta，因而断言停止；其源码版本保留在 082532 目录。修正的是独立审查脚本的基线处理，未修改作者输出、fixture 或模型，也没有新增原件执行。最终审查脚本完整源码保存在 082802 证据目录。

有限 flat/absent terrain、stationary flags0、空 incoming producers、单一真实 Boss 来源及三条固定 raw9 声明是本批已验范围。真正资源加载成功后的 registry/history/aura 与剩余 1073 尾部、真实地形/导航和其他 120 家族仍未通过本批。浏览器 bridge 的后续正常 continuation 是单独任务，不会追溯改变这里 113 个前缀的分类。本批未证明完整 915、880、联机运行或完整一局。
