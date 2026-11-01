# CAS v1 小文件只读复核

当前结论：**修复后的 decoder 通过两组正例和全部 26 类负例**。本复核没有执行原件、游戏模型或 Node 生成器，新增游戏差分 case 与完整 880 帧均为 0。

[最终收据](../evidence/opening-cas-codec135-review-20261101T173151.174099Z/review.json) SHA `5e27cf0fd619a8a5c315ac00bb4e8d803ba17c89ca8e5ba9af19c42a7b543839`，绑定 decoder SHA `16ca91ea52fdb107988d2f9c0c7b8d3b069d21df13f5a1b6091dd8ddb1199049`。checker SHA `32da4cf9dfc724029e46d5580bf96d6656c2b0c3f674a0ae534556748dd36bf0`、两份 Node 源和所有输入均与首轮相同，运行前后源与输入 SHA 一致。

原件 pilot 的 19 records / 159 blobs 展开为 1,408,160 B，logical SHA `ecbde62106b836fd20c217a1cedb9f4b1c05290dfc1a37a7fc530dff008ba49f`，与既有同输入非 CAS 原始捕获逐条 SHA 及解码值一致。独立检查 gzip、envelope stream 原字节与 runtime 的 SHA/bytes；decoder 收尾同时核验全部 blob、child edges 和 1,646 次展开引用。没有以 decoder 自己生成的输出作正例真值。

Node 保存的两条 74,143 B JSON.stringify 原字节也完全恢复，logical SHA `1e50b3ccf4d15b3c922a6e9a83c7ff257e2740c4e8f76125a754bdd5d222ce72`。覆盖 `1e-7` / `1e+21` 的原始数字拼写、`-0→0`、`你好😀`、数字 key 排序、重复 4,096 B 字符串，以及 object undefined 省略 / array undefined 转 null；原 4 项 encoder 拒绝记录另只读核对。本次未重跑 Node 生成器。

26 个实际构造负例均由 `CaptureCAS135Error` 拒绝：损坏或缺失 blob、错 bytes、替换为另一合法 blob、重复索引身份、child count、自环 / 前向依赖元数据、相对路径、单 blob / 元数据 / 整个 blob 目录软链接逃逸、重复或错序记录、在后面重放同长度合法旧记录、逻辑 SHA、运行时数量、bool id、仅 envelope 原字节变化、保留 marker 额外字段、缺失换行、未索引文件及引用次数。child count 和引用次数负例同步更新对应元数据 SHA，确实检查语义；合法旧记录重放同步更新 envelope SHA，独立累计 logical SHA 仍拒绝。循环测试仅构造非法依赖元数据，没有伪造满足哈希预像条件的内容寻址循环。

本轮核对了实际修复：封闭实验目录及 metadata / blob 的软链接边界；id 必须为非 bool 的非负安全整数，record_kind 必须为字符串；finish 累计并核对 envelope stream 原始 bytes / SHA / 最大记录大小。UTF16 surrogate 检查改为 regex，静态排除集合与原逐字符检查一致。本范围没有评估攻击者并发替换文件的竞态。

[首轮失败收据](../evidence/opening-cas-codec135-review-20261101T172237.434592Z/review.json) SHA `5a84f1d120a1ee2e949b51d671f38ac892bd2fe832809c29a7770104dcc9e503` 原样保留：旧 decoder SHA `f64afeb450c25e856608ae8c7151aa1be048d980478a1e6b8dacf793a450c33c` 仅拒绝 21 / 26，存在 3 类 metadata / 目录软链接逃逸、bool id 以及 envelope index 原字节未在 finish 核验的漏拒绝。旧批不是绿批，不与最终 26 计数相加。主 driver 外层另有 gzip / index SHA 与严格 Node 身份约束；这些旧 decoder 反例不意味着原件 pilot 或在途原件捕获本身已经损坏。

每轮仅复制 9,116,536 B 小 CAS 文件，不复制 WASM。最终 owned PID / PGID 68084，4.434 秒 / 60 秒，exit 0 且 PID / PGID 均 missing；首轮 PID / PGID 50471 的 exit 1 为发现漏拒绝，亦已终态。复现命令：`python3 reverse-engineering/scripts/check_opening_combat135_cas_codec.py`。脚本为 [check_opening_combat135_cas_codec.py](../scripts/check_opening_combat135_cas_codec.py)。

这项验收只覆盖证据传输 codec；不验收 400 / 500 帧游戏行为，不恢复任何新游戏逻辑，也不增加独立重建 domain。
