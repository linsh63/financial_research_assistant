"""Streamlit Demo：金融研报 RAG 问答系统。"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
GENERATION = ROOT / "scripts" / "generation"
EVALUATION = ROOT / "scripts" / "evaluation"
for path in (SRC, GENERATION, EVALUATION):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import generate_answers as gen  # noqa: E402
from financial_report_rag.generation.context_formatter import (  # noqa: E402
    ContextFormatConfig,
    format_contexts,
)
from financial_report_rag.generation.llm_client import OpenAIChatClient, OpenAIChatConfig  # noqa: E402
from financial_report_rag.generation.prompt_builder import build_answer_messages  # noqa: E402


DEFAULT_MAX_TOKENS = 900
MODEL_PROVIDERS = {
    "GPT": {
        "api_key_env": "OPENAI_API_KEY",
        "base_url": "https://api.vveai.com/v1",
        "model": "gpt-5.4-mini",
    },
    "DeepSeek": {
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
    },
}


@dataclass(frozen=True)
class DemoConfig:
    """保存 Demo 使用的正式检索配置。"""

    index_dir: str = "data/processed/indexes/bge_large_zh_v15"
    index_type: str = "flat"
    bm25_path: str = "data/processed/indexes/bge_large_zh_v15/bm25.pkl"
    embedding_model: str = "models/bge-large-zh-v1.5"
    reranker_model: str = "models/bge-reranker-v2-m3"
    compare_rewrite_file: str = "data/processed/query_rewrites/compare_financial_table_no_unit_rule.jsonl"


def build_args(config: DemoConfig) -> SimpleNamespace:
    """构造与生成脚本兼容的参数对象。"""
    return SimpleNamespace(
        dry_run=False,
        index_dir=config.index_dir,
        index_type=config.index_type,
        bm25_path=config.bm25_path,
        embedding_model=config.embedding_model,
        embedding_backend="sentence-transformers",
        embedding_batch_size=16,
        embedding_max_length=512,
        reranker_model=config.reranker_model,
        reranker_backend="transformers",
        reranker_batch_size=2,
        reranker_max_length=512,
        score_activation="none",
        score_threshold=None,
        relative_drop_threshold=None,
        use_fp16=False,
        no_normalize=False,
        vector_weight=0.6,
        bm25_weight=0.4,
        fusion="weighted",
        rrf_k=60,
        parent_window_pages=1,
        parent_max_chars=0,
        fact_top_k=5,
        compare_candidate_top_k=20,
        compare_entity_top_k=8,
        compare_rewrite_file=config.compare_rewrite_file,
        compare_rewrite_top_k=8,
        compare_rewrite_mode="separate",
        compare_rewrite_per_query_keep=2,
        compare_rewrite_include_merged=False,
        compare_parent_fill=True,
        compare_parent_fill_pool=12,
        compare_coarse_to_fine_supplement=True,
        compare_coarse_doc_top_n=2,
        compare_coarse_adaptive_doc_ratio=3.0,
        compare_coarse_page_top_k=12,
        compare_coarse_per_entity_keep=4,
        compare_coarse_guarantee_per_entity=4,
        compare_top_k=5,
        summary_candidate_top_k=50,
        summary_top_k=8,
        summary_per_source=2,
        summary_subtopic_slots=False,
        summary_subtopic_top_k=12,
        summary_subtopic_max_queries=6,
        summary_subtopic_guarantee_per_query=1,
        summary_subtopic_per_query_keep=2,
        summary_subtopic_per_source=1,
        max_contexts=8,
        max_chars_per_context=1800,
        max_total_context_chars=9000,
        summary_evidence_pack=False,
        summary_evidence_points_per_context=6,
        summary_evidence_max_chars=7000,
    )


@st.cache_resource(show_spinner=False)
def load_retriever(config: DemoConfig) -> gen.GenerationRoutedRetriever:
    """加载一次索引和模型，后续交互复用。"""
    return gen.build_retriever(build_args(config))


def build_client(api_key: str, base_url: str, model: str, timeout: float, max_tokens: int) -> OpenAIChatClient:
    """构造 OpenAI-compatible 生成客户端。"""
    return OpenAIChatClient(
        OpenAIChatConfig(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=0.0,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    )


def render_provider_config(default_timeout: int) -> dict:
    """在侧边栏渲染模型服务选择和超时设置。"""
    provider_name = st.segmented_control(
        "模型服务",
        options=list(MODEL_PROVIDERS.keys()),
        default="GPT",
        width="stretch",
    )
    provider = MODEL_PROVIDERS[str(provider_name or "GPT")]
    timeout = st.number_input("超时秒数", min_value=10, max_value=300, value=default_timeout, step=10)
    st.caption(
        "\n".join(
            [
                f"API Key：`{provider['api_key_env']}`",
                f"Base URL：`{provider['base_url']}`",
                f"模型：`{provider['model']}`",
            ]
        )
    )
    return {
        "provider": provider_name,
        "api_key_env": provider["api_key_env"],
        "base_url": provider["base_url"],
        "model": provider["model"],
        "timeout": float(timeout),
        "max_tokens": DEFAULT_MAX_TOKENS,
    }


def apply_page_style() -> None:
    """注入少量页面样式，让 Demo 更适合现场展示。"""
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1280px;
        }
        div[data-testid="stExpander"] {
            border-radius: 8px;
        }
        .status-card {
            border: 1px solid rgba(128, 128, 128, 0.28);
            border-radius: 8px;
            padding: 0.75rem 0.9rem;
            background: rgba(128, 128, 128, 0.08);
            min-height: 4.2rem;
        }
        .status-card span {
            display: block;
            color: #9ca3af;
            font-size: 0.82rem;
            margin-bottom: 0.25rem;
        }
        .status-card strong {
            display: block;
            font-size: 1.05rem;
            line-height: 1.3;
            word-break: break-word;
        }
        .demo-subtitle {
            color: #4b5563;
            font-size: 0.98rem;
            margin-top: -0.4rem;
            margin-bottom: 1.2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def sample_questions() -> dict[str, tuple[str, str]]:
    """提供可以一键填入的演示问题。"""
    return {
        "事实型": ("fact", "比亚迪2026 Q1 营收多少"),
        "对比型": ("compare", "保利发展 vs 华发股份，哪家公司2025年实现营收更高"),
        "汇总型": ("summary", "新型储能政策对发展目标、应用场景、技术路线和市场机制是如何安排的？"),
    }


def resolve_source_path(source: str) -> Path:
    """把引用中的 source 路径解析到本地 PDF 文件。"""
    path = Path(source)
    if path.is_absolute():
        return path
    return ROOT / path


@st.cache_data(show_spinner=False)
def read_pdf_bytes(path_text: str) -> bytes:
    """读取 PDF 字节，供下载按钮复用。"""
    return Path(path_text).read_bytes()


def render_references(references: list[dict]) -> None:
    """展示结构化引用来源。"""
    if not references:
        st.info("本次没有可展示的引用。")
        return
    rows = []
    for ref in references:
        source = ref.get("source", "")
        rows.append(
            {
                "ref_id": ref.get("ref_id", ""),
                "source": Path(source).name if source else "",
                "pages": ",".join(str(page) for page in ref.get("pages") or []),
                "score": round(float(ref.get("score", 0.0)), 4),
                "chunk_id": ref.get("chunk_id", ""),
            }
        )
    st.dataframe(rows, width="stretch", hide_index=True)


def render_pdf_downloads(references: list[dict], key_prefix: str = "pdf") -> None:
    """为引用到的 PDF 提供下载按钮。"""
    sources: dict[str, Path] = {}
    for ref in references:
        source = str(ref.get("source") or "")
        if not source:
            continue
        source_path = resolve_source_path(source)
        sources[source] = source_path

    if not sources:
        st.info("本次没有可下载的 PDF 来源。")
        return

    st.caption("按引用来源去重展示，点击按钮即可下载对应 PDF。")
    columns = st.columns(2)
    for index, (source, source_path) in enumerate(sources.items()):
        column = columns[index % 2]
        file_name = source_path.name
        pages = sorted(
            {
                page
                for ref in references
                if str(ref.get("source") or "") == source
                for page in (ref.get("pages") or [])
            }
        )
        page_text = ",".join(str(page) for page in pages) if pages else "-"
        with column:
            st.markdown(f"**{file_name}**")
            st.caption(f"引用页码：{page_text}")
            if source_path.exists():
                st.download_button(
                    label="下载 PDF",
                    data=read_pdf_bytes(str(source_path)),
                    file_name=file_name,
                    mime="application/pdf",
                    key=f"{key_prefix}_download_{index}_{file_name}",
                    on_click="ignore",
                    width="stretch",
                )
            else:
                st.warning(f"本地文件不存在：{source_path}")


def render_status_cards(items: list[tuple[str, str | int]]) -> None:
    """用暗色主题友好的小卡片展示运行状态。"""
    columns = st.columns(len(items))
    for column, (label, value) in zip(columns, items):
        with column:
            st.markdown(
                f"""
                <div class="status-card">
                    <span>{label}</span>
                    <strong>{value}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_contexts(formatted) -> None:
    """逐条展示进入 LLM 的证据块。"""
    for context in formatted.contexts:
        source_name = Path(context.source).name if context.source else ""
        pages = ",".join(str(page) for page in context.pages) if context.pages else "-"
        title = f"资料{context.index} | {source_name} | pages={pages} | score={context.score:.4f}"
        with st.expander(title, expanded=context.index <= 2):
            st.caption(f"chunk_id: {context.chunk_id}")
            st.write(context.text)


def render_result(result: dict) -> None:
    """渲染一次问答结果。"""
    st.success(f"检索完成：策略 `{result['strategy']}`，进入上下文资料 {len(result['formatted'].contexts)} 条。")
    render_status_cards(
        [
            ("问题类型", result["question_type"]),
            ("最终证据数", len(result["formatted"].contexts)),
            ("候选证据数", result["candidate_count"]),
            ("Prompt 字数", len(result["messages"][-1]["content"])),
        ]
    )

    answer_tab, evidence_tab, prompt_tab = st.tabs(["回答与引用", "召回证据", "完整 Prompt"])
    with answer_tab:
        answer_col, reference_col = st.columns([1.15, 1])
        with answer_col:
            st.subheader("回答")
            st.markdown(result["answer"])
        with reference_col:
            st.subheader("引用来源")
            render_references(result["formatted"].references)
            st.subheader("PDF 下载")
            render_pdf_downloads(result["formatted"].references)

    with evidence_tab:
        st.subheader("进入生成模型的证据")
        render_contexts(result["formatted"])

    with prompt_tab:
        st.subheader("完整 Prompt")
        st.json(result["messages"])


def main() -> None:
    """启动 Streamlit 页面。"""
    st.set_page_config(page_title="金融研报 RAG Demo", layout="wide")
    apply_page_style()
    st.title("金融研报 RAG Demo")
    st.markdown(
        '<div class="demo-subtitle">输入问题后，系统会展示路由策略、召回证据、最终回答、引用来源，并支持下载对应 PDF。</div>',
        unsafe_allow_html=True,
    )

    config = DemoConfig()
    with st.sidebar:
        st.header("运行配置")
        st.caption("一键切换 GPT / DeepSeek。若想只看检索证据，可以手动打开 dry-run。")
        dry_run = st.checkbox("只检索，不调用 API", value=False)
        provider_config = render_provider_config(default_timeout=90)

        st.divider()
        st.subheader("正式检索路线")
        st.code(
            "\n".join(
                [
                    "fact: hybrid Top5 + parent window",
                    "compare: query rewrite + entity slots + rerank + parent fill",
                    "summary: hybrid Top50 + source diverse Top8",
                ]
            )
        )

    samples = sample_questions()
    st.subheader("示例问题")
    cols = st.columns(len(samples))
    for col, (label, (sample_type, sample_query)) in zip(cols, samples.items()):
        if col.button(label, width="stretch"):
            st.session_state["question_type"] = sample_type
            st.session_state["query"] = sample_query

    st.subheader("输入问题")
    question_type = st.radio(
        "问题类型",
        options=["fact", "compare", "summary"],
        horizontal=True,
        index=["fact", "compare", "summary"].index(st.session_state.get("question_type", "fact")),
    )
    query = st.text_area(
        "问题",
        value=st.session_state.get("query", "比亚迪2026 Q1 营收多少"),
        height=90,
    )
    run = st.button("开始问答", type="primary", width="stretch")

    if not run:
        last_result = st.session_state.get("last_demo_result")
        if last_result:
            st.caption("以下为上一次问答结果。修改问题后，请重新点击“开始问答”刷新。")
            render_result(last_result)
        else:
            st.info("可以先点一个示例问题，也可以直接输入自己的问题。")
        return

    if not query.strip():
        st.warning("请先输入问题。")
        return

    api_key = os.getenv(provider_config["api_key_env"], "")
    if not dry_run and not api_key:
        st.error(f"没有读取到环境变量 `{provider_config['api_key_env']}`。可以先勾选 dry-run，或在终端设置 API Key 后重启 Demo。")
        return

    with st.spinner("正在加载索引、执行混合召回和 rerank..."):
        retriever = load_retriever(config)
        question = {
            "question_id": "demo_001",
            "question_type": question_type,
            "query": query.strip(),
        }
        routed = retriever.retrieve_question(question)
        context_config = ContextFormatConfig(max_contexts=8, max_chars_per_context=1800, max_total_chars=9000)
        formatted = format_contexts(
            routed.results,
            context_config,
            query=question["query"],
            question_type=routed.question_type,
        )
        messages = build_answer_messages(question["query"], routed.question_type, formatted.text)

    if dry_run:
        answer = "当前为 dry-run 模式，只展示检索证据和 prompt，未调用生成模型。"
    else:
        with st.spinner("正在调用生成模型..."):
            client = build_client(
                api_key,
                provider_config["base_url"],
                provider_config["model"],
                provider_config["timeout"],
                provider_config["max_tokens"],
            )
            answer = client.generate(messages)

    result = {
        "answer": answer,
        "candidate_count": len(routed.results),
        "formatted": formatted,
        "messages": messages,
        "question_type": routed.question_type,
        "strategy": routed.strategy,
    }
    st.session_state["last_demo_result"] = result
    render_result(result)


if __name__ == "__main__":
    main()
