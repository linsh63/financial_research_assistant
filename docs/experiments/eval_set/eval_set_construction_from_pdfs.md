# 从原始 PDF 构造金融 RAG 评测集

## 目标

第二周需要自建 80-120 条评测数据，每条数据至少包含：

- `query`：用户问题。
- `ground_truth_doc_id`：正确答案所在文档。
- `answer`：标准答案。

为了让后续 Recall@3、Recall@5、Recall@10 能稳定计算，建议额外记录页码、证据文本和问题类型。

## 推荐数据格式

使用 JSONL，每行一条：

```json
{
  "question_id": "fact_0001",
  "question_type": "fact",
  "query": "比亚迪 2026 年一季度归母净利润是多少？",
  "answer": "归母净利润为 91.55 亿元。",
  "ground_truth_doc_id": "BYD_202601",
  "source": "data/raw/new_energy/BYD_202601.pdf",
  "pages": [1],
  "evidence_text": "2026 年一季度，公司实现归母净利润 91.55 亿元...",
  "evidence_chunk_id": "",
  "evidence_bbox": [],
  "notes": "答案必须能从证据原文直接推出。"
}
```

字段说明：

| 字段 | 作用 |
|---|---|
| `question_id` | 稳定编号，方便复盘 badcase |
| `question_type` | `fact`、`compare`、`summary` 三类 |
| `query` | 检索系统输入 |
| `answer` | 人工确认的标准答案 |
| `ground_truth_doc_id` | 召回评测的核心标签 |
| `source` | 原始 PDF 路径 |
| `pages` | 答案所在页 |
| `evidence_text` | 可支撑答案的原文 |
| `evidence_chunk_id` | 如果已经切块，可补对应 chunk |
| `evidence_bbox` | 如果有版面坐标，可补 bbox 方便可视化 |

## 构造流程

### 1. 先确定抽样范围

从 `data/raw` 中选择覆盖多个行业的 PDF，不要只从一个文档里出题。

建议第一版比例：

| 类型 | 数量 | 来源 |
|---|---:|---|
| 事实型 | 50-70 | 单篇研报、年报、政策文件 |
| 对比型 | 20-30 | 两篇以上公司研报，或同一行业多家公司 |
| 汇总型 | 10-20 | 行业报告、政策文件、同一主题多文档 |

第一版可以先做 30 条小评测集，等召回链路跑顺后扩展到 80-120 条。

### 2. 从 PDF 中定位候选证据

先跑解析和切块，得到页面级和 chunk 级文件：

```bash
python scripts/parse_pdfs.py \
  --raw-dir data/raw \
  --output data/processed/pages/pages_deepdoc.jsonl

python scripts/build_chunks.py \
  --input data/processed/pages/pages_deepdoc.jsonl \
  --output data/processed/chunks/chunks_deepdoc.jsonl \
  --chunk-size 512 \
  --overlap 100
```

如果只想先用样例：

```bash
python scripts/visualize_chunks.py \
  --chunks data/processed/chunks/chunks_deepdoc_sample.jsonl \
  --output-dir data/processed/visualizations/chunks \
  --with-labels
```

查看带红框 PDF，确认证据是否被正确切到 chunk 中。对金融场景尤其要看：

- 数字所在行有没有被切断。
- 表格行有没有被拆散。
- 右侧栏、页眉页脚、免责声明是否混进正文。
- 同一问题的答案是否需要跨页或跨表格。

### 3. 事实型问题怎么写

事实型问题要求答案能在单个证据片段里直接找到。

适合抽取：

- 营收、净利润、毛利率、费用率。
- 同比、环比、销量、装机量。
- 政策发布时间、政策目标、适用范围。

写法示例：

```json
{
  "question_id": "fact_0001",
  "question_type": "fact",
  "query": "比亚迪 2026 年一季度营业收入是多少？",
  "answer": "营业收入为 XXX 亿元。",
  "ground_truth_doc_id": "BYD_202601",
  "source": "data/raw/new_energy/BYD_202601.pdf",
  "pages": [1],
  "evidence_text": "..."
}
```

检查标准：

- 问题中不要直接复制过长原文。
- 标准答案必须包含单位。
- 如果原文有多个口径，比如营业收入和归母净利润，问题要写清楚口径。

### 4. 对比型问题怎么写

对比型问题用于暴露纯向量召回的弱点，通常需要两个证据来源。

适合抽取：

- A 公司和 B 公司毛利率谁更高。
- 同一公司两个季度费用率变化。
- 两个政策文件对同一主题的要求差异。

建议格式扩展为：

```json
{
  "question_id": "compare_0001",
  "question_type": "compare",
  "query": "比亚迪和宁德时代 2026 年一季度归母净利润哪个更高？",
  "answer": "比亚迪更高 / 宁德时代更高，并列出两者数值。",
  "ground_truth_doc_id": ["BYD_202601", "宁德时代_202601"],
  "source": [
    "data/raw/new_energy/BYD_202601.pdf",
    "data/raw/new_energy/宁德时代_202601.pdf"
  ],
  "pages": {
    "BYD_202601": [1],
    "宁德时代_202601": [1]
  },
  "evidence_text": {
    "BYD_202601": "...",
    "宁德时代_202601": "..."
  }
}
```

检查标准：

- 两个证据都要能独立支撑各自数值。
- 标准答案不能只写“更高”，要写出比较依据。
- 如果单位不同，先统一单位再写答案。

### 5. 汇总型问题怎么写

汇总型问题用于测试系统能否从多个文档召回同主题证据。

适合抽取：

- 新能源行业近期政策变化。
- 半导体行业报告中共同提到的需求驱动。
- 消费行业多个公司的一季度经营特征。

建议每条汇总型问题至少绑定 2-4 个 `ground_truth_doc_id`。

标准答案不要追求很长，写成 3-5 个要点即可：

```json
{
  "question_id": "summary_0001",
  "question_type": "summary",
  "query": "近期新能源行业政策主要围绕哪些方向？",
  "answer": "主要围绕新能源消纳、电力市场建设、设备更新和绿色低碳转型等方向。",
  "ground_truth_doc_id": [
    "ndrc_2025_new_energy_consumption_guidance_qna",
    "ndrc_2024_new_power_system_action_plan"
  ],
  "source": [
    "data/raw/policy/ndrc_2025_new_energy_consumption_guidance_qna.pdf",
    "data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf"
  ],
  "pages": {},
  "evidence_text": {}
}
```

检查标准：

- 不要问开放常识题，答案必须来自语料库。
- 每个要点都要能找到对应证据。
- 如果问题需要行业外知识才能回答，先不要放进第一版评测集。

## 人工标注工作流

推荐按这个顺序做：

1. 打开原始 PDF 或可视化后的红框 PDF。
2. 找到包含数字、结论或政策要求的段落。
3. 复制证据原文到 `evidence_text`。
4. 写一个自然语言问题，不要完全照抄原文。
5. 写标准答案，保留关键数字和单位。
6. 填入 `ground_truth_doc_id`、`source`、`pages`。
7. 用检索系统跑一遍，检查 Top5 是否能召回证据 chunk。

## 质量检查清单

每条评测数据入库前检查：

- `query` 是否只有一个明确问题。
- `answer` 是否能被 `evidence_text` 直接支持。
- `ground_truth_doc_id` 是否和 chunk 中的 `doc_id` 一致。
- `pages` 是否准确。
- 数字是否保留单位、时间范围和口径。
- 对比题是否包含所有对比对象的证据。
- 汇总题是否绑定多个证据来源。

## 文件建议

第一版评测集可以放在：

```text
data/eval/financial_qa_dev.jsonl
```

同时保留一份标注说明：

```text
docs/experiments/eval_set/eval_set_construction_from_pdfs.md
```

后续跑评测时，Recall 的判断逻辑可以先用 `ground_truth_doc_id`，再升级到 `evidence_chunk_id`。第一版不要一开始就追求自动化标注，先保证 30 条高质量样本能稳定复现问题。
