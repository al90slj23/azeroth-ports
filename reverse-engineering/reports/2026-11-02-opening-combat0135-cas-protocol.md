# Fixed135 完整capture的CAS v1 / schema5

新增`run_opening_combat135_cas_oracle.mjs`与`opening_combat135_cas.mjs`，旧schema4 runner/checker/builder及历史证据保持原样。新runner完整case循环与旧runner逐字节相同，[静态对照证明](../evidence/opening-combat135-cas-pilot-20261101T171042.431971Z/output-only-adapter-proof.json)保存case-body SHA；改动限于输出编码、import与runtime envelope。仍使用同一固定135原件模块、6730→1089和14阶段入口、真实snapshot/locale、显式外部clock以及878 host deny。

stdout为一个gzip member，解压后每行是：

```json
{"cas_protocol":"opening-combat135-cas-v1","record_index":0,"record_kind":"opening","id":0,"logical_bytes":12345,"logical_sha256":"…","capture":{"$cas135_blob_v1":"…","bytes":2345}}
```

`logical_bytes`及SHA针对原完整`JSON.stringify(record) + '\n'`的UTF8字节。`capture`可为内联完整编码节点或reference；reference必须恰有`$cas135_blob_v1`与`bytes`两个键。`bytes`是其blob文件的编码JSON字节数，**不是**展开后的逻辑大小。每个blob位于`cas-blobs/<sha256>.json`，文件是无尾换行的JSON UTF8，SHA针对这些实际字节。

编码自底向上处理原始逻辑JSON长度至少512B的string/array/object；blob可以引用子blob。完整字段、数组顺序、对象属性顺序、原始Number值均保留，不排序key。原始capture在编码前全树检查保留marker键、循环、不支持的prototype、非有限Number与未配对UTF16 surrogate，遇到则明确拒绝；正常UTF8及emoji可用。undefined只按原`JSON.stringify`规则处理：对象字段省略、数组元素变为null。

`blob-index.jsonl`每个unique blob一行，字段为`sha256, bytes, file, first_record_index, child_refs`；`child_refs`按编码节点内直接reference首次出现顺序聚合为`{sha256,bytes,count}`，不展开子blob。子blob先于父blob登记；写入所有本record的新blob与index后才发stdout envelope。`blob-references.jsonl`在结束时记录每个blob的`sha256,bytes,first_record_index,last_record_index,total_logical_references`；最后一项按每个record完整展开路径计算，重复引用分别计数。

resolver应先校验文件清单、SHA、bytes、直接child edges与预算，拒绝cycle/错误marker/未登记或越界引用；按原属性顺序完整rehydrate，恢复Number的原JSON lexeme，再验证每条逻辑行SHA和累计SHA，之后才转换为普通值比较。Python默认float打印与Node可能不同；当前跨语言自检覆盖`1e-7`、`1e21`和正常UTF8，不能只用默认`json.dumps`重新格式化浮点。

| 硬预算 | 上限 |
| --- | ---: |
| case / actions / controlled frames | 1 / 600 / 500 |
| 单逻辑record / 逻辑累计 | 2MiB / 8GiB |
| CAS stdout单行 / 原始累计 / gzip累计 | 2MiB / 1GiB / 256MiB |
| 单blob / unique blobs累计 / 文件数 | 16MiB / 512MiB / 65,536 |
| blob-index单行 / 累计 | 2MiB / 256MiB |
| blob-references累计 | 32MiB |
| 编码深度 / 单record节点数 | 128 / 1,048,576 |
| JS heap / WASM memory / owned进程期限 | 512MiB / 256MiB / 60秒 |

blob写入并发16，纯字符串缓存最多64MiB/8192项。不能通过删字段、跳过backing或扩大内存来过预算；超限应作为明确失败保存。60秒外层独立PGID仍由driver控制，helper还逐record检查经过时间。

新runtime文件为`opening-combat135-cas-runtime.json`，`schema_version=5`、`output_protocol=bounded_stage_cas_jsonl_gzip`。顶层`output_bytes/uncompressed_output_bytes/output_sha256/uncompressed_sha256`对应CAS stdout index；`logical_output_bytes/logical_output_sha256`对应完整逻辑流。`capture_cas`还保存逐类最大值、unique blob数量/字节、引用计数、blob-index与references文件SHA/字节以及所有预算。

验证目前限于：[纯codec跨语言自检](../evidence/opening-combat135-cas-codec-selfcheck-20261101T170923.533576Z/selfcheck.json) SHA `6bef41616b8e0b9d00645753ddc7a69f3f71638554c6c1b622be46ffc21f6502`；[单帧原件观察pilot](../evidence/opening-combat135-cas-pilot-20261101T171042.431971Z/pilot.json) SHA `277c61ee0336ad70528e4e92d137240d8e72a2dde8580480ef45386828ad9e05`。后者19条记录、16次原件入口，完整rehydrate的1,408,160B与既有同输入单帧原件捕获**逐字节一致**；159个unique blob共250,146B，stdout index6031B压缩到1932B。全部blob清单、SHA、direct refs、展开引用计数、逐条与累计logical SHA、index raw/gzip双SHA均核对。owned PID/PGID34384退出0且missing，0.959秒。

该pilot是一个新的original-only观察case，模型验收case为0，不增加250帧闭环覆盖；没有执行长批，也未宣称500帧已经通过。新runner SHA `77fca2532d920ab720b28c7c8faf143f7a679564fe00a4e784f51cc80088424d`；helper SHA `179e9044f935f6442d9f3a32ba15a881f1ff98b388f35dabb9d6892ffd0ae927`。
