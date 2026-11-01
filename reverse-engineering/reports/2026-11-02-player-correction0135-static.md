# G416玩家校正状态的生产与清除

本次是固定0.135.1 / `90898d5e3`的只读静态定点，**没有新增199原件差分，也没有修改headless或效果系统**。可重跑`python3 reverse-engineering/scripts/trace_player_correction135.py`；[原件窗口与body SHA证明](../evidence/player-correction135-static-20261101T232136.971209Z/proof.json) SHA `f24e914980a47a426801cb4922ead41952853606901ac36daf4dca3af2d12cf1`。

G416并非915空阶段的阻塞标记，而是2328和915共享的待确认玩家重定位状态：tag、XYZ420/424/428、旧动作序号432、Game时钟436。完整1560仅初始化tag0；未激活payload不能用0填充。

2328校正时递增G1644，发199，写真实新XYZ及旧序号/当前Game时钟，置416=1。后续移动的首个分支为：

```text
if G416 != 0:
    if distanceSquared(inputXY, G420/424) > 9
       and f32(GameNow - G436) < 3:
        return 0                    # 保持待确认状态和旧坐标
    G416 = 0                        # 然后继续地形、边界与卡位检查
```

这次清除不是无条件超时回调；只有实际收到后续移动才执行。继续检查仍可能再次校正并置416=1。Game时钟与消息时间戳G444不同，不能混用。恰好距离平方9、恰好3秒均走继续路径，已由38例2328批验证。

另一清除入口是968的opcode199。先消费packedGUID，再把紧随的u32小端值作为确认序号；默认本地分段未见GUID等值验证。其本地分段WAT9644..9661为：

```text
if G416 == 1 and u32(ackSequence) >= u32(G432):
    G416 = 0
17726(G)
```

它采用无符号`>=`，并非仅相等、也不是带环绕的序号比较。较老ACK保留tag；tag!=1亦不清。route1经2080切换玩家后使用同一判据，随后调用17726并切回。完整199的解析容错、跨玩家路由及ACK序号wrap仍需专门原件差分；当前33例968移动批排除了199，不应计作其动态验证。

915的全部直接416访问只有store，没有load或clear。延迟56B记录tag36的玩家重定位分支会发同类199，设置XYZ、旧序号、当前Game时钟和416=1；现独立effect_system135中也把它保存在六个player_action_words中。空队列915不因既有416非零而自行拒绝或清除。

因此，当前headless的`player_action_tag416 != 0` guard是独立实现的范围限制，不能解释为原件规则。未来接入校正路径有两种有依据的续接：保留实际motion owner中的完整payload跨越空915，或处理真实后续movement/199 ACK。任何改动都应新跑同一Game的连续链，不能靠清tag或将未知payload填0避开guard。
