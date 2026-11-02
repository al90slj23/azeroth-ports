# 0.139.0 Thunder Clap：两批异作者联合独审

通过当前限定范围的只读独审。未执行作者生产模型、checker、builder、输入搜索或原件；独审 PID 34619，exit 0，PID／PGID 均已不存在。作者两批 12 件与 58 个源文件并集保持原 SHA。

| 正式批 | fresh | 完整922 | 真实伤害 | 正暴击 | 死亡 | slow写入 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| base18 | 18 | 47 | 34 | 0 | 4 | 90 |
| natural-world9 | 9 | 72 | 113 | 14 | 19 | 282 |

正式 target 仅计 119 次完整 922。2945／1600／1108／4677／1093 各 27 次均作前缀 setup（135 次），虽独立重算其开局／三卡／选择，未改计为新 target；1775、3755 各 119 次只验证实际空 owner。合计 27 个 fresh／492 个直接入口，不把内部 913／2189重复计数。旧 guard 失败、pilot 和 128 个输入的纯作者模型搜索均保留排除，搜索原件执行 0。

current WAT／data 重新绑定后，独参按 922→27754 半径稳定排序→10490 variant2→逐目标暴击 RNG→913 伤害／死亡／掉落→2189 effect1 同步减速计算。所有数值在每个步骤按精确分数舍入到 binary32，f64 伤害总计按目标剩余 HP 截断；死亡消耗奖励 RNG 后才处理下一个目标，未独立重置随机序列。exec2 的 1601276 系数为 0.5，半径10与暴击率0.05保留原值，未扩大范围或改卡。

base18 保留实际四 NPC 并分别近身／远离／测试 radius10 当前坐标 ULP 两侧及恰等边界；每次最多一目标。world9 使用 7 个自然 appseed，实际首卡均为新 Thunder，玩家位置为两原始 NPC 中点，Z 由独立 raw 派生地图高度验证；NPC 从未改位置或清除。51 次自然多目标施法、最多3目标、14次正暴击均严格匹配。area306 含有序 GUID 列表，mask0 尾部无 packed explicit target，不能复用 cleave 的 mask2 包。

147 次实际伤害、23 次静止普通死亡及掉落全一致。存活目标写 U124=now+3×owned68、U120=0.5、U376=0；致死后 marker1 的目标不再减速。真实 effect49/source36 为空，U356 保持继承值；非空 effect49、已有 slow376 移除和 U356 条件分支没有假装覆盖。此 exec2 没有产生1775 hit或3755 area工作，两空消费者之后完整 Game、captured owners均不变。

119 份完整 Game 入口继承共 308448B，只改显式时钟；首个受控操作只改玩家XYZ。NPC 全部 432B 存储共 205632B 从真实上一步 owner 重放，61124 个 None 均物理保留，其中 56245 实际非零。拾取旧 owner 共 28000B 另严格重放；新增 backing 未写字节仍未知，12516 个 pickup None 中实际 11227 非零。两 Rune 13328B、其他背景144704B严格守恒。全部两个 owned、racial、live1020、Aura 原始 owner保留；8568 个玩家逻辑字段（72×119）、2737 个属性值（23×119）、RNG、三套技能集合、HP／XP／击杀／counter／killcost／f64累计一致。

已知消息仅验收 116 条／5946B 的 launch/reward 有序子序列：90×306、26×169。原件还发出 317 条未独立还原的 592／169，不能称完整消息流。原始捕获另保留额外 Game 状态（例如960、1000至1063、1136至1147附近变化），其完整语义／统计 owner 尚未重建；spell-wide BTree 值由冻结 driver读取，未另捕获其物理节点。玩家72键 BTree 原始节点则已独立解码。

base18 为 54源／42 production／167边，world9 为56源／43 production／185边；并集58源／43 production。42个当前函数体、静态定义与系数表、全部非export WASM section均核对。源预期先于原件冻结，期望阶段禁读原件；本次独参只导入已冻结的纯独审 helper，未导入生产代码。

本批是完整开局→显式XP5→首次新Thunder之后的受控 direct922；未运行1238冷却调度、2123到期、925 AI或主循环884，重复直接施法不能当作真实技能频率验收。伤害仍限默认 Human／Warrior 满血239，无正数吸血／治疗；>70半径、其他技能／学校／NPC／status／proc／非空callbacks、自然 App／worldRc／externref bootstrap、完整UI／联机／存档／Windows原生与完整一局保持未知。研究与封装优化分开，目标未宣称完成。

详见[机器报告](2026-11-02-thunder-clap0139-independent-review.json)。
