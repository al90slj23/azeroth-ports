# latest137身份与固定136／135研究分工

2026-11-01T15:43:19Z重新核官方[Windows更新manifest](https://wow.aethus.pl/exe/latest.json)及[Web入口](https://wow.aethus.pl/)：latest已从0.136.0变为**0.137.0**。manifest前后相同，Web部署stamp前后均`c628fd68823e`；三个JS及完整WASM另档。新原件均在4T，未执行EXE或实例化137 WASM，未改安装包、存档或Git提交。

文档完成前于2026-11-01T15:55:17Z再次只读拉取小manifest和HTML，仍为同一137 native SHA与Web stamp，见[最终metadata recheck](../evidence/official-latest-final-check-20261101T155515.017487Z/check.json)（SHA256 `609d145476f39adaa61d59acfd545becbf27f6fbe408dc72e92f3617ce0f2d4e`）。完整原件的前后coherence与SHA证据仍使用上面的独立冻结采集，不混为此小刷新下载。

| 版本域 | 身份与已完成工作 | 动态验收 |
|---|---|---|
| latest0.137.0 | 实际9字节build `d171b8f9f`；Windows/Web完整采集和身份guard | 0；尚无全量静态profile |
| 固定0.136.0静态迁移 | 实际9字节build `fe24fb74c`；[175319函数全量profile、RO SQLite、12入口候选与引用审查](2026-11-01-wasm0136-profile.md) | 0；候选同形不是规则验收 |
| 固定0.135.1动态研究 | 实际9字节Web build `90898d5e3`，旧`0898d5e3`为历史截短alias；独立world/opening/combat/XP/选卡实验继续锁定135原件 | 各旧、新135收据按其范围记录，不转记136/137 |

137 Windows EXE147,844,608B，publisher SHA256为`aa6b254f905e2f7a4cbc7c2c8f11af822ec362e3d2b8e84cabd8c38893a10dc8`；三个更新分块拼接gzip，读至EOF核CRC/ISIZE，解压字节与官方大小/SHA完全相同。Web WASM90,941,108B，实际HTTPS下载SHA256为`20ec9a2b5182a72e13ca11668ff0aab17e9dc54a10b923b546708ab85e3fe1c8`；该WASM hash由本机计算，未冒称publisher另发digest。完整采集在`originals/official-acquisition-20261101T154517.001467Z/`，summary SHA256 `30f718efa5066e0b738e7b76e5248f06da7a83beab6f12852c58d76faa655e49`。

[137身份sidecar](../evidence/branding0137-identity-20261101T154758.086510Z/identity.json) SHA256 `f93884e6798bce704b4d565be88627bb2dd54259589fd531f7609d472b1251f3`：native RIP-relative LEA指向build首字节，紧随stack slice长度9；Web真实1468函数body也匹配明确pointer／len9 store指令字节。version `0.137.0`有独立ptr／len7 descriptor。因此build不是相邻文本的固定8位regex截取，也没有把136的`fe24fb74c`误用为137身份。

135／136的[独立pointer/length核验](../evidence/branding0136-identity-20261101T145343.493343Z/identity.json) SHA256 `be6c2874770470d160ca0d0cf0cb72c9be88f7be491be070c1a60d14b72190e5`继续成立。旧收据采用`0898d5e3`的字段保持原样；当前registry在显式alias说明下使用实际`90898d5e3`，并始终以完整WASM SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`绑定135实验，不改历史样本。

首次重检的目录名`official-latest136-recheck-20261101T154250.834931Z`保留“是否仍136”的原始比较过程。其manifest/stamp稳定，但与被冻结136 SHA不同，故末尾断言按预期失败；其中`actual_consumed_build`字段来自被冻结136参考sidecar，不是137 build。新增[discovery addendum](../evidence/official-latest136-recheck-20261101T154250.834931Z/latest137-discovery-addendum.json)和本报告明确这个解释，原下载/receipt不覆写。

137公告宣布增强萨满proc互相触发、武器附魔与三项链重做、两个新天赋；它只指引迁移排查，不能证明其他路径没变。136的旧12入口静态候选不转记137，135的[新120帧／1select组合](2026-11-01-opening-combat0135.md)也仍是固定135、预解析独立world／原件snapshot／外部clock的受控尾阶段验证，不是完整880、Windows或完整一局。

当前工作应分别推进：137建立自身静态profile、声明/函数候选与未来受控验收；136保留已完成静态迁移证据；135继续完成其动态组合并保留每批来源和边界。详见[机器可读状态](2026-11-01-latest-version-state.json)、[targets registry](../targets.json)与[版本策略](../VERSION_STRATEGY.md)。
