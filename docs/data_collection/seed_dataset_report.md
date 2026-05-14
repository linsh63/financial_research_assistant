# Seed Dataset Report

本文件记录当前种子数据集。当前数据集来自用户手动下载，已从 `data/new/` 按行业归档到 `data/raw/`，暂不做 PDF 解析或代码处理。

## 当前结论

当前已经登记 66 份 PDF，覆盖新能源、半导体、消费三个行业和政策文件，合计 420 页。相比长年报，这批文件更适合作为第一阶段的小闭环数据，用来快速验证：

- PDF 文件发现
- manifest 登记
- 页面级解析
- 基础切块
- 来源文档和页码引用

## 数据概览

| 行业 | 文档数 | 当前样本 |
|---|---:|---|
| 新能源 / 汽车 | 10 | BYD、广汽集团、赛力斯、长安汽车、宁德时代、EJGF、GXGK、LJLN、XWD、YWLN |
| 半导体 | 10 | BFHC、GYFL、HGCY、HGXX、HWJ、LCXX、TJKJ、ZKSG、ZWGS、ZXGJ |
| 消费 | 10 | BLY、DPYL、GZMT、HTWY、HXSW、LZLJ、QDPJ、SXFJ、WLY、YLGF |
| 政策文件 | 36 | 设备更新、能源设备更新、消费新场景、新型电力系统、绿色低碳目录、数据中心绿色低碳、低空经济分类、新能源消纳、电力市场、人工智能、固废治理等 |

## 文件列表

| doc_id | 行业 | 页数 | 本地路径 |
|---|---|---:|---|
| `byd_202601` | 新能源 | 5 | `data/raw/new_energy/BYD_202601.pdf` |
| `gac_group_202601` | 新能源 | 3 | `data/raw/new_energy/广汽集团_202601.pdf` |
| `seres_202601` | 新能源 | 3 | `data/raw/new_energy/赛力斯_202601.pdf` |
| `changan_auto_202601` | 新能源 | 3 | `data/raw/new_energy/长安汽车_202601.pdf` |
| `ejgf` | 新能源 | 3 | `data/raw/new_energy/EJGF.pdf` |
| `gxgk` | 新能源 | 6 | `data/raw/new_energy/GXGK.pdf` |
| `ljln` | 新能源 | 3 | `data/raw/new_energy/LJLN.pdf` |
| `xwd` | 新能源 | 3 | `data/raw/new_energy/XWD.pdf` |
| `ywln_202601` | 新能源 | 4 | `data/raw/new_energy/YWLN_202601.pdf` |
| `catl_202601` | 新能源 | 3 | `data/raw/new_energy/宁德时代_202601.pdf` |
| `bfhc` | 半导体 | 6 | `data/raw/semiconductor/BFHC.pdf` |
| `gyfl` | 半导体 | 4 | `data/raw/semiconductor/GYFL.pdf` |
| `hgcy` | 半导体 | 7 | `data/raw/semiconductor/HGCY.pdf` |
| `hgxx` | 半导体 | 5 | `data/raw/semiconductor/HGXX.pdf` |
| `hwj` | 半导体 | 4 | `data/raw/semiconductor/HWJ.pdf` |
| `lcxx` | 半导体 | 4 | `data/raw/semiconductor/LCXX.pdf` |
| `tjkj` | 半导体 | 5 | `data/raw/semiconductor/TJKJ.pdf` |
| `zksg` | 半导体 | 5 | `data/raw/semiconductor/ZKSG.pdf` |
| `zwgs` | 半导体 | 6 | `data/raw/semiconductor/ZWGS.pdf` |
| `zxgj` | 半导体 | 5 | `data/raw/semiconductor/ZXGJ.pdf` |
| `bly` | 消费 | 3 | `data/raw/consumer/BLY.pdf` |
| `dpyl` | 消费 | 4 | `data/raw/consumer/DPYL.pdf` |
| `gzmt` | 消费 | 5 | `data/raw/consumer/GZMT.pdf` |
| `htwy` | 消费 | 5 | `data/raw/consumer/HTWY.pdf` |
| `hxsw` | 消费 | 4 | `data/raw/consumer/HXSW.pdf` |
| `lzlj` | 消费 | 8 | `data/raw/consumer/LZLJ.pdf` |
| `qdpj` | 消费 | 3 | `data/raw/consumer/QDPJ.pdf` |
| `sxfj` | 消费 | 7 | `data/raw/consumer/SXFJ.pdf` |
| `wly` | 消费 | 3 | `data/raw/consumer/WLY.pdf` |
| `ylgf` | 消费 | 5 | `data/raw/consumer/YLGF.pdf` |
| `ndrc_2024_equipment_update_consumer_trade_in` | 政策 | 7 | `data/raw/policy/ndrc_2024_equipment_update_consumer_trade_in.pdf` |
| `ndrc_2024_energy_equipment_update_plan` | 政策 | 5 | `data/raw/policy/ndrc_2024_energy_equipment_update_plan.pdf` |
| `ndrc_2024_consumer_new_scenarios` | 政策 | 9 | `data/raw/policy/ndrc_2024_consumer_new_scenarios.pdf` |
| `ndrc_2024_new_power_system_action_plan` | 政策 | 8 | `data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf` |
| `ndrc_2024_green_low_carbon_industry_catalog` | 政策 | 14 | `data/raw/policy/ndrc_2024_green_low_carbon_industry_catalog.pdf` |
| `ndrc_2024_green_low_carbon_data_center_action_plan` | 政策 | 7 | `data/raw/policy/ndrc_2024_green_low_carbon_data_center_action_plan.pdf` |
| `ndrc_2025_low_altitude_economy_classification` | 政策 | 12 | `data/raw/policy/ndrc_2025_low_altitude_economy_classification.pdf` |
| `ndrc_2025_new_energy_market_quotation_notice` | 政策 | 2 | `data/raw/policy/ndrc_2025_new_energy_market_quotation_notice.pdf` |
| `ndrc_2025_new_energy_consumption_guidance_qna` | 政策 | 2 | `data/raw/policy/ndrc_2025_new_energy_consumption_guidance_qna.pdf` |
| `ndrc_ai_high_quality_employment_article` | 政策 | 2 | `data/raw/policy/ndrc_ai_high_quality_employment_article.pdf` |
| `ndrc_changzhutan_green_transition_interpretation` | 政策 | 2 | `data/raw/policy/ndrc_changzhutan_green_transition_interpretation.pdf` |
| `ndrc_ai_manufacturing_power_article` | 政策 | 2 | `data/raw/policy/ndrc_ai_manufacturing_power_article.pdf` |
| `ndrc_generation_capacity_price_qna` | 政策 | 2 | `data/raw/policy/ndrc_generation_capacity_price_qna.pdf` |
| `ndrc_unified_power_market_interview` | 政策 | 2 | `data/raw/policy/ndrc_unified_power_market_interview.pdf` |
| `ndrc_2026_generation_capacity_price_notice` | 政策 | 2 | `data/raw/policy/ndrc_2026_generation_capacity_price_notice.pdf` |
| `ndrc_ai_international_cooperation_article` | 政策 | 2 | `data/raw/policy/ndrc_ai_international_cooperation_article.pdf` |
| `ndrc_2024_distribution_grid_high_quality_development` | 政策 | 3 | `data/raw/policy/ndrc_2024_distribution_grid_high_quality_development.pdf` |
| `ndrc_solid_waste_governance_interpretation` | 政策 | 2 | `data/raw/policy/ndrc_solid_waste_governance_interpretation.pdf` |
| `policy_202210114475091` | 政策 | 9 | `data/raw/policy/202210114475091.pdf` |
| `policy_p020201029597065666501` | 政策 | 5 | `data/raw/policy/P020201029597065666501.pdf` |
| `policy_p020210325504120315428` | 政策 | 11 | `data/raw/policy/P020210325504120315428.pdf` |
| `policy_p020210421528000000606` | 政策 | 8 | `data/raw/policy/P020210421528000000606.pdf` |
| `policy_p020210421528000346108` | 政策 | 5 | `data/raw/policy/P020210421528000346108.pdf` |
| `policy_p020220121303052384813` | 政策 | 15 | `data/raw/policy/P020220121303052384813.pdf` |
| `policy_p020220321550104020921` | 政策 | 18 | `data/raw/policy/P020220321550104020921.pdf` |
| `policy_p020220602315650388122` | 政策 | 46 | `data/raw/policy/P020220602315650388122.pdf` |
| `policy_p020230721357059106134` | 政策 | 4 | `data/raw/policy/P020230721357059106134.pdf` |
| `policy_p020230721360399538898` | 政策 | 3 | `data/raw/policy/P020230721360399538898.pdf` |
| `policy_p020240624569333510920` | 政策 | 9 | `data/raw/policy/P020240624569333510920.pdf` |
| `policy_p020240726413585348997` | 政策 | 7 | `data/raw/policy/P020240726413585348997.pdf` |
| `policy_p020240806534738672970` | 政策 | 8 | `data/raw/policy/P020240806534738672970.pdf` |
| `policy_p020240821593575195639` | 政策 | 5 | `data/raw/policy/P020240821593575195639.pdf` |
| `policy_p020250106570227369979` | 政策 | 12 | `data/raw/policy/P020250106570227369979.pdf` |
| `policy_p020250912338143145278` | 政策 | 7 | `data/raw/policy/P020250912338143145278.pdf` |
| `policy_w020190905514280441190` | 政策 | 6 | `data/raw/policy/W020190905514280441190.pdf` |
| `policy_w020190906340655425738` | 政策 | 12 | `data/raw/policy/W020190906340655425738.pdf` |

## 后续扩充建议

- 当前三大目标行业已经各有 10 份短 PDF，并补充了 36 份政策/解读文件，可以先进入解析、切块、检索小闭环。
- 后续如需扩充，优先补充每个行业的长研报或年报，增加表格、多栏和长文档复杂度。
- 等解析、切块、检索流程稳定后，再逐步加入长年报和研报。
- 每新增一份 PDF，同步更新 `docs/data_collection/pdf_manifest.csv`。

## 质量检查命令

```bash
find data/raw -name "*.pdf" | wc -l
find data/raw -name "*.pdf" -size -50k -print
file data/raw/**/*.pdf
```

当前检查结果：

- PDF 数量：66
- 小于 50KB 的疑似异常文件：0
- 文件类型：均为 PDF
