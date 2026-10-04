# Working with Markdown in this course

Most of what you write this semester is Markdown: `gap_memo.md`, `vplan.md`,
`closure.md`, `nonvacuity.md`, `FINDINGS.md`, your weekly `ctmNN.md`, and — if
you are on a capstone team — `CONTRIBUTIONS.md`. This page is how to read and
write those files comfortably.

**The short version:** Markdown is plain text. `cat` it, `less` it, or open it
in any editor and it is already readable. Everything below is about making it
*pleasant*, not about making it *possible*. Never let tooling be the reason a
deliverable is late.

---

## Why plain text, and not Word

Three reasons, all of which matter for the way this course is graded:

- **It diffs.** Your `vplan.md` is revised at every capstone milestone. A
  Markdown diff shows exactly which row changed; a `.docx` diff shows nothing
  useful. The same is true of the git history behind `CONTRIBUTIONS.md`.
- **It holds evidence verbatim.** A fenced code block preserves a harness
  transcript character for character — the `found/total` line, the `PASS=1`
  banner, the `sby` verdict. A screenshot of that text is not evidence you can
  grep, and a reflowed Word paste is not the output you actually got.
- **It lives next to the code.** The file sits in the repo with the testbench
  it describes, at the tag that was graded.

---

## A good local editor — Visual Studio Code

Free, works on macOS, Windows, and Linux, and it is the same editor you will
use for the Python and SystemVerilog. <https://code.visualstudio.com/>

This section is about running VS Code **on your own computer**, which is all
you need. Connecting it *to* eustis is a separate question, and the answer is
not the obvious extension — see below.

**Preview a rendered file:**

| | macOS | Windows / Linux |
|---|---|---|
| Preview (replaces the tab) | `Cmd` `Shift` `V` | `Ctrl` `Shift` `V` |
| Preview **side by side** — the one you want | `Cmd` `K` then `V` | `Ctrl` `K` then `V` |

Side-by-side scroll-syncs with your source, so you can watch a table line up
while you type it. No extension needed; Markdown preview is built in.

Two settings worth turning on the first day (`Cmd`/`Ctrl` `,`, then search):

- **`Editor: Word Wrap`** → `on`. Prose in a code editor is miserable without it.
- **`Markdown › Preview: Breaks`** → on, if you want single newlines to render
  as line breaks the way Webcourses does.

---

## Editing files that live on eustis

The toolchain lives on `eustis.eecs.ucf.edu`, so your runs happen there — but
you do not have to write prose in a terminal editor, and you do not need to
install anything to do this well.

### Option 1 — Two windows (recommended, nothing to install)

Keep an **`ssh` window** open for *running* things on eustis, and use **whatever
editor you already have** at home for *writing*. Move files with `scp`, the same
command you used to send the packet over.

This suits the work better than it first sounds. Your deliverables are prose
*about* runs — you run `just mutate alu` on eustis, copy the transcript, and
paste it into a Markdown file. The writing does not have to happen on eustis at
all. What does have to end up there is whatever the assignment says to submit,
and `scp` puts it there in one line.

Nothing to install, nothing to configure, and identical on Windows, macOS, and
Linux.

### Option 1b — SSH FS, if you want eustis files to feel local

Install the **SSH FS** extension (Kelvin Schoofs) in VS Code. It shows eustis as
a folder in your editor and edits files in place over SFTP. Crucially it
installs **nothing on eustis** — which is the whole reason to prefer it over the
extension below.

Optional. The two windows above cover everything this course asks of you.

### ⚠️ Not Microsoft's Remote-SSH — here is why

**Do not start with `ms-vscode-remote.remote-ssh` on eustis.** It installs a few
hundred megabytes of VS Code server *into your home directory*, and your home
directory is a network path (`/home/net/<your-nid>`, not `/home/<your-nid>`).
That combination is unreliable here, and it fails in a way that misleads you:

| What you see | What is actually wrong |
|---|---|
| An **authentication** error | VS Code could not create its lockfile on a network home. Your NID and password are fine. This is the one that eats an evening. |
| Very slow first connect, or hangs later | A few hundred megabytes of small files being read across a network mount. |
| `~` or `$HOME` not expanded in a path box | Remote-SSH path settings have taken absolute paths only since VS Code 1.86. |

**There is no setting that fixes this on eustis.** The usual rescue is to move
the lockfile and the server install into `/tmp` — and you do not have write
access to `/tmp` here, so neither setting can do anything. Pointing them at your
home directory instead just puts a few hundred megabytes back onto the network
mount that caused the slowness to begin with, and spends your quota doing it.

Use two windows. It costs nothing, needs no setting, and cannot fail this way.

To see what your own account actually has — home filesystem type, quota, and
which scratch directories are writable — run `bash code/setup/eustis_check.sh`
on eustis and read section 6.

### Option 2 — Terminal editor on eustis

`nano FINDINGS.md` is fine and prints its shortcuts along the bottom of the
screen — `Ctrl` `O` saves, `Ctrl` `X` exits. `vim` and `emacs` are there too if
they are already yours. Nothing beats this for a one-line fix to a file that is
already on eustis.

### Moving whole directories, not single files

`scp` handles one file at a time well. If you are syncing a working directory,
`rsync` is the better tool:

```bash
rsync -av --exclude sim_build ./ <nid>@eustis.eecs.ucf.edu:~/vv/
```

Either way you now have two copies and one of them can go stale. Sync in one
direction only, and be deliberate about which one is the real one.

---

## Reading Markdown in a bare terminal

When you are on a plain SSH session with no GUI, in rough order of preference:

```bash
glow FINDINGS.md              # if present: renders tables and headings in color
pandoc -f markdown -t plain FINDINGS.md | less    # if present: flattens to prose
less FINDINGS.md              # always works — Markdown is readable as-is
```

Do not install anything into the shared environment to get a prettier view. If
`glow` and `pandoc` are missing, `less` is a complete answer.

---

## No-install option — VS Code in the browser

Open <https://vscode.dev> in **Chrome or Edge**, then *Open Folder* and pick
your course folder. You get the real editor and the real Markdown preview with
nothing installed.

Your files are read directly off your disk through the browser's File System
Access API and are **not uploaded anywhere** — but note this only works in
Chromium-based browsers; Firefox cannot open local folders this way. Useful on a
lab machine you cannot install software on, or on a borrowed laptop.

---

## The Markdown you actually need here

The templates lean on four constructs. This is the whole working vocabulary.

**Fenced code blocks** — for every transcript, command, and raw tool output.
Tag the language so it highlights:

    ```bash
    just mutate alu
    ```

    ```text
    found 7/8
    ```

**Tables** — the templates are mostly tables. The dashes row is required; the
columns do *not* have to line up in the source, though your future self will
thank you.

```
| Mutant | Reachable? | Why it survived |
|--------|------------|-----------------|
| add2sub | yes       | no equal-operand vector |
```

**Checkboxes** — the attestation blocks at the bottom of several templates.

```
- [ ] not done
- [x] done
```

**Emphasis and headings** — `#` through `####`, `**bold**`, `` `inline code` ``.
Use inline code for signal names, file names, and commands. It reads better and
it survives copy-paste.

---

## Before you submit

- [ ] Every transcript is inside a fenced block, pasted verbatim — not
      retyped, not summarized, not a screenshot.
- [ ] Every comment block (`<!-- … -->`) from the template is deleted.
- [ ] Every `<placeholder>` is replaced.
- [ ] The headings the template gave you are still there, unrenamed — several
      rubrics are scored row by row against them.
- [ ] You previewed it once. A broken table is obvious rendered and invisible
      in source.

---

*Stuck on tooling for more than twenty minutes? Post in the course channel.
Losing an evening to a Markdown editor is not the assignment.*
