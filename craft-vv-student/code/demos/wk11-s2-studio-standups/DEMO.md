# Week 11 · Session 2 — bring-up, standups, and the green-by-the-bell door

This session is a studio, not a lecture. You spend all 75 minutes at your own
bench. Here is what happens, what to bring, what you will be asked, and what
has to be true before you leave.

**What it shows.** A smoke test is proof your *environment* works, not that the
design does. Every team leaves with one green.

## What to bring

- Your bench, in whatever state it is in. Bring the failure, not a story
  about it.
- Your track's repo, forked, with the provided RTL in it.
- `vplan.md` holding the three feature rows and two risk rows you drafted in
  Session 1's clinic.
- One named blocker you can say in a sentence.

Two dates are on the board all session: **M1 due Sunday 23:59, tagged `m1`.
CtM-11 due Wednesday 23:59 next week.** The milestone contract is
`weeks/week11/week11-hw.tex` (M1, 15% of the capstone). The session plan is
`weeks/week11/week11.tex`.

## What happens

1. A frame: what M1's skeleton is, and what "brought up" means.
2. Standups. Three minutes per team, timer visible.
3. Four ways bring-up dies, named before you rediscover them.
4. Studio. An instructor rotation works benches in blocker order.
5. The exit check at the door, team by team.

## What you will be asked at standup

Three minutes, whole team standing, one speaker. Four things:

- Which track you are on.
- What state the bench is in.
- **One named blocker.**
- The one thing that will be green by the bell.

Your blocker goes on the board word for word. The blocker list sets the
rotation order for the studio block, so a vague blocker costs you help.

## What "brought up" means

M1 in one sentence, per the capstone packet: a vplan plus a working
environment skeleton. That means the DUT brought up, a driver, monitor and
scoreboard (or pyuvm agent) in place, and a smoke test passing.

Here is the bring-up ladder. Every rung is checkable, so check them in order.

1. The provided RTL compiles under Icarus.
2. Reset drives the design to exactly the state the spec's *Reset* section
   names — checked, not assumed.
3. One transaction in, one observable out, compared against the **spec**.
4. From `code/`, the track smoke run prints PASS —

```bash
make -C capstone/riscv SIM=icarus        # or axi_subsystem / trojan
```

The smoke test is not verification. It proves you can drive and observe the
DUT at all. You cannot find bugs through a bench that does not run. That is why
M1 exists as its own graded gate.

> **Check yourself.** Point at the rung you are actually on. If you are on
> rung 1 and calling it done, name what reset is supposed to leave behind and
> where you check it.

## Four ways bring-up dies

1. **Reset polarity / duration** — the design "runs" from a half-reset state.
   Every later mystery traces back here. Check the spec's *Reset* section
   first.
2. **The oracle copied from the DUT** — a scoreboard derived from the design's
   own logic agrees with the design by construction, bugs included. The oracle
   encodes the spec, independently.
3. **An observability hook mis-wired** — the spec's harness hooks are your
   bench's eyes. A silent mis-wire looks like a passing test that checks
   nothing. Verify that each hook moves when it should.
4. **`sim_build` staleness** — switching DUT paths without `rm -rf sim_build`
   silently re-runs the old compile. The Week-3 demo documented this trap, and
   it returns on day one of every bring-up.

If you are stuck at rung 2, it is almost always failure 1. If you are stuck at
rung 3, it is failure 2 or failure 3.

> **Check yourself.** Take failure 2 seriously for a minute. Open your
> scoreboard and ask where each expected value comes from. If the answer is
> "the same logic the DUT uses", you have this failure.

## The door criterion

At the door, team by team: run the smoke, see PASS, and show `vplan.md`
holding at least the three feature rows and two risk rows from Session 1's
clinic.

If you clear the door early, start your vplan's security row. Every track
carries one: privileged-instruction reachability, locked-register access
control, or the unreachable-Trojan property, per `capstone/capstone.tex`.

If you leave without green, you say out loud the one blocker and your first
move on it. That sentence goes in the standup log.

## If you get stuck

| Problem | Why it happens | Fix |
|---|---|---|
| You have no track by standup time | Choice paralysis | Take the assignment from the clinic's interest poll. `capstone.tex` maps tracks to tastes (architecture / interfaces / security) |
| One bug eats your whole studio block | It is a real env bug, not a concept gap | Timebox it to 10 min, park it with a named hypothesis, work something else, come back at the end |
| "It compiles" feels like done | The ladder collapsed to rung 1 | Re-draw the ladder. Say what the reset state *should* be, then show where that is checked |
| You finish in 20 minutes | Strong start | Pull M2 forward. Randomize one field of your stimulus under the same scoreboard |
