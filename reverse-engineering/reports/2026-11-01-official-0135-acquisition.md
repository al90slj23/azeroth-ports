# 官方0.135.1固定快照取得与身份验收

2026-11-01实时查询[官方更新清单](https://wow.aethus.pl/exe/latest.json)，最新Windows发行已从此前研究快照0.134.0更新为 **0.135.1**。本轮保存官方Windows更新和当时同版Web核心，功能对齐目标应迁移到该固定发行；**取得原件不代表已完成新版逻辑迁移或验证**。

| 原件 | 固定身份 | 验收依据 |
| --- | --- | --- |
| Windows更新EXE | 0.135.1；147797504B；SHA `71e5f1767279db4bd428d1cd9c5d50d37759b72295386a69f9e3f6e70bc59249` | 三块gzip拼合，CRC/ISIZE通过；解压结果精确匹配官方大小与SHA；静态PE32+ x86-64。 |
| Web WASM | 0.135.1 / `0898d5e3`；90959080B；SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2` | 官方HTTPS保存；Aethus菜单branding静态字节；页面stamp `f31d0e03e3ac` 在下载前后相同。SHA为本地计算，未取得独立发布的官方WASM摘要。 |

官方0.135.1说明：修复0.135.0角色面板报错、无法显示本局数值的问题。该单版说明不能代替0.134.0→0.135.1完整改动清单，也不能据此推断只有UI变化。Windows原生短build尚未知，继续以完整官方SHA区分。

全部下载及原件位于4T外盘研究目录 `originals/official-acquisition-20261101T030310.926207Z/`。保存原始更新清单、各HTTP头与状态/最终URL、三块更新及其哈希、gzip流、EXE、页面和stamped启动JS/WASM；所有10个下载产物及解压EXE均重新读取并核对摘要。现有0.134.0/0.126.0原件、安装包与存档均保留。没有再次下载完整资源RAR。

可复现入口为 `python3 reverse-engineering/scripts/acquire_official_snapshot.py --stage all`，默认创建新ignored目录；每次HTTP请求上限60秒。通过 `--directory` 继续时，仅复用与记录大小/SHA一致的下载，并固定该目录中已保存的Windows清单。脚本不执行原生程序、不实例化WASM或调用应用start。

完整收据与源码哈希见[相邻JSON](2026-11-01-official-0135-acquisition.json)。下一步应重新建立新版profile/函数映射，复用0.134.0独立模型与输入语料，针对变化模块重新差分。现有0.134.0测试次数保持原版本归属，不移作0.135.1验收；仍未形成可独立完成一局的替代核心。
