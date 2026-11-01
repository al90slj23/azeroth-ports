# 0.135.1 opening entities独立只读复核

[最终27组/116调用收据](../evidence/world-snapshot0135-oracle-20261101T101743.010880Z/opening-entities135-comparison.json)通过限定域独审；[review](../evidence/opening-entities0135-independent-review-20261101T104031.518712Z/review.json) SHA `a489d812eaea8e68fed6c6bb41f730750335f35d3160efb91b33533ca1e897e6`。没有执行原件、浏览器或作者opening_entities模型，新增原件案例0。

独立重算1744的有效slot次序、counter/GUID、位置/速度、88B所有已写字节及旧padding；1821采用独立原始四字RNG位运算，验证GUID24位截取、counter回绕和有符号i64→u64适配，raw signed返回保留。完整169编码/解码、所有value mask和值（含零key）均重新构造。

严格记录8,415B，未写4,785B单独观察其中3,780非零；定义指针仅在新记录+16..19按显式映射规范化，完整raw88/prototype44/映射已核对。27组最终包共135个/15,990B，与116阶段累计重复观察262,209B分列，不混作新增包。

原件只增export7，完整函数body/签名、23源闭包、117,440,512B真实snapshot、输入/expected分离、878导入全拒绝/实际0、256MiB上限和正常返回栈1048576均核对。Node52920退出0且PID缺失。

共享binary32/trig和world_query高度依赖另有验证；本复算不重新证明其全部输入。窗口8B、special40、边界几何及banner仍不倒记到116调用；历史快照重放不计新差分。完整1089、worldproducer、880与独立一局仍未由本报告证明。
