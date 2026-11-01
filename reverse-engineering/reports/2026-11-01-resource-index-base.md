# 基础MPQ资源索引与独立读取器

7份基础MPQ现已建立可执行的独立读取路径：**29,595条资产路径＋7个内部listfile，共29,602个命名块，全部字节与固定StormLib参考读取一致，0差异**。实际比较1,636,167,198B；全部block均有明确名称，没有通过猜扩展名填补未命名项。资产路径之间无跨包同名，唯一重复名称是内部`(listfile)`。

这些资源来自[已完成CRC验收的基础RAR](2026-11-01-resource-acquisition.md)，包内程序仍是0.102.3。最新0.135.1程序独立保存；本报告不把基础资源包自动认定为0.135.1的完整资源清单。

| 已命名容器 | 数量 |
|---|---:|
| BLP纹理 |17994|
| M2模型 |6988|
| WMO世界模型 |2731|
| ADT地形块 / WDT / WDL |280 / 7 / 7|
| WAV / MP3 |1058 / 42|
| DBC数据表 |154|
| XML / Lua |138 / 130|

## 独立实现及验证范围

`reconstruction/resource_spec/mpq.py`不调用原游戏或StormLib，可独立读取经典MPQ v0头、hash/block表、按名称定位和有界文件内容。当前7份原件的文件flags全部为`0x80000000`，均为原始存储，无文件压缩或加密。每个真实命名文件都与项目内固定的[官方StormLib v9.40](https://github.com/ladislav-zezula/StormLib/releases/tag/v9.40)逐字节对照。参考源码固定commit`6bb1882bd00ddbc3729cac5dac0fda81a61e5514`；源码包、提取源码和编译产物哈希均记录在本机工具收据，未全局安装。

另以该固定工具写入90份合成payload，覆盖原始/单块/扇区、zlib、bzip2、加密与FIX_KEY，含空文件、短尾和4096B边界。独立读取与参考读取均符合原payload，90例0差异，大小写两种名称各验一次；这是格式验证，**不是新增游戏资产或游戏逻辑差分**。文件名路径分隔符保留，应用层别名须另行恢复；未知压缩方法、patch文件和sector-CRC明确拒绝。

`resource_spec/dbc.py`已逐份读取154个WDBC容器，共171225行、28041880B，并在ignored证据中保存与重读核验。它提供精确行/字符串边界；只在每字段确为4B的容器开放word接口。`CharBaseInfo`为2字段/2B行，`CharStartOutfit`为41字段/152B行，保留packed原始行并拒绝猜列宽。尚未恢复全部列的游戏语义。

| 部分实际DBC | 行 / 声明字段 / 每行字节 |
|---|---|
| Map |44 / 42 / 168|
| AreaTable |1081 / 25 / 100|
| CreatureModelData |430 / 16 / 64|
| CreatureDisplayInfo |10534 / 12 / 48|
| Spell |22357 / 173 / 692|
| ChrRaces |9 / 29 / 116|

新版0.135.1的静态补充追踪从初始data段重新定位上述4类完整DBC路径，保留10处字面量与6个完整引用函数：Map的17862，CreatureModelData的970/19873，CreatureDisplayInfo的970/17955/19873，Spell的2709/4546。每条引用绑定真实`i32.const`、原body范围和哈希。这只是后续消费者入口，不声称全部调用者、列语义或运行时加载已追通。

## 复现与未完成项

```sh
python3 reverse-engineering/scripts/mpq_toolchain.py --bootstrap
python3 reverse-engineering/scripts/resource_index.py
python3 reverse-engineering/scripts/mpq_reader_check.py
python3 reverse-engineering/scripts/resource_index_verify.py --directory <本轮resource-index目录> --synthetic-directory <本轮mpq-reader-check目录>
python3 reverse-engineering/scripts/resource_index_consumers135.py
```

最终真实差分在`evidence/resource-index-base-20261101T032320.856364Z/`，独立SQLite索引14479360B，SHA`a3f219f6e76e1d87e50b0790b757f999091e2b479d3b1d40ac2c101aa8680cf4`；合成格式对照在`evidence/mpq-reader-check-20261101T032259.008799Z/`。只读验收重新核对29602个原始表项与所有154份DBC、90例合成输入/结果及源码冻结。没有重复执行参考库或原游戏。

初次DBC检查误设“所有字段4B”，以及合成检查中的路径分隔符假设、空压缩文件offset表假设，均修正并保留失败收据/源码；最终原件全量差分使用修正后的冻结源码重跑通过。原件、工具、索引、路径全表及DBC二进制仅存4T本机忽略区，Git只保存实现和摘要。未执行任何Lua、原生游戏或WASM应用入口，未修改安装包、存档或Android工作。

仍需恢复实际加载/路径别名/生命周期、DBC字段与玩法ID关联，以及M2动画、BLP材质、WMO/地形、特效和声音的完整解释与渲染。当前交付是资源索引与读取器，尚未形成可玩资源管线。
