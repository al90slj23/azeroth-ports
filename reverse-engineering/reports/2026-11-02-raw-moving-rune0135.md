# 固定135：原始资源到移动与符文消费

**451份原始资产／67,281,330B独立构造world、开局和同一运动／战斗状态，完成460帧、4选卡、44条受控移动输入与6489条阶段摘要。** 新增的是独立资源入口的模型执行和终态组合，新增原件case／调用均为0。

[模型收据](../evidence/raw-moving460-owned-20261101T234449.317665Z/model460/receipt.json) SHA `c8cee9a312f3ed4639fea4e6e26055276cfbf9d26ddf99afdbbf7b2459781f42`。固定0.135.1／`90898d5e3`；不读原件memory、WASM或预解析world。manifest声明453份，实际加载451份；两份未加载Spell／SpellIcon另记。

[`run_asset_combat135.py --motion-route first-rune`](../scripts/run_asset_combat135.py)从独立状态生成与原件实验相同的受控轨迹；它没有恢复键盘或摇杆。实际kind5在第444帧收取，随后停止并继续16帧，终态level5／XP12／gold64／HP266／通知counter2。满血cap仍不能证明非零回血增量。

[终态桥接](../evidence/raw-moving460-owned-20261101T234449.317665Z/terminal-model-bridge.json) SHA `2479b7cb37a5efe673ad1874e067aa74a529af84d16e1b9a213bf06a050ebb36`，79项通过。桥接只读取原[连续实验](2026-11-02-opening-moving-rune0135.md)的独立expected流和source snapshot，不读原件输出或执行原件。核对完整9类owner、已序列化属性／经济／技能／RNG／消息、所有44条输入、运动known／None遮罩与通知上下文。两次模型执行共享100份完全相同production，因此这是资源生产与既有逻辑的组合验证，不称第二套独立玩法实现或raw资源逐阶段原件差分。

108来源／104production及所有已读资产在执行前后保持不变；无运行时本地源逃逸。Node未启动，owned Python63273在157.858秒exit0，PID／PGID均消失，480秒预算。world三份规范文件与既有独立world完全相同。安装包与存档未动。

自然输入／App／880、致死受伤与终局、全部职业／地图／技能、存档／UI／音画／联机及latest138连续迁移仍未完成。
