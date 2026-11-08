# EEE4701/EEE5703 Verification & Validation Project 1

## Team Members

- Minh Hoang Ho
- William Wright
- Matias Guillen
- Adrian Emeterio

## Commits

All Commits To This Repo Were Pushed By Minh Hoang Ho But Every Member Wrote Their Own Part

- Minh Hoang Ho Wrote `test_fifo.py` & `crv/seeded_regression.py`
- Matias Guillen Wrote `tb/driver.py` & `tb/monitor.py`
- William Wright Wrote `crv/transactions.py` # Transaction And Constraints In One File
- Adrian Emeterio Wrote `tb/scoreboard.py` & `tb/coverage.py`

## Where To Find The Files

Project Is Under `craft-vv-student/code/tb/project_one/`

Everything Else In `craft-vv-student/` Is The Course Starter Packet

```
craft-vv-student/code/tb/project_one/
├── vplan.md
├── closure.md
├── FINDINGS.md
├── CONTRIBUTIONS.md
├── ai_log.md
├── REPORT.pdf
├── coverage_report.txt
├── test_fifo.py
├── Makefile
├── mutants_released.yaml
├── tb/
│   ├── driver.py
│   ├── monitor.py
│   ├── scoreboard.py
│   └── coverage.py
└── crv/
    ├── transactions.py # Transaction And Constraints In One File
    └── seeded_regression.py
```

## How To Run

Run These From The `craft-vv-student/code/` Folder On Eustis

```bash
source /opt/course/cocotb-env/bin/activate
just mutate project_one
```

Running `just mutate` Writes The Coverage Report To `tb/project_one/coverage_report.txt`

## Results

- All 11 Tests Pass On The Clean FIFO
- Mutation Score Is 8/8 Released Mutants Found (100%)
- Coverage Is 37/37 Bins (100%)
- The Seeded Regression Runs 15 Seeds Of 500 Cycles Each

## Demo

[Demo Video](https://ucf-my.sharepoint.com/:v:/g/personal/ho667674_ucf_edu/IQDNYZTf0hGhSKS1ULnkwfZPAczPsYebZXjd3SrbTUx1ie0?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0&e=aEFBFV)