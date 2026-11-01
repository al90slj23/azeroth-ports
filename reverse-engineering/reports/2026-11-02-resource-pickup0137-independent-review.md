# 固定137资源1420组件独立只读复核

**限定组件域通过**：新36源批90例、90次完整1420资源kind3/4/5调用的归档证据已独立复核。本复核没有导入或执行生产模型、原件、原checker或Node runner；新增原件case、模型验证case、完整880帧均为0。它不验收完整947调度、137世界构造或Windows运行。

[最终复核收据](../evidence/resource-pickup0137-independent-review-20261101T183500.844507Z/review.json) SHA `e175290ea37ebd87c64b8d73067cc264b952e8bcc94c60d50eff6cac72478ef4`；对应[原差分收据](../evidence/resource-pickup0137-oracle-20261101T182737.085717Z/comparison.json) SHA `1e9a748dd96d9c12b239c874067c943a344f96e9fb0eb94c8c3f42510690dba2`。复核脚本为[review_resource_pickup137.py](../scripts/review_resource_pickup137.py)，SHA `11f6ec20ce019720f2ee6c5f04e1f17422ba879f475652776747357030e9666e`；源码副本、独立owned账本及终态保存于复核目录。

## 实际重读与独立检查

- 36份源码的before、after、snapshot和当前SHA一致；从checker及runner重新做静态AST/JS import递归，36个文件、91条本地依赖边完整，含最初漏掉的ZONE_ENTRIES表。预期、输入、module及四份world输入（3个查询产物加135 producer receipt）均已在执行前绑定，复核收尾再次读回哈希。
- 重读原137WASM与私有模块，逐section验证只有export section变化，新增入口1420与global0观测两个export；global0原有mutable属性未改，宿主仅只读其值。原code/data/table/callee字节未变，无start section；1420及1827的body边界/SHA从code section重新定位，878个imports均为function。
- 全部17,418已知值、8,884未知单元、完整活动及非活动backing逐条重比。另从输入槽和实际写区重建**精确None位置**，检查11,992个原有物理字节保留，包括被原fixture以poison材料化的输入未知字节；新增allocator未写区仍未知，未把它们当0。
- 独立位运算与逐步f32舍入核90例角度RNG、yaw、wrapping counter及GUID；逐包解析90个169／9,269B，核头部、packed GUID、位置/朝向、bitmask和1,440个actor字段。完整payload与归档预期逐字节相等；quaternion另以有限f32误差范围检查sin/cos，不冒充新的精确trig模型。
- 12地图×3kind×内外两侧72格矩阵逐项确认；全部XY clamp独立计算，78个controlled高度独立核，12个真实查询输入的地形高度按已冻结135产物来源及expected/original投影比较，没有执行terrain模型或重造其查询器。
- 逐case重读8192B Game前后字节，允许的44B范围之外共733,320B均未改变；消息序号及notification另比。没有以空Game fixture宣称完整合法Game constructor。World124是手工packed查询夹具，135资产身份不会转成137 fresh world boot。
- 4个仅内存里的反例均被拒绝：已写kind字节改成None、RNG改位、非允许Game字节变化、输入未知字节的物理保留被破坏。它们只是审阅器拒绝能力，不计新增原件/模型case。

原件PID/PGID97273退出0、均missing，2.179秒，90个1420返回和malloc stack均恢复1048576；实际host0、峰值20,578,304B／32MiB。复核自身PID/PGID10105退出0、均missing，0.546秒／60秒；复核期间源码、输入和审阅器哈希不变。

## 保留的纠正与验收边界

旧35源[182323批](../evidence/resource-pickup0137-oracle-20261101T182323.787663Z/comparison.json) SHA `8d957fdd974b2c71dd4cca8ddbb95e6e829fdec8fe6129928771dfc1ea5251b0`漏冻checker导入的`initial_state135_data.py`，该批原收据未修改，不作完整闭包验收。作者补齐来源、import闭合断言及world元数据冻结后，用完整原件fresh重跑同90；新旧input、expected、labels、refusals、module及WAT SHA完全相同。旧批、6例pilot和最终90不相加。

primary nearest miss的kind参数低地址读取、其它kind、资源拾取消费、947完整调度/普通432B域、137完整world/boot/一局、UI与联网继续pending。Windows visual/display与72B记录属于另一份[静态迁移证据](2026-11-02-resource-migration0137-static.md)，WASM56B及本次运行均不是native验证。

复现本只读审阅：`python3 reverse-engineering/scripts/review_resource_pickup137.py`。
