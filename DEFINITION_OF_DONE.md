# Definition of "Done Done"

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

## Per-Milestone Definition of Done

### M0 — Scaffold & Health ✅
- [x] Server boots with `uvicorn app.main:app --reload`
- [x] `GET /health` returns `200 {"status": "ok", ...}`
- [x] `/docs` renders Swagger UI
- [x] `pytest` green (1 test)

### M1 — The Contract (schemas) ✅
- [x] Models import cleanly
- [x] 5 validation tests green (valid payload, idea too short, bad recommendation, confidence out of range, extra fields rejected)

### M2 — Mock Engine (lightweight, testing utility) ✅
- [x] `MockEngine().analyze("...")` returns a valid `FeasibilityReport`
- [x] Deterministic: same idea → same report
- [x] All list fields non-empty; `recommendation` is a valid literal
- [x] Tests green

### M3 — API wired to Orchestrator ✅
- [x] `curl POST /analyze` returns a valid report end-to-end (mock engine)
- [x] `POST /analyze {"idea": "hi"}` → 422 (too short)
- [x] `POST /analyze {}` → 422
- [x] 3+ API tests green

### M4 — Tools Layer ✅
- [x] `WebSearchTool()._run("AI tutors")` returns useful text in all modes (Serper / Tavily / mock)
- [x] No keys → mock results returned
- [x] HTTP errors → error string (not exception)
- [x] `SearchInput` rejects `max_results=99`
- [x] Tests green (no real network calls)

### M5 — Agents + Multi-Model Routing ✅
- [x] `build_agents(...)` returns 4 `Agent` instances with expected roles
- [x] Researcher has exactly one tool; others have none
- [x] Research/Market/Risk agents use cheap model; Strategy uses strong model
- [x] No network/LLM call happens at construction
- [x] Tests green

### M6 — Tasks & Crew ✅
- [x] With a real key, `/analyze` produces a genuine 4-agent report
- [x] `decision_task.context` has length 3
- [x] `decision_task.output_pydantic is FeasibilityReport`
- [x] Token usage captured in response meta
- [x] All non-live tests green

### M7 — Async, Timeouts, Graceful Degradation ✅
- [x] Concurrent requests don't serialize (proves non-blocking)
- [x] Timeout triggers 504 or degraded response
- [x] Exception in engine → 500 with no leaked internals
- [x] Tests green

### M8 — MCP Server ✅
- [x] MCP server instantiates and registers `analyze_idea` tool
- [x] Tool callable from Claude Desktop or MCP Inspector
- [x] Returns valid `FeasibilityReport` JSON
- [x] Tests green

### M9 — Observability (LangFuse) ✅
- [x] LangFuse callback attached to Crew when keys are configured
- [x] Traces visible in LangFuse dashboard (all 4 agents, tool calls, token usage)
- [x] No errors when LangFuse keys are absent (graceful skip)
- [x] Tests green

### M10 — Tests, Lint, Types, CI ✅
- [x] `ruff check` green
- [x] `mypy app` green
- [x] `pytest -m "not live"` green (fast, keyless)
- [x] GitHub Actions CI green
- [x] ~80%+ coverage of non-LLM code

### M11 — Docker ✅
- [x] `docker build` succeeds
- [x] `docker compose up` → `curl /health` 200 → `curl /analyze` returns report
- [x] Container runs as non-root
- [x] Image size is reasonable (357MB content — floor for crewai[tools])

### M12 — Docs, Diagram, Demo Script
- [ ] A stranger can clone, run, and understand the system in under 5 minutes from the README alone
- [ ] Architecture diagram included
- [ ] Headline features documented (MCP, multi-model routing, LangFuse)
- [ ] Design-decisions section present
- [ ] `DEMO.md` with literal click-path for the interview
