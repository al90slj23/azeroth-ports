# 0.139.0 Windows／WASM：114条技能声明的直接结构对应

当前固定的官方Windows EXE与对应WASM中，114条技能声明的ID、默认名称、图标名、升级kind列表、effect12B、numeric40B以及execution／school全部逐字一致。此处0原生执行、0WASM实例化、0新动态case；不是伤害或整局行为验收。

Windows x86-64 PE中的实际记录间距为120B，WASM为88B。工具先从PE映射的cleave UTF8地址／64位fatptr发现唯一候选，再尝试112／120／128／136／144B间距；仅120B连续114条完整匹配，不把探索时的固定file offset当验证输入。两个归一化结果SHA相同。

| 字段 | Windows偏移 | WASM偏移 |
|---|---:|---:|
| ID fatptr | 0 | 12 |
| 默认显示名 fatptr | 16 | 20 |
| 图标名 fatptr | 32 | 28 |
| 升级kind切片 | 48 | 36 |
| numeric40B | 64 | 44 |
| effect12B | 104 | 0 |
| execution byte | 117 | 84 |
| school byte | 116 | 85 |

地址、32／64位pointer／length及静态padding另存原始证据，不当作数值行为比较。已知首条cleave的spell845／伤害47等只是表值，不证明native乘法、目标选择、伤害函数地址、调用约定或运行时Game／Unit／owned结构。Windows执行、渲染、UI、联机及完整游戏仍待验证；该观察布局也不能跨版本自动复用。

[机器报告](2026-11-02-native0139-ability-layout.json)列出原件SHA、全部证据路径、字段映射、候选和试验间距；逐条raw记录与归一化结果保存在4T证据目录。
