# Verification plan — <DUT>

**Author:** **Spec version:** **Date:**

> A vplan is an argument that "done" is definable before you write tests. Every
> row here should be something you could defend in a signoff meeting. Rows you
> cannot defend are the honest content of the Risk section, not omissions.

## 1. Scope

**In scope:** <what this plan claims to verify>
**Out of scope:** <what it does not — say so plainly; this is not a weakness>
**Assumptions about the environment:** <clock, reset, protocol legality>

## 2. Feature list

One row per behavior the spec requires. `Req` cites a line or section of the
spec — if you cannot cite one, that is a spec gap and it belongs in section 5.

| ID | Feature | Req | Priority | How it is verified |
|----|---------|-----|----------|--------------------|
| F1 |         |     | H/M/L    | directed / CRV / assertion / formal |
| F2 |         |     |          |  |

## 3. Coverage model

Coverpoints and their bins. A cross earns its place only if the interaction is
where a bug would hide — say which bug.

| ID | Coverpoint | Bins | Why these bins |
|----|-----------|------|----------------|
| C1 |           |      |  |

**Crosses**

| ID | Cross | The interaction it is aimed at |
|----|-------|-------------------------------|
| X1 |       |  |

**Illegal / ignore bins:** <what is excluded and on what authority in the spec>

## 4. Test matrix

Every feature maps to at least one test; every test traces back to a feature.
An untraceable test is a test nobody can defend.

| Test | Features | Kind | Pass criterion |
|------|----------|------|----------------|
|      |          | directed / random / assertion / formal | |

## 5. Risk and spec ambiguity

| # | Ambiguity or risk | Where in the spec | How I resolved it | Residual |
|---|-------------------|-------------------|-------------------|----------|
| 1 |                   |                   | asked / assumed / tested both | |

## 6. Closure criteria

State the numbers *before* you start, so closure is a measurement and not a
negotiation.

- Functional coverage target: **__%** of the model in section 3
- Mutation target: **__/__** on the hidden pool
- Assertions: every property paired with a passing `cover` (no vacuous passes)
- What I will report as **not verified**:
