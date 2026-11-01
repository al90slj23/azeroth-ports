# 本地transport六原入口独立复核

限定域独审通过：[最终43例／220次完整六入口](../evidence/transport0135-20261101T114315.811874Z/transport135-comparison.json)、10份当前／冻结源码及所有输入输出SHA一致。[独审收据](../evidence/transport0135-independent-review-20261101T115033.938265Z/review.json) SHA `b5de2b063d326bfb99593a57235a2959ea66e3b78980556e21de82e12c54c4c9`。没有导入作者模型或执行原件。

独立重算每条operation、ring容量／head／count与全slot保留、poll整232B向量移动、snapshot与88／12B行替换，expected与原件输出一致。55793增长分支实际计数为`{'empty_growth': 2, 'contiguous_growth': 10, 'move_tail': 21, 'copy_prefix': 2}`，最终新增两例覆盖先前缺失的copy-prefix。88B记录每个required／optional所有权头、UTF8与word84及原raw backing另核；源不变／深clone不alias与无关cell字节保护在冻结runner中逐调用执行。未把未写tail或未知slot推成零，也未宣称allocator内部状态等价。

旧pilot与三次41例full均保留。首full的任意命令tag、第二full的非UTF8行输入均不冒称最终typed域；第三full41是合法typed域但缺copy-prefix。最终43仅插入两个case，旧41个input逐项保持，生产模型／原件module未变，旧计数不相加。

这是quiet flags20/21=0／timer8=-1的typed76B cell验证。host0、32MiB、未改callee及真实allocator路径保留；clock／logging、完整App4253、880与真实联网同步未验。本次新增原件调用／主循环帧0。
