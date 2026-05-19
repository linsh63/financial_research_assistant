# Demo 使用说明

项目提供了一个 Streamlit Demo，用于面试或本地演示：

- 输入 query。
- 自动按问题类型执行 routed retrieval。
- 展示召回证据、来源文档、页码和 chunk id。
- 支持下载本次引用到的原始 PDF。
- 调用 OpenAI-compatible API 生成答案。
- 默认使用 GPT API；也支持 dry-run 模式，只展示检索结果和 prompt，不调用 API。

## 启动命令

第一版 Demo 是信息面板式页面：

```bash
cd /Users/linsh/Documents/Recommendation/project/ProjectSet/financial_research_assistant
source .venv-brew/bin/activate
streamlit run demo/app.py
```

第二版 Demo 是 GPT 风格聊天页面，支持检索阶段“思考中...”和流式回答：

```bash
cd /Users/linsh/Documents/Recommendation/project/ProjectSet/financial_research_assistant
source .venv-brew/bin/activate
streamlit run demo/app_chat.py
```

启动后浏览器会打开本地页面。如果没有自动打开，终端会显示类似：

```text
Local URL: http://localhost:8501
```

## API 配置

Demo 侧边栏支持一键切换 `GPT` 和 `DeepSeek`。页面会自动切换 API Key 环境变量名、Base URL 和模型名。

使用 GPT：

```bash
export OPENAI_API_KEY="你的 key"
```

使用 DeepSeek：

```bash
export DEEPSEEK_API_KEY="你的 key"
```

当前 Demo 内置配置：

| provider | api_key_env | base_url | model |
|---|---|---|---|
| GPT | `OPENAI_API_KEY` | `https://api.vveai.com/v1` | `gpt-5.4-mini` |
| DeepSeek | `DEEPSEEK_API_KEY` | `https://api.deepseek.com` | `deepseek-chat` |

默认情况下，页面不会勾选 dry-run。也就是说，只要终端里设置了 `OPENAI_API_KEY`，点击“开始问答”就会调用模型生成答案。

## Dry-run 模式

如果没有 API Key，或网络不稳定，可以勾选：

```text
只检索，不调用 API
```

此时 Demo 会完成：

1. 加载 FAISS、BM25、embedding 和 reranker。
2. 执行正式 routed retrieval。
3. 展示进入 LLM 的证据块和完整 prompt。

不会调用生成模型。

## PDF 下载

每次回答后，`回答与引用` 标签页会展示引用来源表，并在 `PDF 下载` 区域按来源文档去重生成下载按钮。下载的是本地 `data/raw/` 中对应的原始 PDF。

## 当前 Demo 使用的正式策略

| question_type | strategy |
|---|---|
| fact | hybrid Top5 + parent window |
| compare | query rewrite + raw coarse-to-fine entity slots + rerank + parent fill |
| summary | hybrid Top50 + source diverse Top8 |

对应实验结果见：

- `docs/experiments/rerank/17_routed_compare_raw_entity_slots/report.md`
- `docs/experiments/generation/routed_v17_deepseek_full_judge/report.md`

## 推荐演示问题

事实型：

```text
2025年，全国高校毕业生达多少人？
```

对比型：

```text
保利发展 vs 华发股份，哪家公司2025年实现营收更高
```

汇总型：

```text
新型储能政策对发展目标、应用场景、技术路线和市场机制是如何安排的？
```

## 演示时可以强调的点

- Demo 不是单独写的简化流程，而是复用正式评测中的 routed retrieval 和 prompt。
- 每个回答都能查看引用来源和页码，便于解释“答案为什么这么来”。
- dry-run 模式可以直接展示检索证据，用于排查召回是否命中。
- 对比型问题会通过实体槽位保障两家公司证据都进入候选池。
