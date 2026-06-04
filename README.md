# Company Research Crew

Multi-agent company research powered by [CrewAI](https://github.com/joaomdmoura/crewAI), with a Streamlit UI.

## Setup

1. Clone the repo and install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and add your API keys:

   - `OPENAI_API_KEY` — [OpenAI](https://platform.openai.com/api-keys)
   - `SERPER_API_KEY` — [Serper](https://serper.dev)

## Run

**Streamlit UI:**

```bash
streamlit run app.py
```

**CLI:**

```bash
python -c "from crewresearcher import run_company_research; print(run_company_research('Notion'))"
```

## Agents

1. **Web Researcher** — web search via Serper  
2. **Data Extractor** — scrapes the company website  
3. **Report Editor** — produces an executive markdown report  
