# 1367死亡复盘异作者只读复核

**在已声明的借用incoming48历史组件域内通过，未发现阻塞问题。** 独立重算全部103例原件JSON、输出容量、筛选与分组；没有执行作者模型、checker、builder或原件，也未修改作者源码、primary或registry。

原作者收据SHA `05c30dcb209a287d5a722f80fa5e10207c8b173fcb8f0866210677157da8d090`，固定0.135.1 / `90898d5e3`。原WASM SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`；1367完整body SHA `f5b307b9d13c9e9c899ddca880349c2ba03815cf12508b3669dc02c37db502d7`，参数`i32,i32,f32`、无返回值。

独审脚本[`review_player_death_recap135.py`](../scripts/review_player_death_recap135.py)仅使用Python标准库，SHA `b0c92d1116587a58022028844e2bf24d4fc259d6faec092708f9c5d6f2a7b088`。独立读取原件1367完整3056行WAT及13106、6332、85719、44448、51418、11735、52241、54802，重新解析WASM段、导出、878函数导入、单一stack global和静态rank字串；私有模块确实仅改export段。静态函数窗口/body SHA已保存在独审收据。

## 核对规则

- 最近10秒是`stamp >= f32(reference-10)`，没有排除未来事件；NaN时间不满足比较。不修改原ring，也不把过期行从输入删除。
- total/absorbed/avoidable是三次有序binary32归约，初值−0；avoidable只收mechanic字节==1，显示布尔则任何非0为true。
- 连续hit仅按who+what匹配、当前stamp减上一组最新stamp<=1合并，不取绝对值。逆序时间可合并。合并后使用最后一条metadata/HP，伤害和吸收按原件顺序做f32加法。
- `hits`取最后8组，**不是按伤害取前8**。全局`by`同样按who+what聚合，保留首条metadata，按伤害的`f32::total_cmp`变换稳定降序，只显示前6组。长度20/21的两个排序路径均检查，6332合并时相等保留先到元素。
- killer取筛选后最后一条；secs取第一条至reference并夹0..10；ago下限0；hp为HP/max(maxHP,1)夹0..1。NaN/nonfinite输出由实际52241规则写0。
- 85719先加带符号的`0x3effffff`再去掉小数位，不能用Python默认`round`代替。52241小整数为十进制，其余有限数固定3位；11735仅对换行单独写`\n`，其它控制字符如CR/TAB/NUL写小写`\u000d/0009/0000`，中文和emoji保留UTF8。
- Vec<u8>按每次实际append原子增长：需要时取`max(2*capacity,needed,8)`，因此容量可为1142等非2次幂。完整JSON和容量都独立匹配。

## 结果与物理范围

最终[独审证据](../evidence/player-death-recap135-review-owned-20261102T000113.244785Z/review/review.json) SHA `9a0b879daa2d18d2b87d3d56786134f4497c0348d32acc338ae353310b7a6dcf`。

12个完整来源、20条本地导入边与冻结快照逐项匹配，执行前后再核；输入文件只含history/id/reference，期待没有传给原件。103例共1345个active输入行，筛选1291行（含48个future行），生成1287个hit组、808个全局source组；4次相邻合并含1次逆序合并，9例走>=21的长排序路径。103个JSON共120,301B，全部逐字相同，包括wrapped400、中文/控制字符、有序f32抵消和nonfinite样例。

完整历史backing78,480B和header1,648B的执行前后字节不变；其中62,340B非重定位输入字节与fixture直接相等，3270B padding全部保留。字符串指针由原allocator重定位，独审不预测地址；所有已消费UTF8字串通过完整JSON重算绑定。原件runner还对全部分配字串执行执行前后不变断言，独审已核冻结代码和成功退出；但原结果没有逐段保存原字符串backing，因此不把它冒称独立逐字readback。

原件103次完整1367/103新实例、0host/878deny、14,614,528B/32MiB、4447个stack检查的收据与输出一致。原PID/PGID63836已终结并再次只读确认不存在。

独审reader PID/PGID85231退出0，0.5056秒后两者均消失，独立45秒期限；stdout/stderr、owned-process和terminal收据均保留。独审新增原件调用0、production导入/执行0。

## 使用边界

结论只接纳这103例及相应WAT恢复规则；没有把它扩展为完整1073/5620/1938、自然玩家死亡或完整游戏。未使用的输出capacity尾部字节只是原件观测，未独立预测；分类仅恢复原5个标签；任意NaN payload参与多来源排序、非法ring、其它分类值仍未接纳。

后续fatal消费链可复用此脚本的纯`reference(inp,ranks,Counter()) -> (capacity,JSONbytes,diagnostics)`，并把本103例作为已审依赖；复用者不应把它计为自己的第二次1367独立恢复。
