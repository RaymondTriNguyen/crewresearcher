"""Streamlit UI for the multi-agent company research crew."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Company Research Crew",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    .block-container { padding-top: 2rem; max-width: 1100px; }
    .hero-title {
        font-size: 2.25rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
    }
    .hero-sub {
        color: #6b7280;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .agent-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem 1.1rem;
        height: 100%;
    }
    .agent-card h4 { margin: 0 0 0.35rem 0; font-size: 0.95rem; }
    .agent-card p { margin: 0; font-size: 0.82rem; color: #64748b; line-height: 1.4; }
    .status-ok { color: #059669; font-weight: 600; }
    .status-missing { color: #dc2626; font-weight: 600; }
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    div[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    div[data-testid="stSidebar"] .stButton > button {
        background: #334155;
        border: 1px solid #475569;
        color: #f8fafc !important;
    }
    div[data-testid="stSidebar"] .stButton > button:hover {
        background: #475569;
        border-color: #64748b;
    }
</style>
"""

AGENT_INFO = [
    ("Web Researcher", "Searches the web via Serper for news, products, and market signals."),
    ("Data Extractor", "Scrapes the company website and pulls structured facts."),
    ("Report Editor", "Synthesizes findings into an executive markdown report."),
]

RESEARCH_STEPS = [
    "Web research & search",
    "Website scraping",
    "Executive report",
]

API_KEY_FIELDS = {
    "OPENAI_API_KEY": "OpenAI API key",
    "SERPER_API_KEY": "Serper API key",
}


def _session_key_name(env_key: str) -> str:
    return f"runtime_{env_key.lower()}"


def _input_key_name(env_key: str) -> str:
    return f"input_{env_key.lower()}"


def _get_api_key(env_key: str) -> tuple[str, str]:
    session_value = str(st.session_state.get(_session_key_name(env_key), "")).strip()
    if session_value:
        return session_value, "website input"

    env_value = (os.getenv(env_key) or "").strip()
    if env_value:
        return env_value, "environment"

    return "", ""


def _sync_api_key_inputs() -> None:
    for env_key in API_KEY_FIELDS:
        entered = str(st.session_state.get(_input_key_name(env_key), "")).strip()
        if entered:
            st.session_state[_session_key_name(env_key)] = entered

    for env_key in API_KEY_FIELDS:
        value, _ = _get_api_key(env_key)
        if value:
            os.environ[env_key] = value


def _api_status() -> tuple[bool, bool]:
    openai_ok = bool(_get_api_key("OPENAI_API_KEY")[0])
    serper_ok = bool(_get_api_key("SERPER_API_KEY")[0])
    return openai_ok, serper_ok


def _result_to_markdown(result: object) -> str:
    if result is None:
        return ""
    raw = getattr(result, "raw", None)
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    text = str(result).strip()
    if text.startswith("```markdown"):
        text = re.sub(r"^```markdown\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    elif text.startswith("```"):
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _run_company_research(company_name: str, verbose: bool) -> object:
    from crewresearcher import run_company_research

    return run_company_research(company_name, verbose=verbose)


def _init_session() -> None:
    defaults = {
        "report_md": "",
        "report_company": "",
        "report_generated_at": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _render_sidebar() -> tuple[bool, bool, str | None]:
    with st.sidebar:
        st.markdown("### API keys")
        for env_key, label in API_KEY_FIELDS.items():
            st.text_input(
                label,
                type="password",
                key=_input_key_name(env_key),
                placeholder=f"Paste {env_key}",
            )

        _sync_api_key_inputs()
        openai_ok, serper_ok = _api_status()
        ready = openai_ok and serper_ok

        st.divider()
        st.markdown("### Configuration")
        openai_source = _get_api_key("OPENAI_API_KEY")[1]
        st.markdown(
            f'<span class="{"status-ok" if openai_ok else "status-missing"}">'
            f'{"✓" if openai_ok else "✗"} OPENAI_API_KEY</span>',
            unsafe_allow_html=True,
        )
        if openai_ok:
            st.caption(f"Ready from {openai_source}.")

        serper_source = _get_api_key("SERPER_API_KEY")[1]
        st.markdown(
            f'<span class="{"status-ok" if serper_ok else "status-missing"}">'
            f'{"✓" if serper_ok else "✗"} SERPER_API_KEY</span>',
            unsafe_allow_html=True,
        )
        if serper_ok:
            st.caption(f"Ready from {serper_source}.")

        if not ready:
            st.error("Paste the missing keys above. `.env` can still be used as a fallback.")

        st.divider()
        st.markdown("### Options")
        verbose = st.toggle("Verbose agent logs", value=False)

        st.divider()
        st.markdown("### Quick examples")
        examples = ["Notion", "Stripe", "Anthropic", "Figma"]
        cols = st.columns(2)
        picked = None
        for i, name in enumerate(examples):
            if cols[i % 2].button(name, use_container_width=True, key=f"ex_{name}"):
                picked = name

        st.divider()
        st.markdown("### How it works")
        for title, desc in AGENT_INFO:
            st.markdown(f"**{title}** — {desc}")
        st.caption("Research usually takes 1–3 minutes.")

    return ready, verbose, picked


def _render_hero() -> None:
    st.markdown('<p class="hero-title">Company Research Crew</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-sub">AI agents research any company or product and deliver '
        "an executive-ready report with sources.</p>",
        unsafe_allow_html=True,
    )


def _render_agent_cards() -> None:
    cols = st.columns(3)
    for col, (title, desc) in zip(cols, AGENT_INFO):
        with col:
            st.markdown(
                f'<div class="agent-card"><h4>{title}</h4><p>{desc}</p></div>',
                unsafe_allow_html=True,
            )


def main() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    _init_session()

    ready, verbose, example_pick = _render_sidebar()
    _render_hero()
    _render_agent_cards()
    st.divider()

    default_name = st.session_state.get("report_company", "")
    if example_pick:
        default_name = example_pick

    with st.form("research_form", clear_on_submit=False):
        company = st.text_input(
            "Company or product name",
            value=default_name,
            placeholder="e.g. Notion, Stripe, Acme Corp",
            help="Enter the legal name or common brand name.",
        )
        submitted = st.form_submit_button(
            "Run research",
            type="primary",
            use_container_width=True,
            disabled=not ready,
        )

    if submitted:
        name = (company or "").strip()
        if not name:
            st.warning("Please enter a company or product name.")
        else:
            st.session_state.report_company = name
            with st.status("Research in progress…", expanded=True) as status:
                for step in RESEARCH_STEPS:
                    st.write(f"⏳ {step}")
                try:
                    os.environ.setdefault("PYTHONUTF8", "1")
                    result = _run_company_research(name, verbose=verbose)
                    report = _result_to_markdown(result)
                    if not report:
                        raise RuntimeError("The crew returned an empty report.")
                    st.session_state.report_md = report
                    st.session_state.report_generated_at = datetime.now(timezone.utc)
                    status.update(label="Research complete", state="complete", expanded=False)
                except Exception as exc:
                    status.update(label="Research failed", state="error", expanded=True)
                    st.error(str(exc))

    report = st.session_state.report_md
    if report:
        company_label = st.session_state.report_company or "company"
        generated = st.session_state.report_generated_at
        meta = f"Report: **{company_label}**"
        if generated:
            meta += f" · Generated {generated.strftime('%Y-%m-%d %H:%M UTC')}"
        st.success(meta)

        tab_report, tab_raw = st.tabs(["Report", "Markdown source"])
        with tab_report:
            st.markdown(report)
        with tab_raw:
            st.code(report, language="markdown")

        filename = re.sub(r"[^\w\-]+", "_", company_label.lower()).strip("_") or "report"
        st.download_button(
            label="Download report (.md)",
            data=report,
            file_name=f"{filename}_research_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
    elif ready:
        st.info("Enter a company name and click **Run research** to generate a report.")


if __name__ == "__main__":
    main()
