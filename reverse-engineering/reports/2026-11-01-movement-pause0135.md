# 0.135.1 暂停与恢复的移动快照事件

[最终完整原件收据](../evidence/full0135-oracle-20261101T061549.649714Z/movement-pause135-comparison.json) 通过396组、1,136次完整1371命令入口，604条真实221移动消息全部匹配，0差异。7项缺失、非空来源或坏输入拒绝测试通过。此项恢复的是35514/25472共同使用的26200 NPC移动快照consumer，不是按候选卡片数量补计数。

[独立模型](../reconstruction/core_spec/movement_pause135.py) 提供 `moving_sequence_delta(records, now_bits, *, auxiliary_motions=None, claims=None)`，返回 `.count` 和有序 `.guids`。每个完整424字节NPC只在marker==0、duration344>0、`f32(duration344+start340)>now2352`时入选；没有owner/family过滤，也没有GUID去重。35514暂停与25472恢复分别对每个入选快照让G2412按u32加1，并生成221 stop/resume事件，不改NPC记录或RNG。

26200在NPC之后还拼接G660/664的112字节辅助运动和G2112/2116的88字节claims。本模型要求二者显式空tuple，缺省None和非空均拒绝；不能把未知来源自动当空。组合层应在实际35514/25472调用点应用count，并在原件同G中核对G664/G2116确实为0。

专用验收通过真实1371 raw tag7触发phase1→3暂停及3→1恢复，保留原35514、25472、26200与所有包构造callee。比较完整NPC424字节、phase、RNG、u32序列、包和通知数，并直接解码每条实际221的packed u64 GUID、序列与stopflag；没有修改原件payload。覆盖重复和零GUID、u64上限、seq环绕、marker/NaN/正负与极小duration、exact end及binary32加法舍入、mode低位/phase/payload/discriminant门控和seeded顺序向量。

[静态WAT与body证据](../evidence/movement-pause0135-static-20261101T061650.605238Z/movement-pause135-static.json) 核对完整WAT SHA及8个实际function的签名/body SHA。执行模块只增export7，非export所有原件字节保留；全部878host import抛错、实际0调用，512page和60秒子进程截止生效，峰值14,876,672字节，约0.82秒。源码闭包含package init在生产导入前冻结，预期在原件执行前生成、序列化并读回，运行前后核对source/fixture/module身份。没有start、EXE、网络或存档访问。

完整raw221载荷已留存，但非平面地形位置修正、完整duration/geometry编码、非空aux/claims仍未知。自然升级选择phase1→2以及选择后的恢复是否在正确时点调用本consumer，需要父任务same-G链再次验证；本批不把1371的1↔3测试升级为完整880验收。
