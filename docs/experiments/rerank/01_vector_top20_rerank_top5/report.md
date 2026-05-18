# 重排实验：向量前 20 重排前 5 对比

- 评测时间： 2026-05-18T12:07:09
- 评测集： `data/eval/financial_qa_dev.jsonl`
- 索引目录： `data/processed/indexes/bge_large_zh_v15`
- 索引类型：精确向量索引（`flat`）
- 匹配粒度：页码级
- 完成样本： 120 / 120
- 跳过样本： 0
- 总耗时（秒）： 308.64
- 重排模型： `models/bge-reranker-v2-m3`
- 重排后端：本地 `transformers` 加载
- 候选召回数量： 20
- 直接召回数量： 5
- 重排后保留数量： 5
- 分数阈值： 未启用
- 相对分差阈值： 未启用

## 实验设置

- 本实验参考 QAnything 的两阶段检索思路：先用向量表示做第一阶段粗召回，再用交叉编码重排模型对候选切块精排。
- QAnything 还实现了重排的绝对分数阈值和相对分差阈值；本次为了严格对比“直接前 5”和“前 20 + 重排前 5”，没有启用阈值过滤。
- `FlagEmbedding` 后端在当前本机环境下与 `XLMRobertaTokenizer` 存在兼容问题，因此实际运行使用 `transformers` 后端加载同一个本地 `bge-reranker-v2-m3` 模型。
- 本次耗时 308.64s，主要成本来自 120 个问题 × 20 个候选切块的交叉编码打分。

## 总体结果

| scheme | Recall@5 | HitAny@5 | HitAll@5 |
|---|---:|---:|---:|
| vector_top5 | 78.25% | 88.33% | 69.17% |
| vector_top20_rerank_top5 | 82.29% | 90.00% | 74.17% |

结论：`前 20 + 重排前 5` 相比直接向量 `前 5`，召回覆盖率@5 提升 4.04 个百分点，完整命中证据@5 提升 5.00 个百分点。重排对对比型和汇总型的覆盖提升更明显，但也带来 5 个完整命中证据退化样本，后续需要结合阈值过滤、邻页扩展或混合召回候选进一步调参。

## 按问题类型统计

### 向量直接前 5

| question_type | count | Recall@5 | HitAny@5 | HitAll@5 |
|---|---:|---:|---:|---:|
| compare | 30 | 76.67% | 96.67% | 56.67% |
| fact | 70 | 82.86% | 82.86% | 82.86% |
| summary | 20 | 64.50% | 95.00% | 40.00% |

### 向量前 20 + 重排前 5

| question_type | count | Recall@5 | HitAny@5 | HitAll@5 |
|---|---:|---:|---:|---:|
| compare | 30 | 81.67% | 93.33% | 70.00% |
| fact | 70 | 85.71% | 85.71% | 85.71% |
| summary | 20 | 71.25% | 100.00% | 40.00% |

## 变化样本

- 完整命中修复数： 11
- 完整命中退化数： 5

### 重排后修复的样本

- `事实型_049`
- `事实型_053`
- `事实型_054`
- `事实型_056`
- `对比型_006`
- `对比型_010`
- `对比型_011`
- `对比型_012`
- `对比型_025`
- `对比型_027`
- `汇总型_013`

### 重排后退化的样本

- `事实型_005`
- `事实型_006`
- `对比型_002`
- `对比型_020`
- `汇总型_008`

## 未完全命中的样本

### 向量直接前 5 

- `事实型_004` 事实型，证据覆盖=0/1
  问题：国轩高科 2024A 的 PB 估值是多少倍
  召回来源：['data/raw/new_energy/GXGK.pdf', 'data/raw/consumer/WLY.pdf', 'data/raw/new_energy/长安汽车_202601.pdf', 'data/raw/real_estate/XCKG.pdf']
- `事实型_008` 事实型，证据覆盖=0/1
  问题：麦加芯彩 2026E 归母净利润预计是多少
  召回来源：['data/raw/new_energy/MJXC.pdf', 'data/raw/semiconductor/HWJ.pdf', 'data/raw/consumer/DPYL.pdf', 'data/raw/semiconductor/LCXX.pdf']
- `事实型_013` 事实型，证据覆盖=0/1
  问题：安琪酵母2025A净利润为多少
  召回来源：['data/raw/consumer/AQJM.pdf', 'data/raw/healthcare/SYXY.pdf']
- `事实型_035` 事实型，证据覆盖=0/1
  问题：华发股份2025年营业收入同比增长多少
  召回来源：['data/raw/real_estate/HFGF.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/healthcare/SYXY.pdf']
- `事实型_036` 事实型，证据覆盖=0/1
  问题：截至 2025 年末，金地集团有息负债多少
  召回来源：['data/raw/real_estate/JDJT.pdf']
- `事实型_045` 事实型，证据覆盖=0/1
  问题：飞荣达公司2025主营收入为多少
  召回来源：['data/raw/new_energy/LXDQ.pdf', 'data/raw/semiconductor/FRD.pdf', 'data/raw/healthcare/SYXY.pdf', 'data/raw/healthcare/YMKD.pdf']
- `事实型_047` 事实型，证据覆盖=0/1
  问题：2025 年，海达尔公司研发费用为多少
  召回来源：['data/raw/real_estate/ZJGF.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/semiconductor/HYKG.pdf', 'data/raw/healthcare/KLY.pdf']
- `事实型_049` 事实型，证据覆盖=0/1
  问题：海光信息公司2024A销售毛利率为多少
  召回来源：['data/raw/healthcare/SYXY.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/consumer/QHWY.pdf', 'data/raw/healthcare/HXYK.pdf']
- `事实型_050` 事实型，证据覆盖=0/1
  问题：寒武纪-U公司2023A营业收入为多少
  召回来源：['data/raw/semiconductor/HWJ.pdf', 'data/raw/consumer/QHWY.pdf', 'data/raw/real_estate/HFGF.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/consumer/JZSP.pdf']
- `事实型_053` 事实型，证据覆盖=0/1
  问题：2025年全国⾼校毕业⽣人数再创历史新⾼，达到了多少
  召回来源：['data/raw/new_energy/LXDQ.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/semiconductor/HYKG.pdf', 'data/raw/real_estate/JDJT.pdf']
- `事实型_054` 事实型，证据覆盖=0/1
  问题：2024年我国全部⼯业增加值为多少
  召回来源：['data/raw/real_estate/HFGF.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/policy/ndrc_2024_distribution_grid_high_quality_development.pdf', 'data/raw/real_estate/JDJT.pdf']
- `事实型_056` 事实型，证据覆盖=0/1
  问题：2018年1—11月，基础设施业新增意向投资额同比下降多少
  召回来源：['data/raw/policy/P020191031776387313331.pdf']
- `对比型_003` 对比型，证据覆盖=1/2
  问题：千禾味业 vs 神农集团，哪家公司的26Q1营收 更高
  召回来源：['data/raw/consumer/QHWY.pdf', 'data/raw/consumer/HTWY.pdf', 'data/raw/consumer/JZSP.pdf']
- `对比型_006` 对比型，证据覆盖=1/2
  问题：凯莱英 vs 美年健康，哪家公司2025年的归母净利润更高
  召回来源：['data/raw/healthcare/KLY.pdf', 'data/raw/healthcare/SYXY.pdf', 'data/raw/healthcare/TGYY.pdf']
- `对比型_007` 对比型，证据覆盖=1/2
  问题：普蕊斯 vs 普瑞眼科，预计哪家公司在2026年的营收更高
  召回来源：['data/raw/healthcare/PRYK.pdf', 'data/raw/healthcare/AEYK.pdf', 'data/raw/healthcare/HXYK.pdf']
- `对比型_008` 对比型，证据覆盖=0/2
  问题：昭衍新药 vs 通策医疗，预计哪家公司在2026年的营收更高
  召回来源：['data/raw/healthcare/SYXY.pdf', 'data/raw/healthcare/YKSW.pdf']
- `对比型_010` 对比型，证据覆盖=1/2
  问题：药康生物 vs 药明康德，哪家公司2025年的全年营业收入同比增长更多
  召回来源：['data/raw/healthcare/YMKD.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/healthcare/TGYY.pdf', 'data/raw/healthcare/SYXY.pdf']
- `对比型_011` 对比型，证据覆盖=1/2
  问题：威贸电子 vs 欣旺达，哪家公司2025 年营收更高
  召回来源：['data/raw/new_energy/WMDZ.pdf', 'data/raw/healthcare/SYXY.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/new_energy/XWD.pdf', 'data/raw/healthcare/YMKD.pdf']
- `对比型_012` 对比型，证据覆盖=1/2
  问题：亿纬锂能 vs 中国核电，哪家公司2025年的全年营业收入同比增长更多
  召回来源：['data/raw/new_energy/XWD.pdf', 'data/raw/new_energy/ZGHD.pdf']
- `对比型_013` 对比型，证据覆盖=1/2
  问题：中集集团 vs 中自科技，预计哪家公司2026年营业收入更高
  召回来源：['data/raw/new_energy/ZZKJ.pdf', 'data/raw/new_energy/ZJJT.pdf']

### 向量前 20 + 重排前 5 

- `事实型_004` 事实型，证据覆盖=0/1
  问题：国轩高科 2024A 的 PB 估值是多少倍
  召回来源：['data/raw/semiconductor/HGXX.pdf', 'data/raw/new_energy/XWD.pdf', 'data/raw/healthcare/HYYY.pdf', 'data/raw/real_estate/XCKG.pdf', 'data/raw/real_estate/BLFZ.pdf']
- `事实型_005` 事实型，证据覆盖=0/1
  问题：隆基绿能 26Q1 费用率同比提升了多少？
  召回来源：['data/raw/new_energy/ZZKJ.pdf', 'data/raw/semiconductor/HYKG.pdf', 'data/raw/consumer/DPYL.pdf', 'data/raw/healthcare/AEYK.pdf']
- `事实型_006` 事实型，证据覆盖=0/1
  问题：朗信电气电子风扇及电机总成在 2025 年的产能是多少？
  召回来源：['data/raw/new_energy/LXDQ.pdf']
- `事实型_008` 事实型，证据覆盖=0/1
  问题：麦加芯彩 2026E 归母净利润预计是多少
  召回来源：['data/raw/healthcare/BAST.pdf', 'data/raw/semiconductor/HWJ.pdf', 'data/raw/semiconductor/LCXX.pdf', 'data/raw/consumer/YLGF.pdf', 'data/raw/new_energy/宁德时代_202601.pdf']
- `事实型_013` 事实型，证据覆盖=0/1
  问题：安琪酵母2025A净利润为多少
  召回来源：['data/raw/consumer/AQJM.pdf', 'data/raw/real_estate/XCKG.pdf', 'data/raw/real_estate/SZGX.pdf', 'data/raw/real_estate/CJFZ.pdf']
- `事实型_035` 事实型，证据覆盖=0/1
  问题：华发股份2025年营业收入同比增长多少
  召回来源：['data/raw/real_estate/HFGF.pdf', 'data/raw/healthcare/JYYX.pdf', 'data/raw/healthcare/JZYY.pdf', 'data/raw/real_estate/ZGGM.pdf', 'data/raw/new_energy/LXDQ.pdf']
- `事实型_036` 事实型，证据覆盖=0/1
  问题：截至 2025 年末，金地集团有息负债多少
  召回来源：['data/raw/real_estate/JDJT.pdf', 'data/raw/real_estate/BJJT.pdf', 'data/raw/real_estate/ZGGM.pdf']
- `事实型_045` 事实型，证据覆盖=0/1
  问题：飞荣达公司2025主营收入为多少
  召回来源：['data/raw/semiconductor/FRD.pdf', 'data/raw/healthcare/SYXY.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/semiconductor/ZXGJ.pdf', 'data/raw/real_estate/ZGGM.pdf']
- `事实型_047` 事实型，证据覆盖=0/1
  问题：2025 年，海达尔公司研发费用为多少
  召回来源：['data/raw/semiconductor/DLGF.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/semiconductor/HYKG.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/healthcare/SYXY.pdf']
- `事实型_050` 事实型，证据覆盖=0/1
  问题：寒武纪-U公司2023A营业收入为多少
  召回来源：['data/raw/semiconductor/HWJ.pdf', 'data/raw/healthcare/BTGF.pdf', 'data/raw/healthcare/TGYY.pdf']
- `对比型_002` 对比型，证据覆盖=1/2
  问题：泸州老窖 vs 五粮液，哪家公司的2025年营业总收入更高？
  召回来源：['data/raw/consumer/SXFJ.pdf', 'data/raw/consumer/LZLJ.pdf']
- `对比型_003` 对比型，证据覆盖=1/2
  问题：千禾味业 vs 神农集团，哪家公司的26Q1营收 更高
  召回来源：['data/raw/consumer/QHWY.pdf', 'data/raw/consumer/AQJM.pdf', 'data/raw/consumer/HTWY.pdf']
- `对比型_007` 对比型，证据覆盖=0/2
  问题：普蕊斯 vs 普瑞眼科，预计哪家公司在2026年的营收更高
  召回来源：['data/raw/healthcare/PRYK.pdf', 'data/raw/healthcare/AEYK.pdf']
- `对比型_008` 对比型，证据覆盖=0/2
  问题：昭衍新药 vs 通策医疗，预计哪家公司在2026年的营收更高
  召回来源：['data/raw/healthcare/YKSW.pdf', 'data/raw/healthcare/SYXY.pdf']
- `对比型_013` 对比型，证据覆盖=1/2
  问题：中集集团 vs 中自科技，预计哪家公司2026年营业收入更高
  召回来源：['data/raw/new_energy/ZJJT.pdf', 'data/raw/new_energy/ZZKJ.pdf']
- `对比型_014` 对比型，证据覆盖=1/2
  问题：宁德时代 vs 广汽集团，哪家公司2026年Q1实现营收更高
  召回来源：['data/raw/new_energy/长安汽车_202601.pdf', 'data/raw/new_energy/广汽集团_202601.pdf', 'data/raw/new_energy/BYD_202601.pdf']
- `对比型_019` 对比型，证据覆盖=1/2
  问题：珠江股份 vs 中新集团，哪家公司2024年实现营收更高
  召回来源：['data/raw/real_estate/ZXJT.pdf', 'data/raw/real_estate/ZJGF.pdf', 'data/raw/semiconductor/ZXGJ.pdf', 'data/raw/healthcare/BTGF.pdf', 'data/raw/new_energy/SGHN.pdf']
- `对比型_020` 对比型，证据覆盖=1/2
  问题：招商积余2025年的营业收入和招商蛇口2026年一季度的营业收入相比，哪个更高
  召回来源：['data/raw/real_estate/ZSSK.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/real_estate/ZSJY.pdf', 'data/raw/new_energy/SGHN.pdf']
- `对比型_021` 对比型，证据覆盖=1/2
  问题：华源控股 vs 海光信息，哪家公司2026年Q1实现营收更高
  召回来源：['data/raw/semiconductor/HGXX.pdf', 'data/raw/semiconductor/HYKG.pdf']
- `汇总型_001` 汇总型，证据覆盖=2/4
  问题：结合相关政策，新能源消纳与新型电力系统建设主要从哪些方向推进？
  召回来源：['data/raw/policy/ndrc_2024_distribution_grid_high_quality_development.pdf', 'data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/ndrc_2025_new_energy_consumption_guidance_qna.pdf', 'data/raw/policy/P020250106570227369979.pdf']
