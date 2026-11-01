# App history与地址熵的独立只读复核

对 [app_history135.py](../reconstruction/core_spec/app_history135.py) 与最终 [24例／96调用收据](../evidence/app-history0135-oracle-20261101T114831.615348Z/comparison.json) 的独立只读复核通过。该收据SHA `254783e9554e47977d44f2f07f4ce2b433db14d21ef4ac443f4470c56ba9eb05`；生产模型SHA `d8f423c6973be125115857672d506bfc0d7d53f77cc03e04b08837a97376b7d2`。本次新增原件执行0，未导入或运行生产模型。

[最终独审收据](../evidence/app-history0135-independent-review-20261101T115315.665894Z/review.json) SHA `cb7653a5c960e0b0e2438e6c2d64a5b0700f5567ef8fba835c59db0e2190371f`；[机器报告](2026-11-01-app-history0135-independent-review.json)保留原查询／body、完整来源、观察词和边界。复现脚本为 [review_app_history135.py](../scripts/review_app_history135.py)。

## 实际核对

- 独立收集Python import闭包及实际Node runner，确认最终10份源码与运行前后、source snapshot一致。旧7份记录漏掉包入口执行的`upgrade_values.py`／`binary32.py`，作者已补闭包重新冻结运行。旧证据未改；input、expected、私有模块、manifest、typed replay与results六份产物逐byte相同，24例和96调用不相加。
- 重新读取原90,959,080B WASM，独立解析section与export，确认全部非export节字节一致，原导出前缀保留，仅追加4个函数与原mutable stack global0的读出；原stack初值1048576及所有body均未改。通过SQLite只读byte范围重新读取53845／28797／60416／81334／4253的WAT，并交叉核对源WASM body SHA。
- reviewer直接解释原53845的30条`i64.store`，重建完整240B，确认覆盖每个byte恰好一次并形成20个`(0,1,0)`头，再逐例核对offset0..7、三种poison及完整512B。初始化与空28797返回后的24,576B累计buffer观察完全一致；28797的20个conditional free分支在真实cap0下跳过，未由此宣称非空析构通过。
- 逐例核对原60416的seed0＝1048576−17、flag1，以及原81334首词＝1048576−1和返回stack1048576。已知词／flag共408B；两种allocator地址词共384B仅核对真实范围并单列opaque。expected中这两个词仍为None，未在运行后填入地址，也未写Once／随机全局绕过原初始化。
- 独立解码WASM data section，保留5222424处16B空table头的实际segment文件范围与初始化零隙；结果为`(5222416,0,0,0)`。结合原4253的seed／App写入窗口，对三个显式RandomState重放独立重算128B map头、first的逐次wrap64和next first＋4；App4120以后其它字段没有混入四map。
- 最终原件进程PID／PGID15605当前均missing；runtime为24fresh／96调用、878导入全拒绝且实际0、峰值14,680,064B低于32MiB。reviewer没有调用原件、浏览器、EXE、网络或存档。

这份验收保持原范围：history为空，地址熵仅固定真实1MiB stack下的已知投影；seed1分配地址没有独立预测。四map128B仅是已初始化typed-state和静态4253依据，不是新的原4253运行差分。非空history与析构、真实App构造／所有权／history使用、880、UI／联机及独立整局仍未完成。
