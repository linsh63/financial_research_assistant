# RAGFlow DeepDOC 与 RAG 链路学习笔记

这份笔记总结前面讨论过的内容，重点帮助你按顺序理解：

1. DeepDOC 的 `vision` 模块如何从页面图像中抽取 OCR、版面、表格结构。
2. `naive.py` 如何把解析结果变成 chunk。
3. RAGFlow 的混合召回、重排和评测代码在哪里。

## 一、整体链路

RAGFlow 的文档入库和检索可以粗略串成这条线：

```text
文件上传/解析任务
  -> rag/svr/task_executor.py
  -> rag/app/naive.py 或其他 chunker
  -> deepdoc/parser/pdf_parser.py
  -> deepdoc/vision/*
  -> rag/nlp/__init__.py 合并和 tokenize
  -> embedding + 写入检索引擎
  -> rag/nlp/search.py 混合召回和重排
  -> chat/search/retrieval API
  -> evaluation / benchmark
```

核心理解：

- `task_executor.py` 是任务入口，负责调度 chunk 构建、embedding、入库。
- `naive.py` 是一种 chunk 策略，整体是“先解析/粗拆，再合并成 chunk”。
- `deepdoc/vision` 主要服务 PDF 的视觉解析，负责 OCR、版面识别、表格结构识别。
- `rag/nlp/search.py` 是混合召回和重排主线。

## 二、涉及的主要代码文件

### 文档解析与切块

- `ragflow/rag/svr/task_executor.py`
  - 解析任务执行入口。
  - `build_chunks()` 根据 `parser_id` 选择具体 chunker。
  - 后续还负责 embedding 和写入 doc store。

- `ragflow/rag/app/naive.py`
  - naive chunk 策略入口。
  - 根据文件类型选择 parser。
  - PDF 分支根据 `layout_recognize` 选择 `DeepDOC`、`PlainText`、`MinerU`、`Docling` 等解析器。
  - 解析后得到 `sections` 和 `tables`。

- `ragflow/rag/nlp/__init__.py`
  - `naive_merge()`：把 `sections` 顺序合并成 chunk。
  - `tokenize_chunks()`：把文本 chunk 包装成可检索字段。
  - `tokenize_table()`：把表格/图片结果包装成可检索字段。

- `ragflow/deepdoc/parser/pdf_parser.py`
  - PDF 解析主流程。
  - 会调用 `deepdoc/vision` 中的 OCR、layout、table structure 组件。

### DeepDOC Vision

- `ragflow/deepdoc/vision/ocr.py`
  - OCR 主逻辑。
  - 包含文字检测、文字识别和 OCR 编排类。

- `ragflow/deepdoc/vision/layout_recognizer.py`
  - 版面识别。
  - 给 OCR 文本框匹配版面标签，例如 `title`、`text`、`table`、`figure`、`equation`。

- `ragflow/deepdoc/vision/table_structure_recognizer.py`
  - 表格结构识别。
  - 输入表格区域图片，输出行、列、表头、跨行跨列单元格等结构。

- `ragflow/deepdoc/vision/recognizer.py`
  - layout/table 这类检测模型的基础封装。
  - 提供预处理、推理、后处理、排序、重叠匹配等通用工具。

- `ragflow/deepdoc/vision/postprocess.py`
  - OCR 检测和识别的后处理。
  - 例如 DB 检测结果转文本框，CTC 识别结果转字符串。

- `ragflow/deepdoc/vision/operators.py`
  - 图像预处理算子。
  - 例如 resize、normalize、padding、CHW 转换。

- `ragflow/deepdoc/vision/seeit.py`
  - 可视化调试工具。
  - 用于把检测框画到图片上。

- `ragflow/deepdoc/vision/t_ocr.py`
  - OCR 测试/调试脚本。

- `ragflow/deepdoc/vision/t_recognizer.py`
  - layout/table recognizer 测试/调试脚本。

### 检索、融合、重排

- `ragflow/rag/nlp/search.py`
  - 混合召回和重排核心。
  - `Dealer.search()`：候选召回。
  - `Dealer.retrieval()`：对外检索入口。
  - `Dealer.rerank()`：本地 token/vector 混合重排。
  - `Dealer.rerank_by_model()`：外部 reranker 模型重排。

- `ragflow/api/apps/services/dataset_api_service.py`
  - 数据集检索测试入口。
  - 会准备 embedding/rerank/chat 模型，然后调用 `settings.retriever.retrieval()`。

### 评测与 benchmark

- `ragflow/api/db/services/evaluation_service.py`
  - 平台内置 RAG evaluation 服务。
  - 管理 evaluation dataset、test case、run、result。
  - 当前实现了基础 retrieval 指标：precision、recall、F1、hit rate、MRR。

- `ragflow/test/benchmark/`
  - HTTP benchmark 工具。
  - 更偏性能压测，例如 latency、p50、p90、p95。
  - 不等同于完整 RAG 质量评测。

## 三、DeepDOC Vision 核心逻辑

### 1. OCR：`ocr.py`

`ocr.py` 里有三个关键层次：

```text
TextDetector
  -> 找出图片中的文字区域

TextRecognizer
  -> 对裁剪出来的文字图片做识别

OCR
  -> 串起 detection、crop、recognition
```

#### `TextDetector`

职责：

- 输入一张页面图片。
- 经过预处理和检测模型。
- 输出文字框坐标。

输出通常是文本区域框，例如：

```python
[
    [[x0, y0], [x1, y1], [x2, y2], [x3, y3]],
    ...
]
```

#### `TextRecognizer`

职责：

- 输入若干个裁剪后的文字小图。
- 输出每个小图对应的文字和置信度。

可以理解为：

```text
文字图片 -> "公司名称" + score
```

里面出现的 VL、SRN、SAR、SVTR、ABINet 等，是不同 OCR 识别模型结构或预处理方式，不是 RAG 特有概念。

#### `OCR`

职责：

1. 调用 `TextDetector` 找文字框。
2. 按阅读顺序排序文本框。
3. 根据文本框裁剪图片。
4. 调用 `TextRecognizer` 识别文字。
5. 返回带坐标的 OCR 结果。

它是 PDF 视觉解析最前面的组件。

### 2. 版面识别：`layout_recognizer.py`

`LayoutRecognizer` 的功能可以理解为：

```text
页面图片 + OCR 文本框
  -> 调用版面检测模型
  -> 得到标题、正文、表格、图片、页眉、页脚等版面区域
  -> 把 OCR 文本框匹配到对应版面区域
  -> 给每个文本框打 layout_type/layoutno
```

注意：

- 它不是直接“切 chunk”。
- 它是给 OCR 文本框补充版面语义。
- 多个 OCR 文本框可以对应同一个版面标签。
- 例如一个表格区域内的很多文本框，都可能被标记为 `table`。

典型字段：

```python
{
    "text": "经营活动产生的现金流量净额",
    "x0": 100,
    "x1": 500,
    "top": 300,
    "bottom": 330,
    "layout_type": "table",
    "layoutno": 3
}
```

其中：

- `x0` 类似 left。
- `x1` 类似 right。
- `top` / `bottom` 是纵向边界。

### 3. 表格结构识别：`table_structure_recognizer.py`

`TableStructureRecognizer` 输入的是表格区域图片，不是整页 PDF。

它的目标是识别表格内部结构：

```text
表格图片
  -> 表格结构模型
  -> table row / table column / table column header / table spanning cell
  -> 与 OCR 文本框结合
  -> 输出 HTML table 或文本化表格
```

模型输出的结构框大概类似：

```python
[
    {"label": "table row", "x0": 10, "x1": 600, "top": 40, "bottom": 80},
    {"label": "table column", "x0": 10, "x1": 200, "top": 40, "bottom": 300},
    {"label": "table column header", "x0": 10, "x1": 600, "top": 40, "bottom": 80},
]
```

之后 `construct_table()` 会把 OCR 文本放回行列结构中，生成类似：

```html
<table>
  <tr><th>年份</th><th>收入</th></tr>
  <tr><td>2023</td><td>1000</td></tr>
</table>
```

所以表格链路是：

```text
layout 发现 table 区域
  -> 裁剪 table 图片
  -> table structure recognizer 识别行列结构
  -> OCR 文本落到对应单元格
  -> 输出 HTML/文本表格
```

### 4. 通用检测基础：`recognizer.py`

`Recognizer` 是 layout/table 检测模型的基础类，提供：

- 模型加载。
- 图片预处理。
- 推理调用。
- 后处理。
- 框排序。
- 重叠面积计算。
- 查找某个 OCR 框属于哪个 layout/table 框。

可以把它理解成：

```text
视觉检测模型的通用底座
```

`LayoutRecognizer` 和 `TableStructureRecognizer` 都是在它之上做具体任务。

## 四、Chunk 合并逻辑

`naive.py` 的整体逻辑不是单纯“拆分”，而是：

```text
parser 先粗拆
  -> 得到 sections/tables
  -> tables 先单独 tokenize
  -> sections 再按 token 数合并
  -> 生成最终 chunks
```

`naive_merge()` 的逻辑很朴素：

1. 顺序遍历 `sections`。
2. 把当前 section 追加到当前 chunk。
3. 如果当前 chunk 超过 `chunk_token_num` 阈值，就新开 chunk。
4. 如果设置了 `overlapped_percent`，新 chunk 带上一部分上一个 chunk 的尾部文本。

因此它是：

```text
顺序合并 + token 阈值控制 + 可选 overlap
```

不是复杂语义切分。

## 五、混合召回与重排

核心文件是：

```text
ragflow/rag/nlp/search.py
```

主线：

```text
Dealer.retrieval()
  -> Dealer.search()
  -> 全文检索 MatchTextExpr
  -> 向量检索 MatchDenseExpr
  -> FusionExpr weighted_sum
  -> rerank()
  -> similarity_threshold 过滤
  -> 返回 chunks
```

混合召回包含两部分：

- 关键词/全文召回。
- embedding 向量召回。

重排有两种：

- `rerank()`：本地混合相似度。
  - token similarity。
  - vector similarity。
  - rank feature / page rank / tag feature。

- `rerank_by_model()`：外部 reranker 模型。
  - token similarity 仍本地算。
  - 文档相关性分数由 rerank 模型给出。

关键参数：

- `similarity_threshold`：最终过滤阈值。
- `vector_similarity_weight`：向量相似度权重。
- `top_k`：候选窗口大小。
- `rerank_id` / `tenant_rerank_id`：是否启用外部 reranker。

## 六、评测参考

如果你要参考 RAGFlow 给自己的 RAG 做评测，可以重点看：

```text
ragflow/api/db/services/evaluation_service.py
ragflow/test/benchmark/
```

`evaluation_service.py` 当前可参考的指标：

- `precision`
- `recall`
- `f1_score`
- `hit_rate`
- `mrr`
- `answer_length`
- `has_answer`
- `avg_execution_time`

其中更适合你复用的是 retrieval 指标：

```text
retrieved_chunk_ids vs relevant_chunk_ids
```

也就是：

```text
系统实际召回的 chunk
  和
人工标注的相关 chunk
```

做集合和排序比较。

`test/benchmark` 更偏性能：

- 平均耗时。
- min latency。
- p50。
- p90。
- p95。

它适合评估接口速度，不够评估答案质量。

## 七、建议阅读顺序

建议按下面顺序看：

1. `ragflow/deepdoc/vision/ocr.py`
   - 先理解 OCR 如何得到文本框和文字。

2. `ragflow/deepdoc/vision/recognizer.py`
   - 理解视觉检测模型的通用封装。

3. `ragflow/deepdoc/vision/layout_recognizer.py`
   - 看版面标签如何分配给 OCR 文本框。

4. `ragflow/deepdoc/vision/table_structure_recognizer.py`
   - 看表格区域如何变成 HTML/文本表格。

5. `ragflow/deepdoc/parser/pdf_parser.py`
   - 把 OCR、layout、table structure 串起来看。

6. `ragflow/rag/app/naive.py`
   - 看 PDF 分支如何选择 parser，并产出 `sections/tables`。

7. `ragflow/rag/nlp/__init__.py`
   - 看 `naive_merge()` 和 `tokenize_chunks()`。

8. `ragflow/rag/svr/task_executor.py`
   - 看 chunk、embedding、入库如何串起来。

9. `ragflow/rag/nlp/search.py`
   - 看混合召回、融合、重排。

10. `ragflow/api/db/services/evaluation_service.py`
    - 看评测数据集、测试用例、指标计算。

## 八、一句话总结

DeepDOC 的 `vision` 模块负责把 PDF 页面图像变成“带坐标、带版面、带表格结构”的结构化内容；`naive.py` 再把这些内容粗拆后合并成 chunk；`search.py` 负责把 chunk 做全文召回、向量召回和重排；`evaluation_service.py` 和 `test/benchmark` 则分别提供质量评测和性能压测参考。
