"""Multi-agent company research crew for the Streamlit app."""

import os
from typing import Any

from crewai import Agent, Crew, LLM, Process, Task
from crewai_tools import SerperDevTool
from dotenv import load_dotenv

from tools.website_scraper import scrape_company_website

load_dotenv()

OPENAI_MODEL = "gpt-4o-mini"


def _get_llm() -> LLM:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is missing. Enter it in the app sidebar or add it to your .env file."
        )
    os.environ["OPENAI_API_KEY"] = api_key
    return LLM(model=OPENAI_MODEL, api_key=api_key)


def _check_serper() -> None:
    if not (os.getenv("SERPER_API_KEY") or "").strip():
        raise ValueError(
            "SERPER_API_KEY is missing. Enter it in the app sidebar or add it to your .env file."
        )


def build_company_research_crew(company_name: str, verbose: bool = False) -> Crew:
    """Create a crew tailored to research the given company or product."""
    _check_serper()
    llm = _get_llm()
    search_tool = SerperDevTool()

    web_researcher = Agent(
        role="Web Researcher",
        goal=(
            f"Find recent, credible online information about {company_name} including "
            "news, funding, partnerships, products, competitors, and market signals."
        ),
        backstory=(
            "You are an expert internet researcher who excels at discovering high-quality "
            "sources and distinguishing signal from noise."
        ),
        tools=[search_tool],
        llm=llm,
        verbose=verbose,
        allow_delegation=False,
    )

    data_extractor = Agent(
        role="Data Extractor",
        goal=(
            f"Scrape and extract structured facts from {company_name}'s official website "
            "and other primary sources found during research."
        ),
        backstory=(
            "You specialize in pulling clean, factual content from websites and "
            "turning raw pages into structured business intelligence."
        ),
        tools=[scrape_company_website],
        llm=llm,
        verbose=verbose,
        allow_delegation=False,
    )

    report_editor = Agent(
        role="Report Editor",
        goal=(
            f"Produce a polished, executive-ready research report on {company_name} "
            "for business stakeholders."
        ),
        backstory=(
            "You are a senior analyst who synthesizes research into clear, actionable "
            "reports with consistent structure and cited sources."
        ),
        llm=llm,
        verbose=verbose,
        allow_delegation=False,
    )

    web_research_task = Task(
        description=(
            f"Research '{company_name}' across the web. Use the search tool to find:\n"
            "- Company background and what they do\n"
            "- Main products or services\n"
            "- Recent news (last 12 months)\n"
            "- Market position and competitors\n"
            "- Official website URL(s) and notable press or blog URLs\n\n"
            "Run multiple targeted searches. Cite source URLs for each finding."
        ),
        expected_output=(
            "Structured research notes with sections: Background, Products, Recent News, "
            "Market Position, and a list of URLs to scrape (official site + 2-4 key pages)."
        ),
        agent=web_researcher,
    )

    extraction_task = Task(
        description=(
            f"Using the Web Researcher's notes and URLs, scrape {company_name}'s official "
            "website and the most important related pages with the website scraping tool.\n\n"
            "Extract: company overview, products/services, leadership or mission if available, "
            "and any product or pricing signals on the site.\n"
            "If a URL fails, note it and continue with other URLs."
        ),
        expected_output=(
            "Structured extraction with: Company Overview, Products/Services, "
            "Website Facts, and Scraped URLs with brief notes on each."
        ),
        agent=data_extractor,
        context=[web_research_task],
    )

    report_task = Task(
        description=(
            f"Compile a final company research report on '{company_name}' using the web "
            "research and website extraction outputs.\n\n"
            "The report must include these markdown sections:\n"
            "## Executive Summary\n"
            "## Company Background\n"
            "## Products & Services\n"
            "## Recent News & Developments\n"
            "## Market Position & Competitors\n"
            "## Key Insights & Risks\n"
            "## Sources\n\n"
            "Be factual, concise, and business-oriented. Include source URLs in Sources."
        ),
        expected_output=(
            "A complete markdown research report with all required sections, "
            "ready to present to executives."
        ),
        agent=report_editor,
        context=[web_research_task, extraction_task],
    )

    return Crew(
        agents=[web_researcher, data_extractor, report_editor],
        tasks=[web_research_task, extraction_task, report_task],
        process=Process.sequential,
        verbose=verbose,
    )


def run_company_research(company_name: str, verbose: bool = False) -> Any:
    """Run the research crew and return the final report."""
    name = company_name.strip()
    if not name:
        raise ValueError("Company or product name cannot be empty.")

    crew = build_company_research_crew(name, verbose=verbose)
    return crew.kickoff()
