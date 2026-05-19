# Generation Evaluation

- evaluated_at: 2026-05-19T15:59:33
- eval_file: `data/eval/financial_qa_dev.jsonl`
- pred_file: `data/generated/eval_runs/summary_evidence_pack_deepseek_subset_answers.jsonl`
- match_level: `page`
- eval_samples: 20 / 120
- skipped_eval_rows: 0
- prediction_rows: 5

## Overall

| metric | value |
|---|---:|
| generated_rate | 25.00% |
| answer_rate | 25.00% |
| citation_rate | 25.00% |
| reference_recall | 11.92% |
| reference_hit_any | 25.00% |
| reference_hit_all | 0.00% |
| numeric_coverage | 26.79% |
| numeric_count | 8 |

## By Question Type

| question_type | count | answer_rate | citation_rate | reference_recall | reference_hit_all | numeric_coverage | numeric_count |
|---|---:|---:|---:|---:|---:|---:|---:|
| summary | 20 | 25.00% | 25.00% | 11.92% | 0.00% | 26.79% | 8 |

## Badcases

- `summary_001` summary reasons=reference_not_hit_all,number_miss
  query: 结合相关政策，新能源消纳与新型电力系统建设主要从哪些方向推进？
  expected: 主要方向包括：坚持清洁低碳、安全充裕、经济高效、供需协同、灵活智能的基本原则，2024—2027年重点开展9项专项行动，提升电网对清洁能源的接纳、配置、调控能力；健全煤电、抽水蓄能、新型储能等调节性资源容量电价机制，完善体现分时价值差异的零售市场价格机制；突破新能源高效发电利用、系统灵活调节、电网高效仿真和稳定运行控制、智能化调控等技术；通过调节能力建设优化，支撑2025—2027年年均新增2亿千瓦以上新能源合理消纳利用，全国新能源利用率不低于90%；推动新型储能到2027年基本实现规模化、市场化发展，全国装机规模达到1.8亿千瓦以上。
  answer: 根据提供的政策资料，新能源消纳与新型电力系统建设主要从以下方向推进： 1. **分类引导新能源开发与消纳**：将新能源开发消纳划分为5类，统筹“沙戈荒”新能源基地外送与就地消纳，优化水风光基地一体化开发消纳，推动海上风电规范有序开发消纳，科学高效推动省内集中式新能源 [资料1]。 2. **优化电网主网架与输电通道**：优化加强电网主网架，补齐结构短板，夯实电力系统稳定的物理基础；优选一批“沙戈荒”大基地和主要流域水风光一体化基地送出通...
  reference_coverage: 2/4
  missing_numbers: ['2024', '2027', '9', '2025', '90%', '1.8']
  judge: None
  sources: ['data/raw/policy/ndrc_2025_new_energy_consumption_guidance_qna.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf', 'data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/P020210421528000000606.pdf', 'data/raw/policy/P020240806534738672970.pdf']
- `summary_002` summary reasons=reference_not_hit_all,number_miss
  query: 新型储能政策对发展目标、应用场景、技术路线和市场机制是如何安排的？
  expected: 新型储能被定位为支撑新型电力系统的重要技术和基础装备。目标上，到2025年实现从商业化初期向规模化发展转变、装机规模达3000万千瓦以上，到2030年实现全面市场化发展；专项行动进一步提出到2027年基本实现规模化、市场化发展。应用场景上，鼓励电源侧、电网侧、用户侧多元发展，拓展“新能源+储能”、智能微电网、虚拟电厂等场景。技术上，坚持多元化路线，推动锂离子电池规模化应用，推动压缩空气、液流电池、钠离子电池、飞轮、氢储能、热储能等试点示范和商业化发展。市场机制上，推动储能作为独立主体参与电力市场、辅助服务市场，完善容量电价、分时电价和成本疏导机制，并健全标准体系、并网流程和安全监管。
  answer: 根据证据包，新型储能政策在发展目标、应用场景、技术路线和市场机制方面的安排如下： 1. **发展目标**： - 到2025年，新型储能由商业化初期步入规模化发展阶段，具备大规模商业化应用条件；装机规模达3000万千瓦以上 [资料1][资料5]。 - 到2030年，实现新型储能全面市场化发展 [资料5]。 - 新型储能技术创新能力显著提高，核心技术装备自主可控水平大幅提升，标准体系基本完善，产业体系日趋完备，市场环境和商业模式基本成熟 [...
  reference_coverage: 2/5
  missing_numbers: ['2027']
  judge: None
  sources: ['data/raw/policy/P020220321550104020921.pdf', 'data/raw/policy/P020240624569333510920.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/consumer/TCL.pdf', 'data/raw/policy/202210114475091.pdf']
- `summary_003` summary reasons=reference_not_hit_all,number_miss
  query: “十四五”可再生能源规划和氢能规划分别怎样服务能源绿色低碳转型？
  expected: 可再生能源规划提出，加快发展可再生能源、实施可再生能源替代行动，是推进能源革命和构建清洁低碳、安全高效能源体系的重大举措；到2025年，可再生能源消费总量达到10亿吨标准煤左右，年发电量达到3.3万亿千瓦时左右，全国可再生能源电力总量消纳责任权重达到33%左右，非水电消纳责任权重达到18%左右。规划还要求推动绿色直供电、可再生能源供暖、非电直接利用和高比例可再生能源应用示范，健全消纳责任权重和长效机制。氢能规划将氢能界定为来源丰富、绿色低碳、应用广泛的二次能源，要求构建清洁化、低碳化、低成本的多元制氢体系，开展可再生能源制氢示范，构建安全、稳定、高效的氢能供应网络，并形成“1+N”政策体系。
  answer: 根据证据包内容，“十四五”可再生能源规划和氢能规划分别从以下方面服务能源绿色低碳转型： **一、“十四五”可再生能源规划** - **目标锚定**：锚定碳达峰、碳中和与2035年远景目标，提出到2025年非化石能源消费占比目标，并展望2035年非化石能源消费占比达到25%左右、风电和太阳能发电总装机容量达到12亿千瓦以上，可再生能源加速替代化石能源，基本建成清洁低碳、安全高效的能源体系 [资料1]。 - **发展新阶段**：“十四五”时...
  reference_coverage: 1/3
  missing_numbers: ['10', '3.3', '18%']
  judge: None
  sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/P020220323314396580505.pdf', 'data/raw/policy/P020220321550104020921.pdf', 'data/raw/policy/P020210421528000346108.pdf']
- `summary_004` summary reasons=reference_not_hit_all,number_miss
  query: 电网建设、电力市场和容量电价政策如何支撑新能源消纳与系统可靠运行？
  expected: 配电网政策要求适度超前建设配电网，提升承载力，满足分布式新能源和电动汽车充电基础设施发展。全国统一电力市场提出到2030年基本建成全国统一电力市场体系，市场化交易电量占全社会用电量的70%左右，并推动跨省跨区和省内联合交易。容量机制方面，煤电、抽水蓄能、新型储能等支撑性、调节性资源在高比例新能源消纳和新型电力系统中发挥重要作用，政策通过可靠容量补偿、容量市场探索和发电侧容量电价机制，保障其收益、增强电力安全保供能力。新能源报价政策则要求规范集中报价、价格预警和数字化监管，防范市场力滥用，维护市场公平竞争。
  answer: 根据证据包内容，电网建设、电力市场和容量电价政策对新能源消纳与系统可靠运行的支撑作用如下： 1. **电网建设与新能源消纳**：通过推进黄河上游梯级电站大型储能试点项目（如龙羊峡-拉西瓦河段百万千瓦级梯级电站），探索新能源发电抽水与梯级储能电站、流域梯级水电站的联合运行，支撑青海省新能源消纳和外送 [资料4]。同时，“十四五”期间重点开工抽水蓄能项目，包括华北、东北等区域的多个电站，并推进中长期规划电站及中小型抽水蓄能示范，提升区域新能...
  reference_coverage: 2/5
  missing_numbers: ['70%']
  judge: None
  sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/ndrc_2026_generation_capacity_price_notice.pdf', 'data/raw/policy/ndrc_2025_new_energy_consumption_guidance_qna.pdf', 'data/raw/policy/ndrc_generation_capacity_price_qna.pdf']
- `summary_005` summary reasons=reference_not_hit_all,number_miss
  query: 大规模设备更新和消费品以旧换新政策主要支持哪些领域，资金和补贴如何安排？
  expected: 政策统筹安排3000亿元左右超长期特别国债资金，加力支持大规模设备更新和消费品以旧换新。设备更新方面，支持范围从工业、环境基础设施、交通运输、物流、教育、文旅、医疗、回收循环利用，扩大到能源电力、老旧电梯等领域设备更新以及重点行业节能降碳和安全改造，并降低申报门槛、支持中小企业设备更新。具体补贴包括老旧营运船舶报废更新、老旧营运货车报废更新、农业机械报废更新、新能源公交车及动力电池更新等。消费品方面，重点支持汽车报废更新和乘用车置换更新、家电产品和电动自行车以旧换新、旧房装修和厨卫局部改造、居家适老化改造、智能家居消费等，要求真金白银优惠直达消费者。能源设备更新另提出到2027年能源重点领域设备投资规模较2023年增长25%以上。
  answer: 根据证据包，大规模设备更新和消费品以旧换新政策主要支持以下领域，资金和补贴安排如下： 1. **支持领域**： - **能源重点领域**：推动火电设备更新和技术改造（包括煤电机组节能改造、供热改造和灵活性改造“三改联动”），以及输配电、风电、光伏、水电等领域设备更新和技术改造 [资料1]。 - **老旧船舶报废更新**：支持内河客船10年以上、货船15年以上以及沿海客船15年以上、货船20年以上船龄的老旧船舶报废更新 [资料5][资料6...
  reference_coverage: 3/4
  missing_numbers: ['2027', '2023', '25%']
  judge: None
  sources: ['data/raw/policy/ndrc_2024_energy_equipment_update_plan.pdf', 'data/raw/policy/ndrc_2024_equipment_update_consumer_trade_in.pdf', 'data/raw/real_estate/ZJGF.pdf', 'data/raw/policy/W020190905517087932598.pdf', 'data/raw/policy/P020240726413585348997.pdf']
- `summary_006` summary reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all
  query: 培育消费新场景和新型消费的政策重点有哪些？
  expected: 消费新场景政策要求围绕居民吃穿住用行等传统消费和服务消费，培育一批带动性广、显示度高的消费新场景，推广特色鲜明、市场引领突出的典型案例，推动消费新业态、新模式、新产品不断涌现。重点包括餐饮消费细分领域、文旅体育消费、购物消费多元融合、利用人工智能大模型、虚拟现实和数字人等技术拓展购物体验、健康消费、银发消费、育幼消费等。新型消费政策强调线上线下消费有机融合，培育壮大零售新业态，拓展“互联网+”医疗、教育、体育等服务产品，推动数字化、网络化、智能化消费发展。
  answer: 
  reference_coverage: 0/4
  missing_numbers: []
  judge: None
  sources: []
- `summary_007` summary reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all
  query: 绿色消费、汽车消费和电子产品消费政策分别提出了哪些重点措施？
  expected: 绿色消费政策要求促进绿色产品消费、扩大绿色低碳产品供给、完善绿色消费制度保障，围绕衣食住行用等领域推动消费方式绿色转型。汽车消费政策强调优化汽车限购管理、支持老旧汽车更新消费、加快培育二手车市场、加强新能源汽车配套设施建设、降低新能源汽车购置使用成本。电子产品消费政策提出加快推动电子产品升级换代，支持可穿戴设备、智能产品、虚拟现实设备等消费，完善电子产品回收体系，促进绿色智能电子产品消费。
  answer: 
  reference_coverage: 0/3
  missing_numbers: []
  judge: None
  sources: []
- `summary_008` summary reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all
  query: 早期扩内需促消费政策如何通过优化供给、提升服务和改善环境来形成强大国内市场？
  expected: 政策要求顺应居民消费升级大趋势，加快转型升级提升供给质量和水平，以高质量供给催生创造新的市场需求，促进形成强大国内市场。具体包括促进汽车消费、家电和电子产品消费、农村网购和乡村旅游消费、养老托育和家政服务供给、信息消费和超高清视频产品消费；同时提出“十大扩消费行动”，围绕城镇消费、农村消费、住房租赁、汽车消费、旅游休闲、文化体育、智慧家庭、分享经济等方向，增加高品质商品和服务供给，完善商贸物流、信息网络等基础设施，打通物流和信息障碍，加强消费市场信用体系建设。
  answer: 
  reference_coverage: 0/3
  missing_numbers: []
  judge: None
  sources: []
- `summary_009` summary reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all
  query: 绿色低碳转型产业指导目录覆盖了哪些主要产业方向？
  expected: 目录覆盖节能降碳产业、环境保护产业、资源循环利用产业、能源绿色低碳转型、生态保护修复和利用、基础设施绿色升级、绿色服务等方向。具体包括高效节能装备制造、温室气体控制、大气水土壤和固体废弃物治理、可再生能源和清洁能源相关领域、生态农林牧渔业、绿色数据中心建设和节能改造，以及绿色低碳项目咨询设计、合同能源管理、资源循环利用第三方服务、环境污染第三方治理、能耗和温室气体监测、绿色电力交易等。
  answer: 
  reference_coverage: 0/1
  missing_numbers: []
  judge: None
  sources: []
- `summary_010` summary reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 数据中心绿色低碳发展专项行动计划提出了哪些目标和重点任务？
  expected: 目标是到2025年底，全国数据中心布局更加合理，整体上架率不低于60%，平均电能利用效率降至1.5以下，可再生能源利用率年均增长10%；到2030年底，平均电能利用效率、单位算力能效和碳效达到国际先进水平。重点任务包括完善“东数西算”布局，推动小规模、低效率存量分散数据中心向集约化、高效率转变；严格新上项目能效水效要求，新建及改扩建大型和超大型数据中心电能利用效率降至1.25以内，国家枢纽节点项目不得高于1.2；推进存量项目节能降碳改造；推广液冷、蒸发冷却、热管、氟泵、人工智能节能、高效供配电和高效存储等技术装备；通过激励约束、项目清单、监督管理和宣传引导推动落实。
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['2025', '60%', '1.5', '10%', '2030', '1.25', '1.2']
  judge: None
  sources: []

## Metric Notes

- `answer_rate`：生成答案非空的比例。
- `citation_rate`：答案文本中显式出现 `[资料1]` 这类引用编号的比例。
- `reference_recall` / `reference_hit_all`：用生成文件保存的 `references` 对齐评测集 ground_truth 的 source/pages。
- `numeric_coverage`：标准答案中抽出的数字在生成答案中出现的比例，只在标准答案含数字的样本上统计。
- `LLM judge`：启用 `--llm-judge` 后，由模型比较问题、标准答案和生成答案，输出正确性、完整性和忠实度评分。
- 当前 judge 主要判断答案与 ground truth 的一致性；是否完全被原文支撑仍需结合引用覆盖和人工抽查。
