# 官方 0.139.0 获取与真实构建身份

已把 Windows 三分片、解压后的原生 EXE、同一网页标识对应的三个 JS 和 WASM，保存到外接4T全新目录 `originals/official-release-20261102T011227.335145Z/`。未运行 EXE、WASM start 或游戏入口，未替换任何旧原件、安装包、存档或公共登记。

| 文件 | 字节 | SHA-256 |
|---|---:|---|
| Windows EXE | 150595584 | `0e8e314df4d78ab211b1bef5c48d78d713ed64260894af342f998d298d74d274` |
| 官方三片合并gzip | 50738517 | `9ac2ae0bb14b4ca17daabf670f03fe07ca3baf6d23d7c4400d5d96476cd10a73` |
| Web WASM | 92511151 | `71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299` |

EXE通过官方manifest的完整大小/SHA，以及gzip EOF CRC/ISIZE。网页stamp `f339dd20e0fe`，下载前后HTML与官方manifest完全一致。成功获取收据是 `release-acquisition-resumed.json`，SHA `35c0e6b106056c47d3826581941174917e970133a46646e49cda8a0296b6e332`。

实际构建号是九字节 `f79c5e2b4`，Windows与Web两端各自核对实际读取指令：原生RIP-relative LEA定位 `0x14650cdd0`，相邻stack字段1656/1664明确写入pointer和长度9；Web实际函数1488的完整原件body SHA `5654c88a63551ea8d2d0c7117c24dbb183a6d493310e16d18361643875f01af2`，读取build pointer1451616，长度9写入offset676，pointer写入offset672，version pointer1451625/长度7另有真实descriptor。不是从八位正则或相邻字符串推断。

Web指令核对仅复用另一作者已完成的唯一139全profile，只读seek一个品牌函数；未创建第二份全WAT/索引。身份收据 `evidence/branding0139-identity-20261102T012823.573890Z/identity.json`，SHA `2f579c55cd09a0db559cfa3aa7d75818ccb594bcf96eb072ff9d917600c49ceb`。

最初不请求HTTP压缩的WASM请求在60秒后仅收到11081063字节，失败partial和SHA `975c5b3d…` 的失败收据原样保留，不作为成功。随后标准 `curl --compressed` 协商gzip，12.41秒完整传输26200711网络字节，解码成92511151字节的WASM；没有使用部分失败数据拼接，也没有使用range请求。另一次128MiB前缀反汇编预算失败保留，最终只读复用完整profile索引后成功。

官方说明提及引擎更新及插件proc命中区分；本批只建立来源、完整字节与真实构建身份。0.135/0.138的差分通过项不会转记为0.139通过，139伤害、协议或整局兼容性仍需各自的新实验。本批新增原件行为case、原生case、完整主循环帧数均为0。
