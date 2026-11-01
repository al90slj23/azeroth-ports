# 固定0.135.1：真实进场观察独立复核

[只读复核器](../scripts/review_entry_world135_probe.py)对[原件观察](2026-11-01-entry-world0135-probe.md)完成独立验证，未运行原件或浏览器、未修改作者源码。[最终复核](../evidence/entry-world0135-independent-review-20261101T093740.230091Z/review.json) SHA `0675b4c87874e00e622a899af3c06b164a180cadb70a83f3d95815ee70628f8f`；[机器报告](2026-11-01-entry-world0135-probe-independent-review.json)列明范围和限制。

完整原件只有export7增加2902、6959、6730、1089四个研究入口；全部非export字节、原export、签名和函数body核对一致。官方glue保持完整原前缀，只追加绑定导出。9份冻结源码与快照/原件收据前后SHA一致。

561次实际data GET均200；453个真实MPQ文件、83,632,785B全部重新从归档解出，逐一核对表、块、历史StormLib参考SHA、落盘资产和HTTP实际响应。包括1WDT、9ADT、31M2、410WMO、2DBC；不推定不同字节的归档优先级，也不把基础资产身份扩称新版全量资产完备。四份整内存319,029,248B均重新核对SHA，并从二进制独立读出App/G、相同world Rc26204808、strong2/weak1、非平地标志及原始网格域。

真实6730后phase0、NPC0/pickup0；同一G/world经完整1089后phase1、NPC4/pickup2。四个真实NPC的definition284均为5415572；两个原始56B拾取物kind2、数量依次2/1、visual9005。没有将这些观察反填成独立世界模型的预期。

本环境为24允许/854拒绝的独立真实资源与Storage只读宿主，实际3396调用/16名字；唯一存档读取位于新回环origin，`rogue.characters`确实无记录，写入入口不允许。256MiB页上限负例确实触发，峰值166,395,904B；外部请求、用户profile和存档访问均无。Node、Chromium、资产worker均已终态并逐PID确认缺失。没有隐式WASM start，显式JS调用白名单与bind-only路径均核对；这不是穷举动态间接调用图的证明。

**通过的是原件受控观察及资源/状态来源复核，新增独立模型案例为0。** 菜单/profile和App熵仍是研究输入；独立world/真实进场实现、完整880、全部技能、渲染、存档与联机及完整一局仍未验收。首轮工具OOM和过小文件数限额的失败证据保留，不计作游戏原件成功。
