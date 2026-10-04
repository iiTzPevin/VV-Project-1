# Week 7 · Session 2 — the UART on the wire, then the first no-leak assertion

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** Protocol bugs live on cycles, not on end states. One
loopback wire and one forged frame take the suite from 3/8 to 8/8. A no-leak
assertion that passes is evidence about the traces you drove, not a proof.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_starter.py` | **3/8** — one byte, one weak check |
| 1 | `step1_frame_walk.py` | **7/8** — the frame read off the wire; `rx_err_silent` survives |
| 2 | `step2_bad_stop.py` | **8/8** — a stop bit forged low, then a clean frame recovers |
| 3 | `step3_no_leak.py` | the no-leak assertion holds; `LEAK=1` makes it fire |

Here is step 0, in both forms:

```bash
just demo 07 s2 0        # or:  make -C demos/wk07-s2-uart STEP=0
```

Steps 0–2 measured on `dut/uart.sv` (with `dut/uart_sva.sv` bound in) under
Verilator 5.020 `--assert`, scored against `tb/uart_sva/mutants_released.yaml`
(8 mutants). Step 3 runs `dut/leak_check.sv` — its own DUT and toplevel, no
pool. Captured output for every step and the LEAK variant is in `expected/`.
If your run differs, the DUT or the pool moved.

---

## Step 0 — see where the starter leaves you

```bash
just demo 07 s2 0
```

This is `tb/uart_sva`'s smoke test. It sends one byte, waits a frame, and
confirms `tx_ready` came back.

> **Check yourself.** The bound checker watches every cycle. Write down the
> score you expect from this run before you read the next line.

**You should see:** the test passes, and the pool score is **3/8**.

`tx_start_high`, `tx_stop_low`, `tx_ready_always` die on any transmission
because the SVA pins the frame *shape*: start low, stop high, ready only in
idle. The five survivors — `tx_msb_first`, `tx_data_corrupt`, `rx_bit_order`,
`rx_err_silent`, `tx_bits_short` — are all data-path or receiver bugs.

**What it means.** An assertion fires only on a bug the stimulus reaches *and*
the property watches. Nothing here looks at data, and nothing drives the
receiver into trouble. Same lesson as Session 1, protocol edition.

---

## Step 1 — loop the wire back and measure the frame

Type the loopback yourself. One coroutine samples `txd` every posedge into a
trace and mirrors it onto `rxd`. That is an external wire plus a logic
analyzer, in seven lines of Python. Send `[0xA5, 0x4B, 0x01, 0x80]`. The last
three are direction-sensitive: reversed they are different bytes.

```bash
just demo 07 s2 1
```

**You should see:**

```
  the frame on the wire   (CLKS_PER_BIT=8, one row per bit-time)
  pos    samples    reads as
  start  00000000   line low -- frame begins
  bit0   11111111   1  (LSB first)
  bit1   00000000   0
  ...
  bit7   11111111   1
  stop   11111111   line high -- frame ends
  wire reads 0xa5
4 frames measured on the wire; rx_valid pulsed 4x; frame_err 0x
```

**Walk the rows.** Start: 8 low samples. Each data bit: 8 identical samples
— that *is* `a_bit_stable`. Stop: 8 high — with the start row, that is the
framing property `a_stop_high`/`a_start_low` state positionally in
`dut/uart_sva.sv` ("start implies a correctly-timed stop," said without
`##[N:M]` sequences the simulator lacks). Read 1-0-1-0-0-1-0-1 off the wire,
LSB first: 0xa5.

**Score: 7/8.** The wire walk and the loopback scoreboard buy
`tx_msb_first`, `tx_data_corrupt`, `rx_bit_order`, `tx_bits_short` — four
mutants, one wire.

> **Check yourself.** One mutant survives. Name it, and say why the loopback
> can never reach it.

**What it means.** `rx_err_silent` swallows a bad stop bit — and a clean
loopback *can never produce a bad stop bit*. The transmitter refuses to break
its own framing. You cannot detect a fault on a path you cannot reach from the
front door.

---

## Step 2 — forge the frame the transmitter refuses to send

```bash
just demo 07 s2 2
```

Drive `rxd` directly and forge the stop bit low. Three clauses, three
asserts:

```
bad stop: frame_err 1x, rx_valid 0x, rx_data untouched
recovery: next clean frame lands, rx_data = 0xc3
```

**What it means.** `frame_err` — not `rx_valid` — and the data register holds
its old value; one bad frame does not poison the next. Step 1's walk still
runs first, unchanged (the file is an import plus one test). **8/8.** The last
mutant fell to the one stimulus only a bit-banged wire can produce. You repeat
this with your own stop-bit assertion.

> **Check yourself.** Say which single signal in the clean-run output would
> have to change for `rx_err_silent` to survive step 2 as well.

---

## Step 3 — write the first security assertion

```bash
just demo 07 s2 3
```

New DUT — `dut/leak_check.sv`, a declassifier. `public_in` flows to `pub_out`.
The secret may mix in only when `secure_mode` is 0. The assertion inside is the
self-composition monitor from the deck: recompute the same function with the
secret scrubbed to zero, and in secure mode the real output must equal the
scrubbed one.

**You should see:**

```
secure mode: 300 random secrets, pub_out tracked public_in every cycle
open mode: 50 draws declassified by policy
green means: no leak OBSERVED on these traces -- the proof is next week
```

**Then plant the leak** — recompile, one flag:

```bash
make -C demos/wk07-s2-uart STEP=3 LEAK=1
```

**You should see:**

```
[30000] %Error: leak_check.sv:51: Assertion failed in leak_check.a_no_secret_leak: 'assert' failed.
```

30 ns: the *first* secure draw. With `-DLEAK_BUG` the secret is mixed in
regardless of mode, the scrubbed reference disagrees immediately, and the
monitor names it.

**What it means.** The green run checked 300 of the 65,536 possible
secure-mode input pairs (8-bit secret × 8-bit public_in). A no-leak assertion
that passes is *suggestive, not a proof* — the leak may hide on a trace you
never drove. `security_assert.md` in HW7 must say so. Next week this exact
property becomes a proof over all reachable states — that difference is why
formal exists.

> **Check yourself.** 300 draws out of 65,536. State in one sentence what your
> green run does and does not entitle you to write in `security_assert.md`.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| step 1: `loopback: sent=[...] got=[]` | The loopback coroutine is not running, so `rxd` idles and the receiver never sees a frame | `start_loopback()` must be called before the first `send()` |
| step 1: `frame 0 never appeared on the wire` | `tx_valid` pulse missed — `send()` holds valid for exactly one cycle after `tx_ready` | Keep the `Timer(1)` settles in `send()`; do not drive on the rising edge race |
| step 2: `frame_err pulsed 0x` on clean RTL | Bit-banged timing off — the receiver samples mid-bit (`MID = CLKS_PER_BIT/2`) | `drive_frame` must hold each level a full `CLKS_PER_BIT=8`; check the parameter matches the DUT |
| step 3: port errors like `tx_valid not found` | STEP=3 swaps toplevel to `leak_check`; a mixed invocation compiled the UART | Run through `make STEP=3`, never by overriding `MODULE` alone |
| `LEAK=1` run passes | Stale model reused across the flag flip | Build dirs are keyed per step, DUT, and `-leakbug`; if you edited the Makefile, `rm -rf sim_build` |
| Scoring: perfect found/total but a red baseline line | The testbench is broken — it fails clean RTL too | The harness's clean-RTL baseline refuses to score; fix the bench first |
