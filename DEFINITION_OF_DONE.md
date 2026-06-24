# Definition of "Done Done"

You're interview-ready when **all** of these are true:

- [ ] `git clone && docker compose up` → `/analyze` returns a valid report **with no keys**.
- [ ] Add a key + `USE_REAL_CREW=true` → real 4-agent crew produces a schema-valid report (you've run it live at least once).
- [ ] `make test` green in seconds, keyless; GitHub Actions green.
- [ ] README has the architecture diagram, a real sample response, and the design-decisions section.
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

### M1 — The Contract (schemas)
- [ ] Models import cleanly
- [ ] 4+ validation tests green (valid payload, idea too short, bad recommendation, confidence out of range)

### M2 — Mock Engine
- [ ] `MockEngine().analyze("...")` returns a valid `FeasibilityReport`
- [ ] Deterministic: same idea → same report
- [ ] Idea-aware: different ideas → different outputs
- [ ] All list fields non-empty; `recommendation` is a valid literal

### M3 — API wired to Orchestrator
- [ ] `curl POST /analyze` returns a valid report end-to-end (mock engine)
- [ ] `POST /analyze {"idea": "hi"}` → 422 (too short)
- [ ] `POST /analyze {}` → 422
- [ ] 3+ API tests green
- [ ] **Fully demoable with zero keys**

### M4 — Tools Layer
- [ ] `WebSearchTool()._run("AI tutors")` returns useful text in all three modes (Serper / Tavily / mock)
- [ ] No keys → mock results returned
- [ ] HTTP errors → error string (not exception)
- [ ] `SearchInput` rejects `max_results=99`
- [ ] Tests green (no real network calls)

### M5 — Agents
- [ ] `build_agents(...)` returns 4 `Agent` instances with expected roles
- [ ] Researcher has exactly one tool; others have none
- [ ] No network/LLM call happens at construction
- [ ] Tests green

### M6 — Tasks & Crew
- [ ] With a real key + `USE_REAL_CREW=true`, `/analyze` produces a genuine 4-agent report
- [ ] Without keys, transparently uses mock
- [ ] `decision_task.context` has length 3
- [ ] `decision_task.output_pydantic is FeasibilityReport`
- [ ] All non-live tests green

### M7 — Async, Timeouts, Graceful Degradation
- [ ] Concurrent requests don't serialize (proves non-blocking)
- [ ] Timeout triggers 504 or degraded mock response
- [ ] Exception in engine → 500 with no leaked internals
- [ ] Tests green

### M8 — Tests, Lint, Types, CI
- [ ] `ruff check` green
- [ ] `mypy app` green
- [ ] `pytest -m "not live"` green (fast, keyless)
- [ ] GitHub Actions CI green
- [ ] ~80%+ coverage of non-LLM code

### M9 — Docker
- [ ] `docker build` succeeds
- [ ] `docker compose up` → `curl /health` 200 → `curl /analyze` returns mock report
- [ ] Container runs as non-root
- [ ] Image size is reasonable (slim)

### M10 — Docs, Diagram, Demo Script
- [ ] A stranger can clone, run, and understand the system in under 5 minutes from the README alone
- [ ] Architecture diagram included
- [ ] Real sample response included
- [ ] Design-decisions section present
- [ ] `DEMO.md` with literal click-path for the interview

### M11 — Extensions (optional)
- [ ] At least one extension implemented (if time permits)
- [ ] Can describe the rest credibly in an interview
