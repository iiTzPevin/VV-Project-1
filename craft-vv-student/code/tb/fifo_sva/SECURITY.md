# Information-flow assertion: `dut/leak_check.sv`

`leak_check` is a tiny declassifier: `public_in` flows to `pub_out`, and a
designated **secret** input may be mixed in **only** when `secure_mode == 0`
(the open/declassified path). When `secure_mode == 1`, the secret must have no
influence on `pub_out`. The bound assertion `a_no_secret_leak` enforces this by
**self-composition**: it recomputes the exact same declassification function
with the secret scrubbed to zero, and asserts that, in secure mode, the real
output equals the scrubbed output. If the secret can move a public output, the
two disagree and the assertion fires. Run it with
`make -C tb/fifo_sva/leak` (holds, test PASSES) and
`make -C tb/fifo_sva/leak LEAK=1` (injects `-DLEAK_BUG`, the assertion fires and
the leak is caught).

## What this does and does NOT prove (it is simulation-only)

This is a **dynamic, sim-only** non-interference check: it can only catch a leak
on the specific `(secure_mode, public_in, secret)` sequences the testbench
actually drives, and it compares each run against a single scrubbed reference
(secret = 0) rather than all secret values. So a green run means "no leak was
**observed** on the exercised traces," **not** "the secret can never leak."
It does not account for timing/power/other side channels, X-propagation, or
leaks that only appear under inputs the stimulus never reaches — its strength is
bounded by your coverage. A *sound* guarantee of non-interference needs
**formal** 2-safety reasoning (self-composition or product machines proven with
a model checker, or static taint/IFT analysis) that quantifies over *all*
inputs and states — the Week-8 formal flow (`formal/`) is where that kind of
exhaustive proof lives. Use this assertion as a cheap always-on tripwire during
simulation, and reserve the security *proof* for the formal tools.
