# Contributions — Group #15 Project #1

**Members:** Minh Hoang Ho 5182391 · Matias Guillen 5523210  · William Wright 4735092 · Adrian Emeterio 5470594
**Repo:** [GitHub](https://github.com/iiTzPevin/VV-Project-1)
**Demo:** [Video Link](https://ucf-my.sharepoint.com/:v:/g/personal/ho667674_ucf_edu/IQDNYZTf0hGhSKS1ULnkwfZPAczPsYebZXjd3SrbTUx1ie0?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0&e=wYz3sk)
**Track:** Project 1 Constrained-Random Verification Of A Synchronous FIFO
**Last Updated:** 11-04-2026 **Through Milestone:** 11-08-2026

---

## Project #1 — 11-8-2026

| Member | What They Owned | Evidence (Commits / Files / PRs) | Approx. Share |
|--------|-----------------|----------------------------------|--------------:|
| Minh Hoang Ho | Wrote the test cases and wrote the seeded regression | `project_one/test_fifo.py`, `project_one/crv/seeded_regression.py` | 25% |
| Matias Guillen | Wrote the driver and wrote the monitor | `project_one/tb/driver.py`, `project_one/tb/monitor.py` | 25% |
| William Wright | Wrote the pyvsc transaction and its constraints which ended up in one file along with the phase class | `project_one/crv/transactions.py` | 25% |
| Adrian Emeterio | Wrote the scoreboard and wrote the coverage model | `project_one/tb/scoreboard.py`, `project_one/tb/coverage.py` | 25% |

**Shared Or Paired Work:** All of the documentation files including vplan.md, closure.md, FINDINGS.md, ai_log.md, and REPORT.pdf were done as a team effort

**What Slipped, And Who Picked It Up:** Nothing really slipped and every team member finished their part. The only thing was that each of us should have started working on this a lot ealier since we were given a lot more time.

## Whole-Project Summary

| Member | Principal Contributions (All Four Milestones) | Overall Share |
|--------|-----------------------------------------------|--------------:|
| Minh Hoang Ho | steup the repo, wrote test cases, and wrote seeded regression| 25% |
| Matias Guillen | wrote driver and monitor | 25% |
| William Wright | wrote transaction and constraints | 25% |
| Adrian Emeterio | wrote scoreboard and coverage model | 25% |

**The Three Things This Team Did That We Would Each Defend In An Interview:**

1. We split the work evenly so each person owned their own files and knew exactly what they were responsible for.
2. We stayed in contact the whole project and checked each other's files so everything fit together.
3. Every test checks the FIFO against the model on every cycle so we know the results are actually correct.

## Non-Code Contributions

| Member | Contribution | Where it shows |
|--------|--------------|----------------|
| The whole team | Writing all of the write-ups and the report | `vplan.md`, `closure.md`, `FINDINGS.md`, `CONTRIBUTIONS.md`, `ai_log.md`, `README.md`, and `REPORT.pdf` |
| Minh Hoang Ho | Recording the demo | Link in repo |

## AI Assistance

| Where | Used For | Verified By | Where The Verification Shows |
|-------|----------|-------------|------------------------------|
| `crv/seeded_regression.py` | Updating it to work with transactions.py | Minh Hoang Ho | ai_log.md and the eustis mutate run |
| Figure 2 graph script | Writing the script and making the graph from its printed numbers | Minh Hoang Ho | ai_log.md and the report |

---

## Attestation

- [ X ] Every claim above can be traced to the repo history.
- [ X ] This file was updated at each milestone, not reconstructed at the end.
- [ X ] Every member has read this file and agrees it is accurate.
- [ X ] Each member has separately submitted their confidential individual peer
