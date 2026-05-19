"""Streamlit Demo v2：GPT 风格的金融研报 RAG 问答。"""

from __future__ import annotations

import os
import sys
from html import escape
from uuid import uuid4
from pathlib import Path
from typing import Iterator

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = ROOT / "demo"
SRC = ROOT / "src"
GENERATION = ROOT / "scripts" / "generation"
EVALUATION = ROOT / "scripts" / "evaluation"
for path in (DEMO_DIR, SRC, GENERATION, EVALUATION):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app import (  # noqa: E402
    DemoConfig,
    apply_page_style,
    load_retriever,
    read_pdf_bytes,
    render_provider_config,
    render_pdf_downloads,
    render_references,
    resolve_source_path,
    sample_questions,
)
from financial_report_rag.generation.context_formatter import (  # noqa: E402
    ContextFormatConfig,
    FormattedContexts,
    format_contexts,
)
from financial_report_rag.generation.prompt_builder import build_answer_messages  # noqa: E402


QUESTION_TYPE_LABELS = {
    "fact": "事实型",
    "compare": "对比型",
    "summary": "汇总型",
}


def apply_chat_style() -> None:
    """补充 GPT 风格聊天页面样式。"""
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 980px;
            padding-top: 1.4rem;
        }
        .chat-title {
            font-size: 1.55rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }
        .chat-subtitle {
            color: #9ca3af;
            font-size: 0.95rem;
            margin-bottom: 1rem;
        }
        .thinking-box {
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 10px;
            padding: 0.8rem 0.95rem;
            background: rgba(128, 128, 128, 0.08);
            color: #9ca3af;
            line-height: 1.6;
        }
        .source-card {
            border: 1px solid rgba(128, 128, 128, 0.22);
            border-radius: 8px;
            padding: 0.7rem 0.8rem;
            margin-bottom: 0.55rem;
            background: rgba(128, 128, 128, 0.06);
        }
        .source-card small {
            color: #9ca3af;
        }
        .user-message-row {
            display: flex;
            justify-content: flex-end;
            margin: 0.35rem 0 0.8rem 0;
        }
        .user-message-bubble {
            max-width: 72%;
            border-radius: 18px;
            padding: 0.72rem 0.95rem;
            background: #2f2f2f;
            color: #f9fafb;
            line-height: 1.65;
            white-space: pre-wrap;
            word-break: break-word;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def stream_answer(
    messages: list[dict[str, str]],
    api_key: str,
    base_url: str,
    model: str,
    timeout: float,
    max_tokens: int,
) -> Iterator[str]:
    """调用 OpenAI-compatible Chat Completions 流式接口。"""
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout, max_retries=2)
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.0,
        max_tokens=max_tokens,
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        token = getattr(delta, "content", None)
        if token:
            yield token


def context_to_dicts(formatted: FormattedContexts) -> list[dict]:
    """把 FormattedContext 转为可存在 session_state 中的普通字典。"""
    return [
        {
            "index": context.index,
            "source": context.source,
            "pages": context.pages,
            "chunk_id": context.chunk_id,
            "score": context.score,
            "text": context.text,
        }
        for context in formatted.contexts
    ]


def render_source_cards(contexts: list[dict]) -> None:
    """以更紧凑的卡片形式展示证据块。"""
    if not contexts:
        st.info("本次没有可展示的证据。")
        return
    for context in contexts:
        source_name = Path(context.get("source", "")).name
        pages = ",".join(str(page) for page in context.get("pages", []) or []) or "-"
        title = f"资料{context['index']} | {source_name} | pages={pages} | score={context['score']:.4f}"
        with st.expander(title, expanded=context["index"] <= 2):
            st.caption(f"chunk_id: {context.get('chunk_id', '')}")
            st.write(context.get("text", ""))


def render_downloads_from_refs(references: list[dict], key_prefix: str) -> None:
    """渲染 PDF 下载区，复用第一版的下载逻辑。"""
    render_pdf_downloads(references, key_prefix=key_prefix)


def build_demo_result(query: str, question_type: str) -> tuple[dict, list[dict[str, str]]]:
    """执行检索并构造生成 prompt。"""
    retriever = load_retriever(DemoConfig())
    question = {
        "question_id": "chat_demo_001",
        "question_type": question_type,
        "query": query.strip(),
    }
    routed = retriever.retrieve_question(question)
    formatted = format_contexts(
        routed.results,
        ContextFormatConfig(max_contexts=8, max_chars_per_context=1800, max_total_chars=9000),
        query=question["query"],
        question_type=routed.question_type,
    )
    messages = build_answer_messages(question["query"], routed.question_type, formatted.text)
    result = {
        "query": query,
        "question_type": routed.question_type,
        "strategy": routed.strategy,
        "candidate_count": len(routed.results),
        "references": formatted.references,
        "contexts": context_to_dicts(formatted),
        "prompt_messages": messages,
    }
    return result, messages


def init_state() -> None:
    """初始化聊天状态。"""
    st.session_state.setdefault("chat_messages", [])
    st.session_state.setdefault("chat_question_type", "fact")


def render_user_message(content: str) -> None:
    """右对齐渲染用户消息。"""
    st.markdown(
        f"""
        <div class="user-message-row">
            <div class="user-message-bubble">{escape(content)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_history() -> None:
    """渲染历史对话。"""
    for index, message in enumerate(st.session_state.chat_messages):
        if message["role"] == "user":
            render_user_message(message["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(message["content"])
                if message.get("result"):
                    message["result"].setdefault("message_id", f"history_{index}")
                    render_assistant_details(message["result"])


def render_assistant_details(result: dict) -> None:
    """展示一轮回答的检索细节和 PDF 下载。"""
    message_id = str(result.get("message_id") or "message")
    st.caption(
        f"策略：`{result['strategy']}` | 问题类型：`{result['question_type']}` | "
        f"候选：{result['candidate_count']} | 证据：{len(result['contexts'])}"
    )
    with st.expander("引用来源与 PDF 下载", expanded=False):
        render_references(result["references"])
        st.divider()
        render_downloads_from_refs(result["references"], key_prefix=f"chat_{message_id}")
    with st.expander("召回证据", expanded=False):
        render_source_cards(result["contexts"])
    with st.expander("完整 Prompt", expanded=False):
        st.json(result["prompt_messages"])


def sidebar_config() -> dict:
    """读取侧边栏配置。"""
    with st.sidebar:
        st.header("运行配置")
        st.caption("一键切换 GPT / DeepSeek，并采用流式回答。")
        provider_config = render_provider_config(default_timeout=120)
        pending_question_type = st.session_state.pop("pending_question_type", None)
        if pending_question_type:
            st.session_state.chat_question_type = pending_question_type
        st.segmented_control(
            "问题类型",
            options=["fact", "compare", "summary"],
            format_func=lambda value: QUESTION_TYPE_LABELS.get(value, value),
            key="chat_question_type",
            width="stretch",
        )

        st.divider()
        if st.button("清空对话", width="stretch"):
            st.session_state.chat_messages = []
            st.session_state.pop("pending_question", None)
            st.rerun()

        st.subheader("示例问题")
        for label, (sample_type, sample_query) in sample_questions().items():
            if st.button(label, width="stretch"):
                st.session_state.pending_question = sample_query
                st.session_state.pending_question_type = sample_type
                st.rerun()

    return {
        "api_key_env": provider_config["api_key_env"],
        "base_url": provider_config["base_url"],
        "model": provider_config["model"],
        "timeout": provider_config["timeout"],
        "max_tokens": provider_config["max_tokens"],
    }


def main() -> None:
    """启动 GPT 风格聊天 Demo。"""
    st.set_page_config(page_title="Financial RAG Chat", layout="wide")
    apply_page_style()
    apply_chat_style()
    init_state()

    config = sidebar_config()
    st.markdown('<div class="chat-title">Financial RAG Chat</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="chat-subtitle">像 ChatGPT 一样提问；检索阶段显示思考状态，生成阶段流式输出答案。</div>',
        unsafe_allow_html=True,
    )

    render_chat_history()

    query = st.chat_input("输入问题，例如：比亚迪2026 Q1 营收多少")
    pending_question = st.session_state.pop("pending_question", "")
    if pending_question and not query:
        query = pending_question

    if not query:
        return
    query = query.strip()
    question_type = str(st.session_state.get("chat_question_type") or "fact")

    api_key = os.getenv(config["api_key_env"], "")
    if not api_key:
        with st.chat_message("assistant"):
            st.error(f"没有读取到环境变量 `{config['api_key_env']}`。请在终端设置后重启 Demo。")
        return

    st.session_state.chat_messages.append({"role": "user", "content": query})
    render_user_message(query)

    with st.chat_message("assistant"):
        thinking = st.empty()
        thinking.markdown(
            '<div class="thinking-box">思考中... 正在检索相关研报、政策文档和表格证据。</div>',
            unsafe_allow_html=True,
        )
        result, messages = build_demo_result(query, question_type)
        thinking.markdown(
            f'<div class="thinking-box">思考中... 已检索到 {len(result["contexts"])} 条证据，正在生成回答。</div>',
            unsafe_allow_html=True,
        )
        result["message_id"] = uuid4().hex

        answer_placeholder = st.empty()
        answer = ""
        for token in stream_answer(
            messages,
            api_key=api_key,
            base_url=config["base_url"],
            model=config["model"],
            timeout=config["timeout"],
            max_tokens=config["max_tokens"],
        ):
            answer += token
            answer_placeholder.markdown(answer + "▌")
        answer_placeholder.markdown(answer)
        thinking.empty()
        result["answer"] = answer
        render_assistant_details(result)

    st.session_state.chat_messages.append({"role": "assistant", "content": answer, "result": result})


if __name__ == "__main__":
    main()
