# External Datasets

本文档记录外部评测数据集的位置和用途。外部数据放在 `data/external/` 下，不提交到 GitHub。

## FinQA

- 来源：<https://github.com/czyssrs/FinQA.git>
- 本地路径：`data/external/FinQA`
- 用途：金融问答评测集参考，可用于构造或改写本项目的离线 QA 评测集。
- 当前大小：约 134 MB

主要文件：

```text
data/external/FinQA/dataset/train.json
data/external/FinQA/dataset/dev.json
data/external/FinQA/dataset/test.json
data/external/FinQA/dataset/private_test.json
```

重新下载：

```bash
git clone --depth 1 https://github.com/czyssrs/FinQA.git data/external/FinQA
```

注意：

- `data/external/*` 已在 `.gitignore` 中忽略。
- 不要把 FinQA 原始数据提交到本项目仓库。
- 后续可以从 FinQA 中抽样或参考问题形式，整理到 `data/processed/eval_qa.jsonl`。

## FinanceIQ

- 来源：<https://huggingface.co/datasets/Duxiaoman-DI/FinanceIQ>
- 本地路径：`data/external/FinanceIQ`
- 用途：中文金融选择题评测集参考，可用于补充本项目的金融领域 QA 评测问题。
- 当前大小：约 3.5 MB
- 许可证：CC BY-NC-SA 4.0

主要文件：

```text
data/external/FinanceIQ/data/dev/
data/external/FinanceIQ/data/test/
```

当前包含 20 个 CSV 文件，覆盖开发集和测试集。主题包括：

- 证券从业资格
- 基金从业资格
- 期货从业资格
- 银行从业资格
- 注册会计师（CPA）
- 税务师
- 经济师
- 理财规划师
- 精算师-金融数学
- 保险从业资格 CICE

CSV 字段示例：

```text
Question,A,B,C,D,Answer
```

重新下载：

```bash
git clone --depth 1 https://huggingface.co/datasets/Duxiaoman-DI/FinanceIQ data/external/FinanceIQ
```

注意：

- `data/external/*` 已在 `.gitignore` 中忽略。
- 不要把 FinanceIQ 原始数据提交到本项目仓库。
- FinanceIQ 是中文金融考试类选择题，更适合作为金融知识问答评测参考；和 PDF 研报 RAG 的引用页码评测不是同一类任务，后续使用时需要筛选或改写。
