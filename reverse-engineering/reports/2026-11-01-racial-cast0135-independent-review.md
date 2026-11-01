# 0.135.1 六种族kind9数值分支独立只读复核

最终 [053609 receipt](../evidence/full0135-oracle-20261101T053609.059221Z/racial-cast135-comparison.json) 通过：720 cases（693成功、27游戏guard失败）。冻结生产模型从输入独立重放，预期全部吻合；既有完整922原件结果重新比较无差异。28源及执行包闭包、catalogue数据、artifact哈希和非export原件字节一致，当前无源码漂移。每组完整88B定义也与原件data段核对。

实际G1256的80B记录共57,600字节严格比较，922不更改其冷却。801条live记录中23,772字节严格比较，唯一允许未知的是465条新7/8/9记录的+16未写scratch word；旧记录无mask，type12的+12/+16明确从定义复制并严格比较，未作NaN放宽。465处本次实际都是0，但原分支没有写该word，不能将本次零值升级为通用规格。

确认8/9的30距离目标guard、ownerGUID0稳定移除、append后1512再1202；7按任意owner/expiry的同spell阻止重放，成功时更新shield但不立即1512；12按HP35%及active12 guard，保留expired同spell且不立即1512。busy488/context908低位只控制第三attempt ledger，三组ledger均读回比较。另5个纯模型负例确认pointer、clock、RNG及显式ledger一致性边界。

这里只证明六个固定kind9 racial数值/live-record分支，未覆盖war_stomp/escape_artist、1202 aura/display键及包metadata、真实1076冷却调度、来源获得与phase进入或整局游戏。审查没有运行原件或编辑作者源。完整证据与复算脚本见 [review.json](../evidence/racial-cast0135-independent-review-20261101T054128.724568Z/review.json)。
