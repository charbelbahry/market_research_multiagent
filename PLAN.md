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
  - [M2 — Mock Engine (the spine)](#m2)
  - [M3 — API wired to orchestrator](#m3)
  - [M4 — Tools layer (search + mock)](#m4)
  - [M5 — Agents](#m5)
  - [M6 — Tasks & Crew (the real pipeline)](#m6)
  - [M7 — Async, timeouts, graceful degradation](#m7)
  - [M8 — Tests, lint, types, CI](#m8)
  - [M9 — Docker](#m9)
  - [M10 — Docs, diagram, demo script](#m10)
  - [M11 — Extensions (optional, but they impress)](#m11)
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
## 1. The Golden Rule of This Project

> **It must run with zero API keys.**

This single constraint is your best design decision and your single best talking point. A `MockEngine` produces a realistic, deterministic, idea-aware report with no LLM and no network. Consequences:

- The interviewer can `git clone && docker compose up` and hit `/analyze` **live, in the room**, on free wifi, no keys. Most candidates' projects die at "well, you'd need to add your OpenAI key…". Yours does not.
- Your test suite is **fast, deterministic, and free** because tests run against the mock, never a live LLM.
- Real CrewAI is an *upgrade path*, not a dependency. You flip an env var.

Say this out loud in the interview: *"I designed it contract-first with a deterministic fallback so the system is demoable and testable without any paid API, and the real multi-agent crew is a drop-in behind the same interface."* That sentence alone signals senior thinking.

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
### M2 — Mock Engine (the spine)  *(~1–1.5 hr)*

**Goal:** Produce a **valid, deterministic, idea-aware `FeasibilityReport` with no LLM, no network.** This is the most important milestone — everything else demos on top of it.

**Build:** `app/core/mock_engine.py`
- `class MockEngine:` with `def analyze(self, idea: str) -> FeasibilityReport:`.
- Lightweight, deterministic "intelligence":
  - Extract a topic phrase from the idea (simple keyword heuristic — strip stopwords, grab nouns/the longest content phrase).
  - Seed Python's `random` with `hash(idea)` so the *same idea always yields the same report* (deterministic = testable + honest).
  - Template the report fields so they reference the extracted topic (e.g. market_overview mentions the domain, competitors are plausibly generated, recommendation derived from a couple of toy heuristics like idea length / presence of words like "AI", "marketplace", etc.).
  - Set `engine="mock"`, a fixed `confidence` (e.g. 0.55, honestly mid).

**Steps:**
1. Implement topic extraction in `app/utils/text.py` (`extract_topic(idea) -> str`). Keep it dumb but reasonable.
2. Implement deterministic templating. Make at least the recommendation depend on input so the demo isn't obviously canned.
3. Return a fully-populated `FeasibilityReport`.

**Test:** `tests/test_mock_engine.py`
- Output is a valid `FeasibilityReport` (Pydantic validates on construction).
- **Determinism:** `analyze(idea) == analyze(idea)` for the same idea (compare `.model_dump()`).
- **Idea-awareness:** two clearly different ideas produce different `market_overview` / `recommendation` (not identical blobs).
- Every list field is non-empty; `recommendation` is one of the allowed literals.

**Definition of Done:** `MockEngine().analyze("...")` returns a valid report, deterministically, referencing the idea; tests green.

**Interview notes:**
- "The mock is deterministic by seeding on the idea hash — so it's reproducible and unit-testable, and it's honest: confidence is mid and the `engine` field says `mock`."
- Gotcha to mention: you deliberately did **not** make it pretend to be the LLM. It's a labeled fallback, not a fake.

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
### M5 — Agents  *(~45 min)*

**Goal:** Define the four agents with crisp roles, goals, backstories, and tool assignments. **No crew yet** — just instantiable, configurable agents.

**Build:** `app/agents/agents.py` — a factory `build_agents(llm, tools) -> dict[str, Agent]`.

| Agent | role | goal (templated with `{idea}`) | tools | allow_delegation |
|---|---|---|---|---|
| Research | "Senior Product Researcher" | Gather demand signals, competitors, and context for `{idea}` | `[WebSearchTool()]` | `False` |
| Market Analyst | "Market Analyst" | Assess demand, audience, competitive landscape; identify similar products | none (reasons over research output) | `False` |
| Risk Analyst | "Risk & Feasibility Analyst" | Evaluate technical risk, market saturation, cost/complexity, feasibility constraints | none | `False` |
| Strategy/Decision | "Head of Strategy" | Synthesize everything into build / don't-build with reasoning + MVP | none | `False` |

```python
from crewai import Agent, LLM

def build_llm(settings) -> LLM:
    # model-agnostic via LiteLLM; choose model + key from settings
    return LLM(model=settings.model_name, temperature=0.3)

researcher = Agent(
    role="Senior Product Researcher",
    goal="Find concrete demand signals, competitors, and context for: {idea}",
    backstory="You are meticulous and only trust evidence you can cite.",
    tools=[WebSearchTool()],
    llm=llm,
    allow_delegation=False,
    verbose=True,
)
```

**Steps:**
1. Factory builds all four with shared `llm`.
2. Set `allow_delegation=False` on all (lower-level executors shouldn't delegate — prevents delegation loops; quote this).
3. Backstories enforce responsibility boundaries (reduces hallucination — quote the docs).

**Test:** `tests/test_agents.py`
- `build_agents(...)` returns 4 `Agent` instances with expected `role`s.
- Researcher has exactly one tool; others have none.
- No network/LLM call happens at construction (agents are inert until kickoff).

**Definition of Done:** agents instantiate offline; roles/tools correct; tests green.

**Interview notes:**
- Why distinct roles/backstories? CrewAI's whole thesis: role + backstory boundaries reduce "disorganized emergence" and hallucination.
- Why `allow_delegation=False`? Executors that delegate can ping-pong tasks forever and torch your token bill. Known failure mode — naming it shows real experience.
- `temperature=0.3`: report generation wants consistency over creativity.

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
### M8 — Tests, Lint, Types, CI  *(~1 hr)*

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
- "CI is keyless and deterministic because everything testable runs against the mock and mocked HTTP. The one live test is opt-in." This directly answers "how do you test LLM apps?" — a question you *will* get.
- Be ready to explain *what you don't test*: you don't assert LLM *content* (nondeterministic); you assert *your wiring, schemas, and fallbacks*.

---

<a name="m9"></a>
### M9 — Docker  *(~45 min)*

**Goal:** `docker compose up` → working API, no local Python needed. Production-ish uvicorn.

**Build:**
- `Dockerfile` (multi-stage, slim):
  - Base `python:3.12-slim`.
  - Stage 1: install deps into a venv/wheels.
  - Stage 2: copy app + deps, create non-root user, expose 8000.
  - Healthcheck hitting `/health`.
  - CMD: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2` (or gunicorn+uvicorn workers for real prod — mention you know the difference).
- `.dockerignore`: `.venv`, `.git`, `__pycache__`, `tests`, `.env`.
- `docker-compose.yml`: one `api` service, `ports: 8000:8000`, `env_file: .env`, `restart: unless-stopped`, healthcheck.

**Steps:**
1. Multi-stage build to keep the image small (don't ship build tools).
2. **Run as non-root** (`USER appuser`) — security; interviewers notice.
3. Env vars (`OPENAI_API_KEY`, etc.) injected via `env_file`/compose, **never baked into the image**.
4. Default `USE_REAL_CREW=false` so the container demos out-of-the-box with mock.

**Test:**
- `docker build -t analyzer .` succeeds.
- `docker compose up` → `curl localhost:8000/health` 200 → `curl -X POST .../analyze` returns a mock report.
- `docker image inspect` size is reasonable (slim). Container runs as non-root (`docker exec ... whoami` ≠ root).

**Definition of Done:** clean machine, only Docker installed, `docker compose up` → live demo of `/analyze`.

**Interview notes:**
- Multi-stage = small image + no build tools in prod. Non-root = least privilege. Secrets via env = 12-factor. Healthcheck = orchestrator-friendly.
- "Image defaults to mock so it's instantly demoable; flip one env var + add a key to enable the real crew."

---

<a name="m10"></a>
### M10 — Docs, Diagram, Demo Script  *(~1 hr)*

**Goal:** README that gets you hired. The repo is judged in 60 seconds before anyone reads code — make those 60 seconds land.

**Build — README sections (in order):**
1. **One-liner + hero line:** "Multi-agent (CrewAI) feasibility analyzer that turns a product idea into a structured build/don't-build report — runs fully offline with a deterministic fallback."
2. **Architecture diagram** (the ASCII one from §0, or a Mermaid diagram — Mermaid renders on GitHub).
3. **Quickstart:** `docker compose up` → `curl` example with sample request/response JSON.
4. **The agent pipeline** (table of 4 agents + what each produces).
5. **API reference:** `POST /analyze` request/response schema, `GET /health`. Link to `/docs`.
6. **Design decisions** (lift from §2 — CrewAI vs alternatives, sequential vs hierarchical, mock fallback, structured output). *This section is what separates you.*
7. **Running with real LLMs:** env vars, `USE_REAL_CREW=true`.
8. **Testing:** `make test`, the keyless-CI story.
9. **Extensions / roadmap** (M11).
10. **Project structure** (the tree).

**Steps:**
1. Include a **real captured sample response** (run the mock, paste the JSON). Concrete > abstract.
2. Add badges: CI passing, Python version, license (MIT).
3. Add a `/docs` screenshot.
4. Write a `DEMO.md` with your literal click-path for the interview.

**Definition of Done:** a stranger can clone, run, and understand the system in under 5 minutes from the README alone.

**Interview notes:**
- The README's "Design decisions" section pre-answers half the interview. Interviewers love candidates who document trade-offs.

---

<a name="m11"></a>
### M11 — Extensions (optional, but they impress)  *(time-boxed)*

Don't build all of these. Build **one** if you have time, and be able to *describe* the rest. Describing a credible roadmap is itself a senior signal.

| Extension | What it adds | How you'd do it | Talking point |
|---|---|---|---|
| **Memory** | Crew remembers prior analyses | Enable CrewAI's `memory=True` (short-term/entity/long-term) or persist reports in SQLite/Redis | "CrewAI ships layered memory; I'd add long-term memory to compare an idea against past analyses." |
| **Refinement loop** | Decision agent can send work back if confidence is low | Switch from a Crew to a **CrewAI Flow** with `@router` conditional re-run | "Flows give event-driven control + conditional routing — the natural home for a 'redo if confidence < 0.6' loop." |
| **Evaluation agent** | A 5th agent scores the report's quality | Add an Eval task with a rubric + `output_pydantic` score | "An LLM-as-judge gate before returning — catches low-quality reports." |
| **UI dashboard** | Submit ideas, view reports | Tiny React/HTMX front-end hitting `/analyze` | "Thin client over the same contract." |
| **Caching** | Same idea → instant cached report | Hash idea → Redis/in-memory cache | "Cuts cost & latency; the deterministic mock already behaves like a cache in spirit." |
| **Streaming** | Stream agent progress | SSE endpoint emitting task-completion events | "Better UX for a 30–90s pipeline." |

---

<a name="4-pitch"></a>
## 4. The 2–3 Minute Interview Pitch (memorize the shape)

> "I built an **AI Product Research & Feasibility Analyzer**. You POST a one-line product idea and get back a structured JSON report — market overview, competitors, opportunities and gaps, technical feasibility, risks, and a final build / don't-build recommendation with reasoning and an MVP suggestion.
>
> Under the hood it's a **CrewAI multi-agent pipeline**: a Research agent gathers signals using a web-search tool, a Market Analyst assesses demand and competitors, a Risk Analyst evaluates technical and market risk, and a Strategy agent synthesizes everything into the final call. The tasks are chained with CrewAI's `context` mechanism, so each agent builds on the previous one's output — it's a real dependency graph, not four isolated prompts. The final report is **Pydantic-schema-validated**, with auto-retry if the model's JSON doesn't conform.
>
> It's wrapped in **FastAPI** — async, validated, auto-documented at `/docs` — three cleanly separated layers, and it's **Dockerized**, running as non-root with multi-stage builds.
>
> The decision I'm most proud of: the whole thing **runs with zero API keys.** There's a deterministic mock engine behind the same interface, so the system is fully demoable and the test suite is fast, free, and keyless in CI. The real multi-agent crew is a drop-in upgrade behind one env var. Want me to show it running?"

Then open `/docs`, fire `/analyze`, show the JSON, and point at the `engine` field.

---

<a name="5-questions"></a>
## 5. The Kill-Shot Questions (and your answers)

**Q: Is this actually multi-agent, or four prompts in a trench coat?**
A: Multi-agent. The agents have distinct roles/tools and the tasks are linked with `context=[...]`, so each agent's output is the next one's input. The Strategy agent receives all three prior outputs. Remove the context links and it *would* be four isolated prompts — that's exactly the #1 CrewAI beginner bug, and avoiding it is the point.

**Q: Why CrewAI over LangGraph/AutoGen?**
A: The workload is a known, sequential analyst pipeline with structured output. CrewAI's role-based sequential `Process` expresses that most directly and readably. I'd switch to LangGraph the moment I needed cycles or conditional branching, or to CrewAI Flows for event-driven control — which is exactly how I'd build the refinement loop extension.

**Q: How do you test an LLM app — the output is nondeterministic?**
A: I don't assert LLM *content*. I assert wiring, schemas, and fallbacks against a deterministic mock engine and mocked HTTP. CI is keyless and runs in seconds. There's one opt-in, key-gated live smoke test I run manually before shipping, to confirm a real end-to-end run.

**Q: What happens if the LLM returns malformed JSON?**
A: `output_pydantic` makes CrewAI re-prompt to fix the schema automatically. If `result.pydantic` still comes back empty, the engine falls back to parsing `result.raw`, and ultimately to the mock — the user never gets a 500 for a model formatting hiccup.

**Q: CrewAI's kickoff is blocking — doesn't that wreck FastAPI's concurrency?**
A: It would if called directly. I offload it with `asyncio.to_thread` and bound it with `asyncio.wait_for`, so the event loop stays free and slow runs time out gracefully (504 or degrade-to-mock).

**Q: How do you stop agents from looping / burning tokens?**
A: `allow_delegation=False` on executors (so they can't ping-pong tasks), sequential process (no manager nondeterminism), low temperature, tight task `expected_output`, and a request timeout as a hard backstop.

**Q: Where are secrets?**
A: Env only, via `pydantic-settings`, injected through Docker `env_file`. Never in code, never in the image, never logged. `.env` is gitignored; `.env.example` documents the vars.

**Q: How would you take this to production?**
A: gunicorn with uvicorn workers behind a reverse proxy, request caching by idea-hash, structured logging + tracing (CrewAI has AgentOps/LangFuse/OpenTelemetry hooks), rate limiting, a queue (Celery/RQ) for long runs with a job-status endpoint instead of holding the HTTP connection, and per-task model routing to cut cost.

**Q: Cost?**
A: Sequential keeps token use predictable (no manager overhead). Cheaper model for Research/extraction, stronger model only for the Strategy synthesis (CrewAI is model-agnostic per-agent via LiteLLM). Cache repeats. The mock path is free.

**Q: What's the weakest part / what would you do with another week?**
A: (Pick one, be honest.) The mock's "intelligence" is templated, not learned; the refinement loop and an evaluation/judge agent aren't built yet; and I'd add idea-hash caching and SSE progress streaming. Knowing the gaps is the point.

---

<a name="6-failure-modes"></a>
## 6. Failure Modes You Must Be Able to Name

Naming these unprompted is what makes you look senior:
1. **Forgotten `context` links** → agents work in isolation (the classic bug). Mitigated by explicit `context=[...]` + a test asserting `decision_task.context` length.
2. **Delegation loops** (hierarchical / `allow_delegation=True`) → infinite ping-pong, token bonfire. Mitigated: sequential + delegation off.
3. **Blocking the event loop** with sync `kickoff`. Mitigated: `asyncio.to_thread`.
4. **Schema drift** in LLM JSON. Mitigated: `output_pydantic` auto-retry + fallback parsing.
5. **Provider outage / missing key.** Mitigated: tool returns error strings (agent recovers) + mock engine fallback.
6. **Runaway latency.** Mitigated: `asyncio.wait_for` timeout → 504 or degrade.
7. **Secret leakage.** Mitigated: env-only config, non-root container, no secrets in logs.

---

<a name="7-done"></a>
## 7. Definition of "Done Done"

You're interview-ready when **all** of these are true:
- [ ] `git clone && docker compose up` → `/analyze` returns a valid report **with no keys**.
- [ ] Add a key + `USE_REAL_CREW=true` → real 4-agent crew produces a schema-valid report (you've run it live at least once).
- [ ] `make test` green in seconds, keyless; GitHub Actions green.
- [ ] README has the architecture diagram, a real sample response, and the design-decisions section.
- [ ] You can draw the pipeline on a whiteboard and explain every box.
- [ ] You can answer every question in §5 without hesitating.
- [ ] You can say the §4 pitch in under 3 minutes and then demo it live.

---

### Suggested 2-Day Schedule

**Day 1:** M0 → M3 (you have a fully demoable product by lunch) → M4 → M5.
**Day 2:** M6 (the real crew) → M7 → M8 → M9 → M10. M11 only if time remains.

If Day 2 runs short, **stop after M8+M9+M10** and skip M11 entirely — a tested, dockerized, well-documented mock-backed system with the crew wired and one live run beats a half-built ambitious one every time.

Now go be the demon. 🔱

