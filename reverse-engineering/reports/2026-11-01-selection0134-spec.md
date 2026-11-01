# 官方0.134.0完整选卡函数验收

官方 **0.134.0 / 983346a7** 的完整函数 **1073** 与独立80B记录数值实现完成 **779例对照，0差异**。这是本版原函数的新执行结果；没有把0.126.0结果或单独25368数值helper的案例数计入本次验收。

本次逐例比较 **完整80B拥有记录 + 5个标量**：owned count1660、phase2579、selection kind2577、pending2368、candidate count1904，共6类字段。原1073及本次命中的原内部后处理函数照常执行。

## 原件、执行范围与隔离

| 项目 | 核验结果 |
| --- | --- |
| 官方原件 | 90,953,762B；SHA-256 `2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52` |
| 完整1073 body | `[5741770,5758218)`，16,448B；`264e7ce32add4bcd3695a8429c1b342c392aa83091b76a37c5f99c646b267d02` |
| 研究模块 | 90,953,857B；`0ce9e7d78a3fe5d09c5d43d4cd8ffbb05073492818d9c0952ecd3399b332f1de` |
| 唯一变动 | export节7，保留原36个导出，新增1073/1513/4600的3个研究导出；其他节逐字节一致 |
| 分配器 | 原导出`__wbindgen_malloc`，新版函数91940，`(i32 size,i32 align)->i32` |
| 实例与内存 | 25个新实例，每32例重建实例；最大14,942,208B，运行上限32MiB |
| 宿主调用 | 878个原函数导入全部立即throw，实际调用0次 |
| 应用启动 | 原件没有隐式start节；未调用`start`或`__wbindgen_start`，未启动完整游戏 |

完整官方模块确实被实例化；本轮只调用研究导出的1073与原分配器。没有替换内部辅助函数、读取用户存档或修改已安装游戏。完整原指令、数据、表、内存定义及globals均保留。

所有fixture从原分配器取得新内存，再写入人工状态：warrior/human、等级1、实际`cleave`定义地址5463472、空modifier/装备/loot、mode2574=0、pending2368=1。新版候选cap/ptr/count为1896/1900/1904，owned为1652/1656/1660，phase/kind为2579/2577；这些位置已由新版完整指令独立定位，未套用历史状态偏移。

## 775个笛卡尔样例与4个边界

有序kind序列长度为1、2、3，kind取0..4，分别得到5、25、125个序列；每个序列交叉tier0..4：`(5+25+125)×5 = 775`。重复kind及顺序均保留，读取前一次更新后的真实记录。

| 组别 | 数量 | 实际结果 |
| --- | ---: | --- |
| 全部有序kind序列 × tier |775|完整80B记录与5个标量逐项一致|
| phase1入口守卫 |1|记录及owned数不变；保留phase1、kind0、pending1、候选数1|
| 空kind，tier999 |1|不读取tier数值helper；记录不变，完整收尾返回phase1/kind255/pending0/候选数0|
| owned index1越界，owned count1 |1|记录不变，完整收尾仍返回phase1/kind255/pending0/候选数0|
| tier0新能力，空modifier |1|完整初始化80B与neutral-additional模型相同；owned count1且收尾完成|
| **合计** |**779**|**0差异**|

## 独立实现与后处理边界

本轮复用生产规格中的`AbilityRecord`、`apply_upgrade_card`、`initialize_ability`与`neutral_additional_bytes`：验证的是已迁移的有序binary32记录更新及tier0中性附加字段初始化。源码保留历史名称，不代表带历史phase字段名的高层选择API已整体迁移。

原1073内部实际经过本例命中的共享处理，再调用原1513属性重算和原4600收尾；独立模型仍把共享后处理、属性重算、通知、装备等副作用列为pending。本次没有用模型补齐或替换原件尾部，也没有因为原件运行通过而把模型的pending改称已经实现。属性输出向量没有另与独立完整属性规格比较。

本次范围仅包括上述合成`cleave`状态。非零新技能tier、其他技能定义、其他待选队列、下一批候选生成、非空modifier/装备/loot，以及完整游戏仍未验收。779例不是全部输入的穷举，也不能证明整核心等价或替代核心已经可玩。

## 归档与独立复核

真实证据目录：`evidence/full0134-oracle-20261101T003559.972819Z`。JSON报告固定全部脚本/模型源码SHA、案例/原件结果/差异文件SHA，以及以下回执：

| 回执 | SHA-256 |
| --- | --- |
| `selection134-comparison.json` | `db02302326f5f72a01cdc44ccc5fc4156ade7768c3820af9fc67aecc4e431a69` |
| `manifest.json` | `43ccbeb88da74b72e9a0702c8802ddaa8d19527ee8619125a5785423bf2c70a1` |
| `independent-review.json` | `db34627dc88a92ea912bea2cdfff395dd1ef56d672eef7b0bc9befe0c317cf68` |

独立只读复核未发现实质问题：重新逐字节比较非export节、解析新增导出、核对新版body和状态偏移，读回779条案例与原件结果，并重新运行纯Python模型逐例核算779/0。复核没有编译、实例化或执行WASM。

复现命令：

```sh
python3 reverse-engineering/scripts/check_selection134_full_spec.py
```

本次整理报告只读取既有归档，没有额外执行原件，也没有commit/push。
