# 真实非平坦世界的135运动停止

新增 `world_motion_stop135.py` 已通过56个fresh原件完整17119组件输入，声明范围0差异；异作者独立复核待完成。[机器收据](../evidence/world-motion-stop135-oracle-20261102T000919.144127Z/comparison.json) SHA256 `8a49cd52bcaaf2b8fbd803ab0476f1dce459e7c837a57ac6b4c16bb83a983e99`。旧4例pilot不累加。

- 使用真实after1089完整166,395,904B内存作为输入，SHA `23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf`，原worldRc26204808及allocator原样恢复。9块真实地形、secondary560×560，flat未启用。没有伪造world，也没有把absence置true。
- 完整17119依次调用17217/16340，按NPC424→辅助112→claim88和源顺序停止运动，2412共享wrapping序列，每条停止发完整221。165个新增包及精确payload/capacity、82,544B三域完整backing、145,152B Game不变式均匹配；仅新增packet-vector指针保留实际观察。
- 覆盖真实非平坦高度、tile边界、secondary缓存点、真正world miss、零时长claim、inactive/dead分支、重复GUID、前缀和队列增长。输出对应独立模型150次29631命中、15次miss保留插值Z；内部height函数次数没有插桩。
- 查询顺序为29631命中取Z；miss且primary存在时23181只替换Z，保留XY；再miss保留插值Z。实际snapshot的Rc56=-1，primary路径只有静态/接口依据，不计作新的实际primary producer覆盖。
- 完整world查询输入的2318个范围共5,950,608B，在每个原件case前后都保存digest并匹配原snapshot；既有prefix的payload与48B metadata逐字核对。
- 支持byte/None源记录：216个已知投影字节重核同批原件，3080个None仅由模型保持。这不是额外原件case。inactive分支不读取未知GUID/坐标，也不要求world；消费未知marker或active缺world会拒绝。
-17份源码/34条导入边冻结前后一致。878宿主导入全拒绝，实际0次；256MiB WASM、512MiB heap，56 fresh实例，PID/PGID96231退出0且双missing，5.679秒/60秒。原件body/callees只增私有导出，未改写。

接口：`stop_world_motion135(WorldMotionStopInput135(...), world)`，world为已有独立`WorldQueries135`。返回更新的三域记录、movement序号/队列元数据、仅新增的221包、停止GUID和高度来源观察。prefix、真实当前Game、AI/1073的剩余队列和fatal/history由调用方保留并组合。

这使非平坦stop消费者可接入后续整合；没有独立重造world、恢复externref VM、启动App或完成同状态AI→fatal终局。旧terminal/death/headless以及安装包、存档均未修改。
