# 固定0.135.1：真实App构造观察与独立730B投影

原官方构造器自然产生的App在cast时，已恢复的**730B全部一致**。其中**33B为显式输入、697B为独立预测**；另4,438B继续保持None，没有整块复制App或填零。这是对既有原件受控观察的部分投影复核，本checker新增原件调用、原件案例、完整880帧及观察批次均为0；完整独立App生产者仍未恢复。

[比较收据](../evidence/app-state0135-capture-check-20261101T121246.633972Z/comparison.json) SHA `0850bf419fe3b430117255ddd445501721c0c3c6ffb343d99fdd7c3e0b09c03a`绑定[原观察收据](../evidence/full-app0135-probe-20261101T120144.289175Z/receipt.json) SHA `fd5dba35d0aeacffe822ce070fd5bc218da8352a5b725e48c166df289b91c726`。原观察捕获App=21088840、Rc=21088824，cast时memory为27,787,264B；它与旧32MiB叶子oracle是不同host/运行域，本checker仅只读receipt，不恢复或运行原件memory。

## 输入与预测边界

[check_app_state135_capture.py](../scripts/check_app_state135_capture.py)仅从原`app5168_hex_at_cast`读取以下模型输入，其余已知字段由[app_state135.py](../reconstruction/core_spec/app_state135.py)和[history组件](2026-11-01-app-history0135.md)生成。expected和完整None mask在比较之前独立保存，原App原始字节另存为observed文件。

| 分类 | 字节数 | 来源与验证意义 |
|---|---:|---|
| 显式输入 | 33 | 首map seedpair@4008共16B，transport指针@4768共4B，LCG seed@4928共8B，server指针@5056共4B，启动flag@5161共1B；这些字段不算独立预测 |
| 空history | 240 | `empty_history135()`独立生成20个`(0,1,0)`byte-vector头，不从App复制 |
| map头及后3组seedpair | 112 | `app_hash_maps135(RandomState135(first,second))`生成四个空table头64B和后3组连续seedpair48B；没有直接复制128B map区 |
| seed派生字段 | 8 | 由LCG输入按原integer mix/select独立计算App4936 |
| 其它原构造写入 | 337 | 精确宽度常数、queue/vector头、option tag、显式零写入等 |
| 保留未知/未激活 | 4,438 | 完整None mask保留，不比较、不据实际零值改成已知；三个live-copy区未作为输入 |

直接输入LCG seed为1793534541444，首map seedpair为(1048039,14549904)，transport指针14549552、server指针20678464、flag1。这些地址和entropy均属于该次原件运行的opaque输入，不是独立allocator、熵或所有权生产者。

checker完整AST依赖为7源：自身、`source_closure135.py`，以及core包入口、`app_state135.py`、`app_history135.py`、`upgrade_values.py`和`binary32.py`。前后SHA一致并另存source-snapshot；不导入原件builder或trace，因此不同于静态32例的10源闭包。生产模型和trace未修改；旧静态7源依赖遗漏已在[静态主报告](2026-11-01-app-state0135.md)另行补正，不覆盖历史收据。

## 真实指针与剩余限制

通过真实12B闭包环境和guarded vtable5305816再次确认`App=u32(env+8)+16=Rc+16`，对应25ms interval。cast时strong3/weak1/borrow0属于原件观察；模型不预测最终holder数，也不把构造初始strong1误当作cast时strong。

原观察的官方初始化已返回，8次idle880调用完整返回，但另外的WebGPU/SwiftShader渲染路径发生`createBuffer`错误并panic。因此本次吻合不代表渲染器健康、完整启动成功或已能游戏。它也不恢复原table/global/externref状态，不代表独立App、selected-profile、transport全部所有权、renderer或完整游戏已重建。

原观察与本checker均不使用现存用户profile；本checker不启动浏览器、原应用或网络，也不访问用户存档。原件函数体和原内存未被本checker修改。[独立复核通过](2026-11-01-app-state0135-capture-independent-review.md)；[机器可读范围](2026-11-01-app-state0135-capture.json)保留全部限制。

复现：`python3 reverse-engineering/scripts/check_app_state135_capture.py`只复核上述固定原观察收据；不会产生新原件调用。
