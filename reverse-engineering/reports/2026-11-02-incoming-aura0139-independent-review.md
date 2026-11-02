# 0.139 护盾清理与空 Aura 独立复核

结论：本批受控域通过。36个全新实例、31次完整1076及8次直接1173结果全部与独立参考一致。36次1600和36次83304为真实setup，72次setup不加进新组件覆盖。复核没有执行作者生产模块、检查器、构建器或原件。

- 独立重算护盾吸收、exhausted分支移除全部kind7、source-depleted分支移除全部旧source spellID，保留物理live backing且count归零。23次exhausted、7次source-depleted及1次同Game无盾跟击分别核对；8次直接1173另外核对。
- 当前拥有技能kind0和种族kind8来自139原件静态数据；owned80与racial80全字节不变，无kind12冷却Aura源、modifier或保留live源被偷偷当作空。
- 1173没有直接调用1542。全部23个constructor-derived数值词保持不变。Aura键是47..100及113..124共66键；旧count48、ready低位1且tag全0时可跳过，所以flag1/3控制例仍只有constructor原3键，其他例为69个逻辑键，不能把未写的键补0。
- 从完整raw节点独立遍历叶/非叶BTree，445次节点观察的有序键、值、child链、count与声明逻辑字段一致。物理节点未用字节、地址和分配形状仍只作为观察保留。
- 完整1173本体明确先分配768B新vector、每16B仅初始化4B tag，最终释放旧缓存并交换。38次Aura生产的指针均相对旧缓存改变；48×16槽只有tag0已知，12B payload保持None，即便旧48槽payload有已知poison值。1次无盾跟击沿用Aura，未产生新的1173调用；expected里的written_keys是上一次producer元数据，不代表跟击再次写66键。
- 全部声明投影共26,648个known cells一致、102,568个None保留，其中16,492次未知字节观察非零没有倒填。history48、英文fallback、source0/contact0、HP/累计、736/740及744 canary均核对。相对前态的100,372个Game非指针字节守恒；179个指针或树高词观察不算独立预测。
- 23来源、10生产文件、导入闭包和7作者交付文件及快照SHA均核对；11个完整静态本体重新绑定当前139原件。仅导出段改变，所有原件代码和自然callees保留。882导入全部拒绝、实际0宿主调用，39次目标栈返回逐项留存，295次总检查中的setup/allocator部分为runner断言及汇总。

范围限于研究profile的human warrior、借用flat query、显式phase1、非致死、无正reserve spill、仅含且全部移除的盾live记录、post-retain空源。仍未恢复非空Aura/modifier、保留live、kind12冷却、一般1173、28155/1466、死亡/复活、自然App或真实WorldRc；没有完成游戏或Windows执行验收。12个作者模型边界检查、pilot及preparation/selfcheck失败均不增加本批36/39。

最终独审收据：`evidence/incoming-aura139-independent-review-20261102T040751.342505Z/review.json`，SHA256 `a043d2eeddb6bd0cd9df249fd5f1929fa8ff35f9d1fb59e2b0f7ddefde8ba512`。原件进程74307及复核进程1538均有exit0/PID与PGID消失收据。来源、期待和模块由prepared预先冻结；本复核为读取后字节绑定，不是新原件实验。
