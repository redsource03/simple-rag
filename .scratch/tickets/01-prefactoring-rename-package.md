# 01: Prefactoring — rename package to simple_rag and fix pyproject.toml

**What to build:** Rename the package from `rag_agent` to `simple_rag` and fix `pyproject.toml` so the repo is internally consistent and ready for the full refactor.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] `src/rag_agent/` renamed to `src/simple_rag/`
- [ ] `pyproject.toml` `name` changed from `rag-agent` to `simple-rag`
- [ ] `pyproject.toml` `[project.scripts]` updated to `simple-rag = "simple_rag.__main__:main"`
- [ ] `fastmcp` version conflict resolved (remove `>=4.0.0` and keep `==4.1.6`, or vice versa)
- [ ] `google-adk` dependency removed (no code uses it; it's a separate service)
- [ ] All imports in `main.py` and `config.py` updated to `simple_rag.`
- [ ] `poetry lock` runs without errors
- [ ] `python -m simple_rag` starts the server (no import errors)

---

**Notes:** This is a wide refactor — rename the entire package in one pass. The old name `rag_agent` cannot coexist with `simple_rag` in the same namespace. All 9 downstream tickets depend on this being done first.
