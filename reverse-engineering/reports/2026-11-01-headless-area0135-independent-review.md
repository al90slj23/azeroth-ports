# 0.135.1 同G范围技能闭环独立复核

[064308最终收据](../evidence/full0135-oracle-20261101T064308.759593Z/headless135-comparison.json) 在声明域内通过：8 seed、1,614帧、9,695个逐action阶段、11次自然升级选择。从64份冻结源码（57个core模块含package init）重生成固定“先第一个upgrade，否则第一张”policy的完整400-frame预算corpus，再独立回放每个action；六个阶段依次为2088玩家、1754命中、3757范围效果、921 AI、2862拾取、947生成。结果与原件保存输出全部相等。没有运行原件或修改作者源。

8个角色索引/签名/body SHA、原export保留及只新增这8个export、所有非export原件字节、全部source/artifact身份通过，当前无drift。9,695阶段各自从有序lossless u32 delta独立恢复128×424B NPC及128×88B area backing，再与完整纯模型bytes和双方SHA比较；累计检查526,167,040B NPC、109,204,480B area（包含每阶段重复检查的未用槽）。没有NPC/area mask；仅旧pickup arrival与声明的inactive live words共10,919次可为未写u32，其余整数/浮点字节严格。

实际集成触发6次area出生、34次due tick、4次到期、4次旧area槽复用、1次area死亡与151次slow状态写。逐阶段还独立核算共享G2408：122个NPC、6个area及71个pickup出生增加199；8份构造初始counter各10，终态counter合计279，死亡、生成后的counter与RNG持续一致。52次旧NPC槽复用保留416个非零未写字节，没有非零stale death-time U4复用。

覆盖边界必须分开：seed1只产生flamestrike（2120/effect0），唯一area死亡也来自该技能；seed6只产生blizzard（10/effect1），151次120/124写均是存活NPC，blizzard没有致死。4次area到期全删除最后active槽，非平凡survivor memmove计数0；复用area的19个未写字节也全为0。非零19B保留、多记录中间压缩及effect1致死抑制已在独立area组件批验证，不能算成本次8seed集成新证据。

终态为6个pending_selected_ability、2个frame_budget400。seed1和6分别在143、257帧自然选择，并在第二次选择后继续143帧原件比对到400；其下一纯模型步为pending_due_event，没有执行第401原件帧。seed3第一次105帧选择后继续152帧，到257帧第二次选择后停；其他5 seed第一次选择后停。所有unknown停点及全部8 seed保留，没有按已实现能力改policy或删seed。

真实1089/resource boot仍未完成；phase1是显式研究边界，两种128槽零存储也是受控预留。完整880/915调度、其他来源/技能效果、physical packet/ECS/rendering及未建模player keys仍未知。本批不能作为完整游戏重造完成证明。

[最终独审证据](../evidence/headless-area0135-independent-review-20261101T064609.019436Z/review.json) 保留当前reviewer源与旧reviewer完整源；旧源SHA57927bea…吻合旧062623审查记录，旧收据和快照未改。旧reviewer的当前hash已变化，不声称仍与历史hash相等。
