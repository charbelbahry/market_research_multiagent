# AI Product Research & Feasibility Analyzer — Full Build Plan

**A milestone-driven, test-at-every-step implementation guide for a portfolio-grade CrewAI + FastAPI project.**

This document is two things at once:
1. A precise build order you can follow with no guesswork.
2. Your interview weapon — every milestone ends with the *why* and the exact questions you'll be asked, so you can defend every line.

Target build time: **1–2 focused days.** Each milestone is independently shippable and demoable. If you run out of time at any milestone, what you have still works and still demos.

---

## Table of Contents

- [0. Mental Model (read this first)](#0-mental-model)
- [1. The Golden Rule of this Project](#1-the-golden-rule)
- [2. Tech Decisions & Trade-offs (interview ammo)](#2-tech-decisions)
- [3. Milestones](#3-milestones)
  - [M0 — Scaffold & Health](#m0)
  - [M1 — The Contract (schemas)](#m1)
  - [M2 — Mock Engine (lightweight, testing utility)](#m2)
  - [M3 — API wired to orchestrator](#m3)
  - [M4 — Tools layer (search + mock)](#m4)
  - [M5 — Agents + Multi-Model Routing](#m5)
  - [M6 — Tasks & Crew (the real pipeline)](#m6)
  - [M7 — Async, timeouts, graceful degradation](#m7)
  - [M8 — MCP Server](#m8)
  - [M9 — Observability (LangFuse)](#m9)
  - [M10 — Tests, lint, types, CI](#m10)
  - [M11 — Docker](#m11)
  - [M12 — Docs, diagram, demo script](#m12)
- [4. The 2–3 Minute Interview Pitch](#4-pitch)
- [5. The Kill-Shot Questions (and your answers)](#5-questions)
- [6. Failure Modes You Must Be Able to Name](#6-failure-modes)
- [7. Definition of "Done Done"](#7-done)

---

<a name="0-mental-model"></a>
## 0. Mental Model

The system is a **pipeline**, not a chatbot. A user posts one idea string. Four specialized agents pass work down a chain. The last agent emits a **structured, schema-validated JSON report**. FastAPI wraps the pipeline behind one endpoint.

```
                                  ┌──────────────────────────────────────────┐
  POST /analyze   ──►  FastAPI    │              Orchestrator                │
  { "idea": ... }     (validate)  │   if LLM key present → CrewAI pipeline   │ ──► FeasibilityReport (JSON)
                                  │   else              → Mock engine        │
                                  └──────────────────────────────────────────┘
                                                  │
                  Research ─► Market Analyst ─► Risk Analyst ─► Strategy/Decision
                   (search       (demand,         (tech, cost,      (synthesize,
                    tool)         competitors)      saturation)       build/don't)
```

Three layers, strictly separated:
- **API layer** (`app/api`) — HTTP, validation, error mapping. Knows nothing about CrewAI.
- **Orchestration layer** (`app/core`) — decides *real crew vs mock*, runs it, returns a `FeasibilityReport`. The only place that imports CrewAI.
- **Domain layer** (`app/agents`, `app/tasks`, `app/tools`, `app/schemas`) — the building blocks.

If you can draw that diagram on a whiteboard and explain why each box exists, you've already won half the interview.

---

<a name="1-the-golden-rule"></a>
## 1. The Project's Core Principles

> **Production-grade AI engineering, not just a wrapper.**

Three principles drive every decision:

1. **Multi-model cost optimization:** Different agents use different models — cheap models for research/extraction, powerful models for synthesis. This shows you think about production cost, not just "it works."
2. **AI ecosystem interoperability:** The pipeline is exposed as an MCP server, making it callable from Claude Desktop, Cursor, or any MCP client. It's not a silo — it's a composable tool.
3. **Observability:** Every agent call, tool invocation, and token count is traced via LangFuse. You can't run AI in production without knowing what's happening inside.

The mock engine exists as a lightweight testing utility — it keeps CI fast, free, and deterministic. But the headline features are the real AI capabilities.

Say this out loud in the interview: *"I built it with production AI in mind — multi-model routing for cost, MCP for ecosystem integration, and LangFuse tracing for observability. The agents aren't a black box; I can trace every decision."*

---

<a name="2-tech-decisions"></a>
## 2. Tech Decisions & Trade-offs (interview ammo)

Memorize the *reasoning*, not just the choice. Interviewers probe "why not X".

### Why CrewAI (vs LangGraph / AutoGen / raw API calls)

| Framework | Strength | Why not (for this) |
|---|---|---|
| **CrewAI** ✅ | Role-based mental model (Agent/Task/Crew/Process) maps 1:1 to "a team of analysts". Fastest idea→working pipeline. Standalone, lean, model-agnostic via LiteLLM. | Less fine-grained than graph control — fine here, the flow is linear. |
| LangGraph | Graph/state-machine control, great for cycles & branching. | Overkill for a strictly sequential pipeline; more boilerplate to show the same thing. |
| AutoGen | Strong conversational multi-agent, code-exec. | Conversation-centric; harder to get clean structured output and a deterministic pipeline. |
| Raw LLM calls | Total control, no dependency. | You lose the *story*. The whole point is demonstrating **multi-agent orchestration**. |

**Punchline:** "The task is a deterministic, sequential analyst pipeline with structured output — CrewAI's sequential `Process` is the most direct, readable expression of that. I'd reach for LangGraph the moment I needed loops or conditional routing."

### Why `Process.sequential` (not hierarchical)

- Sequential = a fixed assembly line; the output of each task is `context` for the next. Predictable, cheap, easy to debug.
- Hierarchical adds a manager LLM that delegates dynamically — powerful but **burns far more tokens**, can loop, and adds nondeterminism you don't want in a report generator.
- "I start sequential because the pipeline order is known. Hierarchical is the upgrade when task order isn't predetermined." (This is literally CrewAI's own guidance — quoting it shows you read the docs.)

### Why structured output via `output_pydantic`

- You attach a Pydantic model to the **final** task. CrewAI instructs the LLM to emit JSON matching that schema and **auto-retries with a corrective prompt** if it doesn't validate. You then read `result.pydantic` as a typed object.
- Alternative (free-text + regex parsing) is fragile. Naming `output_pydantic` shows you know the framework's structured-output story.

### Why FastAPI

- Async-native, Pydantic validation built in, auto OpenAPI docs at `/docs` (great for a live demo), production-grade with `uvicorn`.

### Why the orchestrator indirection

- The API never imports CrewAI. The orchestrator picks engine. This is the Strategy pattern: two engines (`MockEngine`, `CrewEngine`) behind one `analyze(idea) -> FeasibilityReport` interface. Swappable, testable, mockable.

---

<a name="3-milestones"></a>
## 3. Milestones

Each milestone has: **Goal · Build · Steps · Test (automated + manual) · Definition of Done · Interview notes / gotchas.**

Branch per milestone (`git checkout -b m2-mock-engine`), merge to `main` when DoD is green. Your commit history *is* part of the portfolio — it shows incremental, tested delivery.

---

<a name="m0"></a>
### M0 — Scaffold & Health  *(~30–45 min)*

**Goal:** A repo that boots a FastAPI server and answers `/health`. Nothing else. Prove the skeleton breathes.

**Build:**
```
ai-product-research-analyzer/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app factory + include routers
│   ├── config.py          # Settings via pydantic-settings (reads env)
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py      # GET /health  (and later POST /analyze)
│   ├── core/ tasks/ agents/ tools/ schemas/ utils/   # empty __init__.py for now
├── tests/ __init__.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md   (stub)
```

**Steps (exact, boring, do them all):**
1. `python --version` → must be **>=3.10 and <3.14** (CrewAI constraint). If not, install via pyenv.
2. `python -m venv .venv && source .venv/bin/activate` (Windows: `.venv\Scripts\activate`).
3. Create `requirements.txt` with at least:
   ```
   fastapi>=0.115
   uvicorn[standard]>=0.30
   pydantic>=2.7
   pydantic-settings>=2.3
   python-dotenv>=1.0
   httpx>=0.27
   # added in later milestones:
   # crewai>=0.86
   # crewai-tools>=0.17
   # dev:
   pytest>=8.0
   pytest-asyncio>=0.23
   ```
4. `pip install -r requirements.txt`.
5. `config.py`: a `Settings(BaseSettings)` with fields `app_name`, `model_name` (default e.g. `"gpt-4o-mini"`), `openai_api_key: str | None`, `anthropic_api_key: str | None`, `serper_api_key: str | None`, `tavily_api_key: str | None`, `use_real_crew: bool = False`, `request_timeout_seconds: int = 120`. Add a cached `get_settings()` (`functools.lru_cache`).
6. `main.py`: `create_app()` factory, mount router, return app. Bottom: `app = create_app()`.
7. `routes.py`: `GET /health` → `{"status": "ok", "engine": "<mock|crew>"}`.
8. `.gitignore`: `.venv/`, `__pycache__/`, `.env`, `*.pyc`, `.pytest_cache/`.
9. `.env.example`: every env var with empty/placeholder values + comments. **Never commit a real `.env`.**

**Test:**
- *Manual:* `uvicorn app.main:app --reload` → open `http://127.0.0.1:8000/health` → `200 {"status":"ok",...}`. Open `/docs` → Swagger UI loads.
- *Automated:* `tests/test_health.py` using `fastapi.testclient.TestClient`: assert `GET /health` returns 200 and `status == "ok"`.

**Definition of Done:** server boots, `/health` 200, `/docs` renders, `pytest` green (1 test).

**Interview notes:**
- Why a `create_app()` factory? Testability + multiple configs (test vs prod) without import-time side effects.
- Why `pydantic-settings`/`lru_cache`? Centralized, validated, cached config; secrets come from env, never code. Name "12-factor config."

---

<a name="m1"></a>
### M1 — The Contract (schemas)  *(~30 min)*

**Goal:** Define the **request** and **report** Pydantic models *before* any logic. Contract-first. Everything downstream conforms to these.

**Build:** `app/schemas/report.py`
- `AnalyzeRequest`: `idea: str = Field(min_length=10, max_length=2000)`. Validation here is your first line of defense.
- `Competitor`: `name: str`, `description: str`, `differentiator: str | None`.
- `FeasibilityReport` (this is the deliverable shape required by the prompt):
  - `idea: str`
  - `market_overview: str`
  - `competitors: list[Competitor]`
  - `opportunities: list[str]`
  - `gaps: list[str]`
  - `technical_feasibility: str`
  - `risks: list[str]`
  - `recommendation: Literal["build", "dont_build", "build_with_caveats"]`
  - `confidence: float = Field(ge=0, le=1)`
  - `reasoning: str`
  - `mvp_suggestion: str | None`
  - `engine: Literal["mock", "crew"]`  ← provenance, so the response is honest about how it was generated
- `AnalyzeResponse` wrapping `report: FeasibilityReport` + `meta` (e.g. `duration_ms`, `model`).

**Steps:**
1. Write the models. Add `model_config = ConfigDict(extra="forbid")` to reject junk.
2. Give every field a `description=` — this doubles as your OpenAPI docs **and** as the schema CrewAI will target for structured output later. (Field descriptions literally guide the LLM. Free win.)

**Test:** `tests/test_schemas.py`
- Valid payload constructs `FeasibilityReport` OK.
- `idea` too short → `ValidationError`.
- Bad `recommendation` value → `ValidationError`.
- `confidence = 1.5` → `ValidationError`.

**Definition of Done:** models import cleanly; 4+ validation tests green.

**Interview notes:**
- "Contract-first means the mock, the crew, and the API all agree on one shape — I can swap the engine and clients never notice."
- Why `Literal` for recommendation? Compile-time-ish guarantee the report can only say one of three things — no free-text drift.
- The `engine` field is an honesty feature: the response tells you whether a real LLM or the fallback produced it.

---

<a name="m2"></a>
### M2 — Mock Engine (lightweight, testing utility)  *(~30–45 min)*

**Goal:** A lightweight, deterministic mock that returns a valid `FeasibilityReport` for testing and CI. This is **not** a headline feature — it's a testing utility that keeps your test suite fast, free, and keyless.

**Build:** `app/core/mock_engine.py`
- `class MockEngine:` with `def analyze(self, idea: str) -> FeasibilityReport:`.
- Simple deterministic report:
  - Seed Python's `random` with `hash(idea)` so the same idea always yields the same report.
  - Template basic fields referencing the idea.
  - Set `engine="mock"`, a fixed `confidence` (e.g. 0.55).

**Steps:**
1. Return a fully-populated `FeasibilityReport` with hardcoded but valid data.
2. Seed randomness for determinism — same idea → same report.
3. Keep it simple — this is a testing tool, not a demo feature.

**Test:** `tests/test_mock_engine.py`
- Output is a valid `FeasibilityReport` (Pydantic validates on construction).
- **Determinism:** `analyze(idea) == analyze(idea)` for the same idea.
- Every list field is non-empty; `recommendation` is one of the allowed literals.

**Definition of Done:** `MockEngine().analyze("...")` returns a valid report, deterministically; tests green.

**Interview notes:**
- "The mock keeps CI fast and keyless — I test wiring and schemas, not LLM content. It's a testing strategy, not a product feature."

---

<a name="m3"></a>
### M3 — API wired to Orchestrator  *(~45 min)*

**Goal:** `POST /analyze` returns a real `FeasibilityReport` end-to-end — using the mock engine. The HTTP surface is now fully functional.

**Build:**
- `app/core/orchestrator.py`: `class Orchestrator` with `analyze(idea) -> FeasibilityReport`. Logic: `if settings.use_real_crew and (has LLM key): use CrewEngine else: use MockEngine`. (CrewEngine is a stub returning mock for now, filled in M6.)
- `app/api/routes.py`: add `POST /analyze` → validate `AnalyzeRequest`, call orchestrator, wrap in `AnalyzeResponse`, return.

**Steps:**
1. Orchestrator selects engine, records `duration_ms`.
2. Route: `async def analyze(req: AnalyzeRequest)`. For now call orchestrator synchronously (we make it truly async in M7). Map known errors to HTTP (422 already handled by Pydantic; 500 for unexpected; 504 reserved for timeout in M7).
3. Add a structured logger (`app/utils/logging.py`) logging each request: idea length, engine used, duration. **Never log secrets.**

**Test:** `tests/test_api_analyze.py`
- `POST /analyze {"idea": "Should I build an AI study assistant..."}` → 200, body matches `AnalyzeResponse` schema, `report.engine == "mock"`.
- `POST /analyze {"idea": "hi"}` → 422 (too short).
- `POST /analyze {}` → 422.
- Response time logged.

**Definition of Done:** live `curl` against `/analyze` returns a valid report; 3+ API tests green. **You can now demo the whole product with zero keys.**

**Interview notes:**
- "By M3 the product is fully demoable. Real agents are an internal upgrade behind a stable HTTP contract — clients don't change."
- Strategy pattern call-out: orchestrator chooses engine; both implement the same method signature.

---

<a name="m4"></a>
### M4 — Tools Layer (search + mock fallback)  *(~1 hr)*

**Goal:** A web-search tool the Research agent can call — backed by Serper **or** Tavily, with a **mock fallback** when no key is set. Demonstrates the CrewAI custom-tool API.

**Build:** `app/tools/search_tool.py`
- Pydantic input schema:
  ```python
  class SearchInput(BaseModel):
      query: str = Field(..., description="Search query for market/competitor research")
      max_results: int = Field(5, ge=1, le=10)
  ```
- `class WebSearchTool(BaseTool)`:
  ```python
  from crewai.tools import BaseTool
  class WebSearchTool(BaseTool):
      name: str = "web_search"
      description: str = "Search the web for market data, competitors, and demand signals."
      args_schema: Type[BaseModel] = SearchInput
      def _run(self, query: str, max_results: int = 5) -> str:
          # 1. if SERPER_API_KEY -> call Serper via httpx
          # 2. elif TAVILY_API_KEY -> call Tavily via httpx
          # 3. else -> return deterministic mock results (formatted string)
          # On any HTTP error: return a clear error string (NOT raise) so the agent can recover.
  ```
- `app/tools/mock_search.py`: deterministic fake SERP results keyed off the query.

**Steps:**
1. Implement Serper call (`POST https://google.serper.dev/search`, header `X-API-KEY`).
2. Implement Tavily call (`POST https://api.tavily.com/search`).
3. Implement mock fallback returning a few plausible result snippets as a formatted string.
4. **Return errors as strings, never raise** — CrewAI best practice: the agent reads the error and retries/adapts. Raising kills the run.

**Test:** `tests/test_search_tool.py` (no real network — monkeypatch/mocked httpx)
- No keys set → returns mock results string, non-empty.
- Serper path: monkeypatch httpx to a canned 200 JSON → tool returns parsed snippets.
- HTTP 500 from provider → tool returns an error *string* (not an exception).
- `SearchInput` rejects `max_results=99`.

**Definition of Done:** tool callable standalone (`WebSearchTool()._run("AI tutors")`) returns useful text in all three modes; tests green.

**Interview notes:**
- "One tool, three backends, graceful fallback. Tools return error strings instead of raising — that's the CrewAI convention so the agent can recover instead of crashing the crew."
- Single-responsibility: a search tool searches; it doesn't summarize. The agent chains reasoning. (Quote the docs' "each tool does one thing".)
- Why `httpx` not the provider SDKs? Fewer deps, full control, easy to mock in tests.

---

<a name="m5"></a>
### M5 — Agents + Multi-Model Routing  *(~1.5 hr)*

**Goal:** Define the four agents with crisp roles, goals, backstories, and tool assignments — **each with its own model** based on task complexity. This is where cost optimization lives.

**Build:** `app/agents/agents.py` — a factory `build_agents(settings, tools) -> dict[str, Agent]`.

| Agent | role | goal (templated with `{idea}`) | tools | model | allow_delegation |
|---|---|---|---|---|---|
| Research | "Senior Product Researcher" | Gather demand signals, competitors, and context for `{idea}` | `[WebSearchTool()]` | cheap (e.g. `gpt-4o-mini`, `claude-3-haiku`) | `False` |
| Market Analyst | "Market Analyst" | Assess demand, audience, competitive landscape; identify similar products | none | cheap | `False` |
| Risk Analyst | "Risk & Feasibility Analyst" | Evaluate technical risk, market saturation, cost/complexity, feasibility constraints | none | cheap | `False` |
| Strategy/Decision | "Head of Strategy" | Synthesize everything into build / don't-build with reasoning + MVP | none | strong (e.g. `gpt-4o`, `claude-sonnet`) | `False` |

```python
from crewai import Agent, LLM

def build_llm(model_name: str, temperature: float = 0.3) -> LLM:
    return LLM(model=model_name, temperature=temperature)

def build_agents(settings, tools) -> dict[str, Agent]:
    cheap_llm = build_llm(settings.cheap_model_name)      # e.g. gpt-4o-mini
    strong_llm = build_llm(settings.strong_model_name)     # e.g. gpt-4o

    researcher = Agent(
        role="Senior Product Researcher",
        goal="Find concrete demand signals, competitors, and context for: {idea}",
        backstory="You are meticulous and only trust evidence you can cite.",
        tools=[tools["web_search"]],
        llm=cheap_llm,         # ← cheap model: extraction, not reasoning
        allow_delegation=False,
        verbose=True,
    )
    # ... Market Analyst + Risk Analyst use cheap_llm
    # ... Strategy uses strong_llm
    return {"research": researcher, "market": market, "risk": risk, "strategy": strategy}
```

**Config additions** (`app/config.py`):
```python
cheap_model_name: str = "gpt-4o-mini"       # research, extraction
strong_model_name: str = "gpt-4o"           # synthesis, final decision
```

**Steps:**
1. Add `cheap_model_name` and `strong_model_name` to `Settings`.
2. Factory builds agents with separate LLM instances — cheap for Research/Market/Risk, strong for Strategy.
3. Set `allow_delegation=False` on all (prevents delegation loops).
4. Backstories enforce responsibility boundaries.

**Test:** `tests/test_agents.py`
- `build_agents(...)` returns 4 `Agent` instances with expected `role`s.
- Researcher has exactly one tool; others have none.
- Research/Market/Risk agents use the cheap model; Strategy uses the strong model.
- No network/LLM call happens at construction.

**Definition of Done:** agents instantiate offline; roles/tools/models correct; tests green.

**Interview notes:**
- **The cost sentence:** "Not every agent needs GPT-4o. Research and extraction run on a cheap model; only the Strategy synthesis uses the expensive one. This cuts cost ~60% with no quality loss on the final recommendation — the reasoning-heavy work is the only thing that needs reasoning-heavy models."
- Why distinct roles/backstories? CrewAI's thesis: role + backstory boundaries reduce hallucination.
- Why `allow_delegation=False`? Prevents delegation ping-pong — a known token-burning failure mode.
- CrewAI is model-agnostic per-agent via LiteLLM — you can even mix providers (OpenAI for research, Anthropic for strategy).

---

<a name="m6"></a>
### M6 — Tasks & Crew (the real pipeline)  *(~1.5–2 hr)*

**Goal:** Wire the four tasks into a **sequential crew** where each task feeds the next via `context`, and the final task emits a schema-validated `FeasibilityReport`. This is the headline feature.

**Build:**
- `app/tasks/tasks.py`: `build_tasks(agents) -> list[Task]`.
  ```python
  research_task = Task(
      description="Research the idea: {idea}. Use web_search. Output raw findings.",
      expected_output="Bullet list of demand signals, competitors, and sources.",
      agent=agents["research"],
  )
  market_task = Task(
      description="Analyze demand, audience, competitors for {idea}.",
      expected_output="Market overview + competitor list + opportunities/gaps.",
      agent=agents["market"],
      context=[research_task],          # ← depends on research
  )
  risk_task = Task(
      description="Evaluate technical, market, cost, and feasibility risks for {idea}.",
      expected_output="Categorized risk list with severity.",
      agent=agents["risk"],
      context=[research_task, market_task],
  )
  decision_task = Task(
      description="Synthesize all findings for {idea} into a final recommendation.",
      expected_output="A complete feasibility report.",
      agent=agents["strategy"],
      context=[research_task, market_task, risk_task],
      output_pydantic=FeasibilityReport,   # ← structured, validated, auto-retried
  )
  ```
- `app/core/crew_engine.py`: `class CrewEngine` with `analyze(idea) -> FeasibilityReport`:
  ```python
  crew = Crew(agents=[...], tasks=[...], process=Process.sequential, verbose=True)
  result = crew.kickoff(inputs={"idea": idea})
  report = result.pydantic            # typed FeasibilityReport
  report.engine = "crew"
  return report
  ```

**Steps:**
1. Build tasks; **the `context=[...]` chain is the dependency graph** — this is what makes it "multi-agent collaboration" and not four isolated calls. (Forgetting `context` is *the* #1 CrewAI beginner bug — name it.)
2. Only the final task gets `output_pydantic`.
3. CrewEngine reads `result.pydantic`; if it's `None` (rare), fall back to parsing `result.raw` or to the mock — never 500 on the user.
4. Stamp `engine="crew"` and real token usage from `result.token_usage` into `meta` (great demo detail).

**Test:** *(do not call a live LLM in CI)*
- `tests/test_tasks.py`: `build_tasks` returns 4 `Task`s; `decision_task.context` has length 3; `decision_task.output_pydantic is FeasibilityReport`.
- `tests/test_crew_engine.py`: monkeypatch `Crew.kickoff` to return a fake `CrewOutput` whose `.pydantic` is a valid `FeasibilityReport` → assert engine stamps `"crew"` and returns it. (You're testing *your wiring*, not the LLM.)
- **One** optional, *not-in-CI*, key-gated live smoke test (`@pytest.mark.live`, skipped without key) that actually kicks off with a cheap model and asserts a valid report. Run it manually before the interview so you can say "yes, I ran it end-to-end against a real model."

**Definition of Done:** with a real key + `USE_REAL_CREW=true`, `/analyze` produces a genuine 4-agent report; without keys it transparently uses mock; all non-live tests green.

**Interview notes:**
- **The money sentence:** "Tasks are chained with `context`, so each agent's output becomes the next agent's input — that's the dependency graph that makes this genuinely multi-agent rather than four parallel prompts. The final Strategy agent gets all three prior outputs as context and emits a Pydantic-validated report; CrewAI auto-retries if the JSON doesn't match the schema."
- Know `result.pydantic` vs `result.raw` vs `result.token_usage` cold.
- Know *why sequential*: the order is known and fixed (research → analyze → risk → decide).

---

<a name="m7"></a>
### M7 — Async, Timeouts, Graceful Degradation  *(~1 hr)*

**Goal:** Make the endpoint truly async and resilient. CrewAI's `kickoff` is **blocking** — running it directly in an async route would block the event loop. Fix that. Add timeouts and fallback.

**Build / change:**
- In the orchestrator's async path: `await asyncio.to_thread(engine.analyze, idea)` (offloads the blocking crew to a worker thread so the event loop stays free). *Alternative:* CrewAI exposes `kickoff_async` — mention you know it exists; `to_thread` keeps the mock and crew paths uniform.
- Wrap in `asyncio.wait_for(..., timeout=settings.request_timeout_seconds)`.
- On `TimeoutError` → either return 504 **or** degrade to mock with a `meta.degraded=true` flag (your call; degrading is the friendlier demo).
- On unexpected exception → log + 500 with a safe message (no stack trace to client).

**Steps:**
1. Make route `async def`; orchestrator exposes `async def analyze_async`.
2. Add timeout + try/except mapping.
3. Add a tiny middleware or dependency to attach `duration_ms` to every response.

**Test:** `tests/test_async.py`
- Concurrency: fire N concurrent `/analyze` requests (mock engine) via `httpx.AsyncClient` → all 200, total time ≈ not N× serial (proves non-blocking).
- Timeout: monkeypatch engine to `time.sleep(big)`, set timeout=1 → assert 504 or degraded mock.
- Exception: monkeypatch engine to raise → assert 500 + no leaked internals.

**Definition of Done:** concurrent requests don't serialize; timeout + error paths behave; tests green.

**Interview notes:**
- **Critical gotcha to volunteer:** "CrewAI's `kickoff` is synchronous and CPU/IO-bound on the LLM, so calling it directly in an async route blocks the whole event loop. I offload it with `asyncio.to_thread` and bound it with `asyncio.wait_for`." Saying this *unprompted* reads as senior.
- Degrade-to-mock vs 504: a product decision. Explain the trade-off (availability vs honesty) — there's no wrong answer if you can justify it.

---

<a name="m8"></a>
### M8 — MCP Server  *(~2–3 hr)*

**Goal:** Expose the analyzer as an **MCP (Model Context Protocol) server** so it's callable from Claude Desktop, Cursor, Windsurf, or any MCP-compatible client. This turns the project from "a FastAPI app" into "an AI-native tool in the ecosystem."

**Build:** `app/mcp/server.py`
- Use the `mcp` Python SDK to create an MCP server.
- Expose one tool: `analyze_idea(idea: str) -> str` that runs the orchestrator and returns the JSON report.
- The MCP server wraps the same orchestrator used by the API — one pipeline, two interfaces.

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("market-research-analyzer")

@server.tool()
async def analyze_idea(idea: str) -> str:
    """Analyze a product idea for market feasibility. Returns a structured report with market overview, competitors, risks, and a build/don't-build recommendation."""
    orchestrator = Orchestrator(get_settings())
    report = await orchestrator.analyze_async(idea)
    return report.model_dump_json(indent=2)
```

**Steps:**
1. Install `mcp` SDK.
2. Create the MCP server with the `analyze_idea` tool.
3. Add tool description that helps the LLM understand when to call it.
4. Add a `mcp_server.py` entry point for `mcp run` / stdio transport.
5. Test with Claude Desktop or MCP Inspector.

**Test:** `tests/test_mcp.py`
- MCP server instantiates without error.
- Tool is registered with correct name and description.
- Tool invocation returns a valid JSON string parseable as `FeasibilityReport`.

**Definition of Done:** `mcp dev app/mcp/server.py` starts; Claude Desktop or MCP Inspector can call `analyze_idea` and get a report; tests green.

**Interview notes:**
- **The ecosystem sentence:** "I exposed the pipeline as an MCP server — the same crew that runs behind the API is now callable from Claude Desktop, Cursor, or any MCP client. It's composable, not siloed."
- MCP is the standard Anthropic introduced for tool interoperability — naming it shows you're current.
- Same orchestrator, two transports (HTTP + MCP stdio) — clean separation of concerns.

---

<a name="m9"></a>
### M9 — Observability (LangFuse)  *(~1.5 hr)*

**Goal:** Instrument the pipeline with **LangFuse tracing** so every agent call, tool invocation, token count, and latency is captured and viewable in a dashboard. Production AI without observability is flying blind.

**Build:**
- Integrate LangFuse's callback handler with CrewAI.
- Every crew kickoff creates a trace with spans for each agent/task.
- Token usage, latency, and model info are captured per-span.

```python
from langfuse.callback import CallbackHandler

def analyze(self, idea: str) -> FeasibilityReport:
    langfuse_handler = CallbackHandler(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    crew = Crew(
        agents=[...], tasks=[...],
        process=Process.sequential,
        callbacks=[langfuse_handler],   # ← traces everything
    )
    result = crew.kickoff(inputs={"idea": idea})
    # ...
```

**Config additions** (`app/config.py`):
```python
langfuse_public_key: str | None = None
langfuse_secret_key: str | None = None
langfuse_host: str = "https://cloud.langfuse.com"
```

**Steps:**
1. Add LangFuse config to Settings (optional — tracing is disabled if keys aren't set).
2. Create a callback handler factory that returns the handler or `None`.
3. Attach to Crew only when LangFuse is configured.
4. Add trace metadata: idea hash, engine type, model names.
5. Test with LangFuse cloud (free tier) or self-hosted.

**Test:** `tests/test_observability.py`
- When LangFuse keys are not set, no callback is attached (no error).
- When keys are set, callback handler is created with correct config.
- Crew receives the callback in its config.

**Definition of Done:** with LangFuse configured, a crew run produces a visible trace in the LangFuse dashboard showing all 4 agents, tool calls, and token usage; without LangFuse keys, the pipeline runs normally with no errors.

**Interview notes:**
- **The production sentence:** "You can't run AI in production without knowing what's happening inside. I instrumented the pipeline with LangFuse — every agent call, tool invocation, and token count is traced. When a report is bad, I can trace exactly which agent went wrong and why."
- LangFuse is open-source and self-hostable — no vendor lock-in.
- Graceful degradation: no LangFuse keys → no tracing, no errors. Same pattern as the rest of the project.

---

<a name="m10"></a>
### M10 — Tests, Lint, Types, CI  *(~1 hr)*

**Goal:** Green, fast, deterministic CI. This is the difference between "a script" and "engineering."

**Build:**
- `pytest.ini` / `pyproject.toml` test config; `pytest-asyncio` mode.
- `ruff` for lint+format, `mypy` for types (or `pyright`).
- `.github/workflows/ci.yml`: on push/PR → install, `ruff check`, `mypy app`, `pytest -m "not live"`.
- `Makefile`: `make install`, `make run`, `make test`, `make lint`, `make fmt`, `make docker`.

**Steps:**
1. Mark the live test `@pytest.mark.live`; CI runs `-m "not live"` so **CI needs no API keys**.
2. Target ~80%+ coverage of the non-LLM code (schemas, mock, tools fallback, orchestrator routing, API).
3. Add a coverage badge to the README later.

**Test:** the test suite *is* the deliverable. Run `make test` → all green in seconds, no network.

**Definition of Done:** `ruff`, `mypy`, `pytest` all green locally and in GitHub Actions; live tests excluded from CI.

**Interview notes:**
- "CI is keyless and deterministic because everything testable runs against the mock and mocked HTTP. The one live test is opt-in."
- Be ready to explain *what you don't test*: you don't assert LLM *content* (nondeterministic); you assert *your wiring, schemas, and fallbacks*.

---

<a name="m11"></a>
### M11 — Docker  *(~45 min)*

**Goal:** `docker compose up` → working API, no local Python needed. Production-ish uvicorn.

**Build:**
- `Dockerfile` (multi-stage, slim):
  - Base `python:3.12-slim`.
  - Stage 1: install deps into a venv/wheels.
  - Stage 2: copy app + deps, create non-root user, expose 8000.
  - Healthcheck hitting `/health`.
  - CMD: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2`.
- `.dockerignore`: `.venv`, `.git`, `__pycache__`, `tests`, `.env`.
- `docker-compose.yml`: one `api` service, `ports: 8000:8000`, `env_file: .env`, `restart: unless-stopped`, healthcheck.

**Steps:**
1. Multi-stage build to keep the image small.
2. **Run as non-root** (`USER appuser`) — security.
3. Env vars injected via `env_file`/compose, **never baked into the image**.

**Test:**
- `docker build -t analyzer .` succeeds.
- `docker compose up` → `curl localhost:8000/health` 200.
- Container runs as non-root.

**Definition of Done:** `docker compose up` → live API demo.

**Interview notes:**
- Multi-stage = small image. Non-root = least privilege. Secrets via env = 12-factor. Healthcheck = orchestrator-friendly.

---

<a name="m12"></a>
### M12 — Docs, Diagram, Demo Script  *(~1 hr)*

**Goal:** README that gets you hired. The repo is judged in 60 seconds before anyone reads code.

**Build — README sections (in order):**
1. **One-liner + hero line:** "Multi-agent (CrewAI) feasibility analyzer with multi-model routing, MCP integration, and LangFuse observability."
2. **Architecture diagram** (Mermaid renders on GitHub).
3. **Quickstart:** `docker compose up` → `curl` example.
4. **The agent pipeline** (table of 4 agents + models + what each produces).
5. **Headline features:** MCP server, multi-model routing, LangFuse tracing.
6. **API reference:** `POST /analyze`, `GET /health`. Link to `/docs`.
7. **Design decisions** (CrewAI vs alternatives, sequential vs hierarchical, multi-model routing, MCP).
8. **Running with real LLMs:** env vars, model config.
9. **Testing:** `make test`, the keyless-CI story.
10. **Project structure** (the tree).

**Definition of Done:** a stranger can clone, run, and understand the system in under 5 minutes.

---

<a name="4-pitch"></a>
## 4. The 2–3 Minute Interview Pitch (memorize the shape)

> "I built an **AI Product Research & Feasibility Analyzer**. You POST a one-line product idea and get back a structured JSON report — market overview, competitors, opportunities and gaps, technical feasibility, risks, and a final build / don't-build recommendation with reasoning and an MVP suggestion.
>
> Under the hood it's a **CrewAI multi-agent pipeline**: a Research agent gathers signals using a web-search tool, a Market Analyst assesses demand and competitors, a Risk Analyst evaluates technical and market risk, and a Strategy agent synthesizes everything into the final call. The tasks are chained with CrewAI's `context` mechanism — a real dependency graph, not four isolated prompts. The final report is **Pydantic-schema-validated**, with auto-retry if the model's JSON doesn't conform.
>
> Three things I'm most proud of:
>
> **Multi-model routing** — not every agent needs GPT-4o. Research and extraction run on a cheap model; only the Strategy synthesis uses the expensive one. Cuts cost ~60%.
>
> **MCP server** — the same pipeline is exposed as an MCP tool, so you can call it from Claude Desktop or Cursor. It's not a silo; it's composable.
>
> **LangFuse observability** — every agent call, tool invocation, and token count is traced. When a report is bad, I can show you exactly which agent went wrong.
>
> It's wrapped in FastAPI, Dockerized with multi-stage builds, and the test suite is fast and keyless because of a lightweight mock engine. Want me to show it running?"

Then open `/docs`, fire `/analyze`, show the JSON, open the LangFuse trace, and point at the per-agent spans.

---

<a name="5-questions"></a>
## 5. The Kill-Shot Questions (and your answers)

**Q: Is this actually multi-agent, or four prompts in a trench coat?**
A: Multi-agent. The agents have distinct roles/tools and the tasks are linked with `context=[...]`, so each agent's output is the next one's input. The Strategy agent receives all three prior outputs. Remove the context links and it *would* be four isolated prompts — that's exactly the #1 CrewAI beginner bug, and avoiding it is the point.

**Q: Why CrewAI over LangGraph/AutoGen?**
A: The workload is a known, sequential analyst pipeline with structured output. CrewAI's role-based sequential `Process` expresses that most directly and readably. I'd switch to LangGraph the moment I needed cycles or conditional branching, or to CrewAI Flows for event-driven control.

**Q: How do you test an LLM app — the output is nondeterministic?**
A: I don't assert LLM *content*. I assert wiring, schemas, and fallbacks against a deterministic mock engine and mocked HTTP. CI is keyless and runs in seconds. There's one opt-in, key-gated live smoke test I run manually before shipping.

**Q: What happens if the LLM returns malformed JSON?**
A: `output_pydantic` makes CrewAI re-prompt to fix the schema automatically. If `result.pydantic` still comes back empty, the engine falls back to parsing `result.raw` — the user never gets a 500 for a model formatting hiccup.

**Q: CrewAI's kickoff is blocking — doesn't that wreck FastAPI's concurrency?**
A: It would if called directly. I offload it with `asyncio.to_thread` and bound it with `asyncio.wait_for`, so the event loop stays free and slow runs time out gracefully.

**Q: How do you handle cost?**
A: Multi-model routing. Research and extraction agents run on `gpt-4o-mini` (cheap, fast). Only the Strategy agent gets the expensive model for synthesis. Sequential process keeps token use predictable — no manager overhead. I also capture token usage per-agent via LangFuse so I can track cost per request.

**Q: Why MCP?**
A: MCP is becoming the standard for AI tool interoperability. Exposing the pipeline as an MCP server means it's callable from Claude Desktop, Cursor, or any MCP client — not just via my REST API. Same orchestrator, two transports. It shows the system is composable, not siloed.

**Q: How do you debug a bad report in production?**
A: LangFuse tracing. Every crew run creates a trace with spans for each agent, tool call, and LLM invocation. I can see exactly which agent produced what, how many tokens it used, and where the reasoning went wrong. Without this, multi-agent systems are a black box.

**Q: How do you stop agents from looping / burning tokens?**
A: `allow_delegation=False` on executors, sequential process, low temperature, tight task `expected_output`, and a request timeout as a hard backstop.

**Q: Where are secrets?**
A: Env only, via `pydantic-settings`, injected through Docker `env_file`. Never in code, never in the image, never logged. `.env` is gitignored; `.env.example` documents the vars.

**Q: What's the weakest part / what would you do with another week?**
A: (Pick one, be honest.) An evaluation/judge agent for quality gating, SSE streaming for real-time progress, and idea-hash caching for repeat queries. Knowing the gaps is the point.

---

<a name="6-failure-modes"></a>
## 6. Failure Modes You Must Be Able to Name

Naming these unprompted is what makes you look senior:
1. **Forgotten `context` links** → agents work in isolation (the classic bug). Mitigated by explicit `context=[...]` + a test asserting `decision_task.context` length.
2. **Delegation loops** (hierarchical / `allow_delegation=True`) → infinite ping-pong, token bonfire. Mitigated: sequential + delegation off.
3. **Blocking the event loop** with sync `kickoff`. Mitigated: `asyncio.to_thread`.
4. **Schema drift** in LLM JSON. Mitigated: `output_pydantic` auto-retry + fallback parsing.
5. **Provider outage / missing key.** Mitigated: tool returns error strings (agent recovers) + mock engine fallback for testing.
6. **Runaway latency.** Mitigated: `asyncio.wait_for` timeout → 504 or degrade.
7. **Secret leakage.** Mitigated: env-only config, non-root container, no secrets in logs.
8. **Cost explosion from using expensive models for simple tasks.** Mitigated: multi-model routing — cheap models for extraction, expensive only for synthesis.
9. **Black-box multi-agent debugging.** Mitigated: LangFuse tracing with per-agent spans.

---

<a name="7-done"></a>
## 7. Definition of "Done Done"

You're interview-ready when **all** of these are true:
- [ ] `git clone && docker compose up` → `/analyze` returns a valid report.
- [ ] Real 4-agent crew produces a schema-valid report with multi-model routing (you've run it live at least once).
- [ ] MCP server is callable from Claude Desktop or MCP Inspector.
- [ ] LangFuse trace shows all 4 agents with token usage.
- [ ] `make test` green in seconds, keyless; GitHub Actions green.
- [ ] README has the architecture diagram, headline features, and design-decisions section.
- [ ] You can draw the pipeline on a whiteboard and explain every box.
- [ ] You can answer every question in §5 without hesitating.
- [ ] You can say the §4 pitch in under 3 minutes and then demo it live.

---

### Suggested 3-Day Schedule

**Day 1:** M0 ✅ → M1 ✅ → M2 → M3 (fully demoable via API by end of day) → M4.
**Day 2:** M5 (agents + multi-model routing) → M6 (real crew) → M7 (async/timeouts).
**Day 3:** M8 (MCP server) → M9 (LangFuse) → M10 (CI) → M11 (Docker) → M12 (docs).

If Day 3 runs short, **prioritize M10+M11+M12** over polishing M8/M9 — a tested, dockerized, documented system beats a half-finished feature.

Now go be the demon. 🔱

