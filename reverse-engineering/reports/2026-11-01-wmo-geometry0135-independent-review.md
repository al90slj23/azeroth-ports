# 0.135.1 WMO碰撞投影独立只读复核

[作者最终收据](../evidence/wmo-geometry0135-20261101T103753.433490Z/wmo-geometry135-comparison.json)通过限定域独审：425组、830次显式原1510/4464入口，新增原件案例0。[review](../evidence/wmo-geometry0135-independent-review-20261101T104559.989694Z/review.json) SHA `b1fa07cccbc87cd424bd48f810660705938a005806f47a3a923b8d352c8d4af9`。没有执行原件、浏览器或作者WMO模型。

从固定patch.MPQ重新读全部410文件；独立解密并核hash/block表、MPQ32B头、实际文件名hash、SQLite行与原始offset/payload SHA。23root、387group，987,600原顶点/3,168,786个u16索引；独立按flags过滤与首次出现次序重算459,261顶点/1,051,449个u32索引，所有受控追加亦逐字匹配。65,537顶点前缀与大于65,535的目的索引完整保留。

30,932,188B已知几何严格比较；14,196,304B未写allocator尾段单列未知，其中832,181B非零。完整160B原输出保留；独立范围是root标签/组数、group三组几何Vec与+152/+156字段，指针和其它字段仅作原始观察，未声称完整160B解析对象已恢复。

7源闭包、只读SQLite定点11函数WAT、函数签名/body、section7仅增两导出、expected分离、原hash真实0→1及878导入全拒绝/实际0均核对。峰值19,202,048B、32MiB上限；PID/PGID20841退出0且均缺失，无snapshot/Once注入。

root路径规划未算作9513/VFS差分。旧Windows MPQ身份不等于最新135全部资产等价；完整WMO、world/6730/1089与完整一局仍需后续验证。
