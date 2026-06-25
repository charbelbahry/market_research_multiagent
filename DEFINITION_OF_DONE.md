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

### M3 — API wired to Orchestrator
- [ ] `curl POST /analyze` returns a valid report end-to-end (mock engine)
- [ ] `POST /analyze {"idea": "hi"}` → 422 (too short)
- [ ] `POST /analyze {}` → 422
- [ ] 3+ API tests green

### M4 — Tools Layer
- [ ] `WebSearchTool()._run("AI tutors")` returns useful text in all modes (Serper / Tavily / mock)
- [ ] No keys → mock results returned
- [ ] HTTP errors → error string (not exception)
- [ ] `SearchInput` rejects `max_results=99`
- [ ] Tests green (no real network calls)

### M5 — Agents + Multi-Model Routing
- [ ] `build_agents(...)` returns 4 `Agent` instances with expected roles
- [ ] Researcher has exactly one tool; others have none
- [ ] Research/Market/Risk agents use cheap model; Strategy uses strong model
- [ ] No network/LLM call happens at construction
- [ ] Tests green

### M6 — Tasks & Crew
- [ ] With a real key, `/analyze` produces a genuine 4-agent report
- [ ] `decision_task.context` has length 3
- [ ] `decision_task.output_pydantic is FeasibilityReport`
- [ ] Token usage captured in response meta
- [ ] All non-live tests green

### M7 — Async, Timeouts, Graceful Degradation
- [ ] Concurrent requests don't serialize (proves non-blocking)
- [ ] Timeout triggers 504 or degraded response
- [ ] Exception in engine → 500 with no leaked internals
- [ ] Tests green

### M8 — MCP Server
- [ ] MCP server instantiates and registers `analyze_idea` tool
- [ ] Tool callable from Claude Desktop or MCP Inspector
- [ ] Returns valid `FeasibilityReport` JSON
- [ ] Tests green

### M9 — Observability (LangFuse)
- [ ] LangFuse callback attached to Crew when keys are configured
- [ ] Traces visible in LangFuse dashboard (all 4 agents, tool calls, token usage)
- [ ] No errors when LangFuse keys are absent (graceful skip)
- [ ] Tests green

### M10 — Tests, Lint, Types, CI
- [ ] `ruff check` green
- [ ] `mypy app` green
- [ ] `pytest -m "not live"` green (fast, keyless)
- [ ] GitHub Actions CI green
- [ ] ~80%+ coverage of non-LLM code

### M11 — Docker
- [ ] `docker build` succeeds
- [ ] `docker compose up` → `curl /health` 200 → `curl /analyze` returns report
- [ ] Container runs as non-root
- [ ] Image size is reasonable (slim)

### M12 — Docs, Diagram, Demo Script
- [ ] A stranger can clone, run, and understand the system in under 5 minutes from the README alone
- [ ] Architecture diagram included
- [ ] Headline features documented (MCP, multi-model routing, LangFuse)
- [ ] Design-decisions section present
- [ ] `DEMO.md` with literal click-path for the interview
