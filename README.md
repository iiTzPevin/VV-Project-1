# EEE4701/EEE5703 Verification & Validation Project 1

## Team Members

- Minh Hoang Ho
- William Wright
- Matias Guillen
- Adrian Emeterio

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
just test project_one icarus
just mutate project_one
```

Running `just test` Writes The Coverage Report To `tb/project_one/coverage_report.txt`

## Results

- All 11 Tests Pass On The Clean FIFO
- Mutation Score Is 8/8 Released Mutants Found
- Coverage Is 37/37 Bins
- The Seeded Regression Runs 15 Seeds Of 500 Cycles Each

## Demo

Link: 
