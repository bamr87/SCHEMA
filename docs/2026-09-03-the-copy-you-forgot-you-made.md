# The Copy You Forgot You Made

*Draft for it-journey. Written after a session that started with "the SCHEMA
repo hasn't been updated in a while" and ended two pull requests deep in
somewhere else entirely.*

## The complaint

The prompt was five words of substance: *the SCHEMA repo has not been updated
in a long time.* No ticket, no stack trace, no failing build. Just a feeling
that something had gone quiet.

That is a real class of software problem and one of the hardest to act on,
because "quiet" has two causes and they look identical from outside. Either the
thing is finished — stable, correct, nothing to do — or nobody is looking. A
repository cannot tell you which it is, and neither can `git log`. The last
commit was two and a half weeks old. For a mature library that is health. For a
control plane's dependency it might be rot. The date alone carries no signal.

So the first job was not to fix anything. It was to find a measurement that
distinguishes the two.

## What "not updated" turned out to mean

The repo in question, `bamr87/SCHEMA`, is a small package that defines a
convention: every directory in a repository carries a `SCHEMA.md` file
describing what belongs in it, and a linter checks those files against reality.
The point is to let AI coding agents *look up* a repository's structure instead
of re-deriving it with `ls -R` every session. The package describes itself in
its own format — the pyramid describes the pyramid.

Its neighbour is a monorepo hub that manages about forty projects and runs four
daily and weekly automation loops: one that fixes broken workflows, one that
works through issues, one that rotates credentials, one that opens improvement
PRs nobody asked for. A serious amount of machinery.

`SCHEMA` was in that hub's project registry. It was in none of those loops.

Here is why, and it is the kind of thing you only find by reading the code
rather than the docs. Every loop selected its targets from `.gitmodules` — the
list of git submodules mounted inside the hub. `SCHEMA` was registered but not
mounted. So:

- the standardization fan-out skipped it
- the schema adoption fan-out skipped it
- the weekly improvement loop skipped it
- the AI-harness deploy lever skipped it

Four independent automations, one shared assumption, and a repo that fell
through all four. It had no `@claude` handler, no scheduled anything, no
dependency updates. It was not quiet because it was finished. It was quiet
because it was unreachable.

**Lesson one: when several independent systems all miss the same thing, they
are not independent. They share a lookup.**

## The assumption that was never true

The fan-out engine works like this: take a target name, resolve its GitHub URL,
`git clone` it fresh into a temp dir, seed files, commit, open a pull request.

Read that again and the bug is obvious. It *clones*. It never reads the mounted
working tree. The only thing `.gitmodules` ever contributed was a URL — and the
registry has the URL too, in a field called `repo_url`, right there in the same
repository.

The fix was about thirty lines: if the target is not in `.gitmodules`, look it
up in the registry. Every safety property survives untouched — still pull-request
only, still additive, still dry-run by default, still refusing upstreams that
aren't ours.

This is a shape worth recognising. The submodule check was not a *constraint*,
it was a *coincidence*: the first implementation happened to have `.gitmodules`
in hand, so it used it, and the accident calcified into a rule that nobody
re-derived. Years later four systems inherited a limitation that never had a
reason.

**Lesson two: ask what a check is actually protecting. If you cannot name the
failure it prevents, it may be protecting a coincidence.**

## Measuring instead of assuming

Here is the part I would want any engineer — human or AI — to copy.

The obvious next move after finding that gap is to write the fix and say "this
unblocks some repos." Instead: the hub already commits a daily inventory of
every repository's automation coverage, as a YAML file in git. The data to
*prove* the claim was sitting right there, in the working tree, free.

Five lines of Python against that committed file:

```
gap candidates:              .github, SCHEMA, git-with-the-program, irony-works
old rule (must be mounted):  []
new rule (must be ours):     .github, SCHEMA, git-with-the-program, irony-works
```

The deploy lever's target list was **empty**. Not "smaller than it should be" —
empty. Every closeable gap in the entire fleet was on a repo the lever could not
reach, so the automation had been running, succeeding, and doing nothing at all.

There was even a diagnostic designed to catch exactly this: a finding called
`gap-not-deployable` that fires when the kit could help but the fan-out cannot
reach the repo. It had been firing. It scores 35 on a severity scale, and the
attention board is capped at 20 items with a current floor of 65. The warning
existed and was truncated off the bottom of the page every single day.

**Lesson three: a signal that nobody can see is not a signal. Check your alert
budget the way you check your error budget — a warning below the cut is
indistinguishable from a warning you never wrote.**

And the corollary, for anyone directing an AI agent: *make it compute the
number.* "This probably affects a few repos" and "this affects four repos, and
the old rule returned zero" are different claims with different consequences,
and only one of them is checkable by the person reading your pull request. When
the data is already in the repo, an assertion is a choice.

## Vendoring: the copy you forgot you made

Then the second half, which is the more broadly useful story.

The hub does not *depend* on the SCHEMA package. There is no package registry
entry, no lockfile, no `pip install`. It **copies** three files in: the linter,
a template, a protocol snippet. Then it fans those copies out to forty more
repositories.

This is vendoring, and every organisation does it somewhere — a shared lint
config, a CI template, a `utils.py` that got pasted into a second service, a
Dockerfile that seven teams edited independently. Vendoring is often the right
call. The cost is that you have created a dependency your tooling cannot see.

The hub knew this and had defended half of it. A drift check compared every
*submodule's* copy of the linter against the *hub's* copy. It had already caught
three repositories that had quietly forked it. The comment above that check is
the best one-sentence statement of the problem I have read:

> A vendored copy that drifts is worse than a missing one: the repo still passes
> a gate, just not the same gate as everyone else.

But the check only looked downward. Nothing compared the *hub's* copy against
*upstream*. The provenance record — "we vendored commit `b2ffca1` on this date"
— was a hand-maintained text file, updated by whoever remembered. The entire
fleet could have drifted a year behind the package it vendors, and every gate in
every repository would still have been green.

**Lesson four: for every copy you make, ask which direction you check. Most
teams check the copies against the source of copies. Almost nobody checks the
source of copies against the original.**

## Building a contract that survives adaptation

The naive fix is a hash comparison: store the upstream file's SHA-256, fail when
the local copy differs. It falls over immediately on contact with reality.

Two of the three vendored files are *deliberately modified* downstream. The hub
reflows prose to one-paragraph-per-line because it has a markdown gate that
requires it. It restyles markdown tables from `|---|` to `| --- |`. It uses
single quotes where upstream uses double. None of that is drift. All of it
changes the hash. A strict comparison would have screamed every week about
changes that were intentional and correct, and would have been muted within a
month — the classic path from "we added monitoring" to "everyone ignores the
monitoring."

So the manifest declares a **parity tier** per file:

| tier | meaning | comparison |
| --- | --- | --- |
| `strict` | must be byte-identical | raw SHA-256 |
| `text` | may be restyled, must not change meaning | layout-blind SHA-256 |

The linter is `strict`, because a linter that differs by one line is a different
gate and the whole point is that everyone passes the same one. The two documents
are `text`.

The layout-blind hash has one subtlety worth stealing. My first version
normalised by *collapsing* whitespace runs to a single space — the obvious move,
and wrong. Reflowing prose collapses whitespace, but restyling a markdown table
**inserts** it: `|---|` and `| --- |` have different run structure, not just
different run lengths. Collapsing them does not converge. Removing whitespace
entirely does. Two lines of code, and the difference between a check that is
permanently amber and a check people trust.

I only found it because I ran the comparison against the real hub before writing
the tests, and it reported drift on a file whose own documentation said it was
content-identical. One of the two was lying. Chasing that down produced both the
fix and a test that pins it:

```python
def test_retabulated_text_payload_passes():
    # `|---|` -> `| --- |` INSERTS whitespace; a collapse-only normalizer
    # would call this drift, which is why the hash removes whitespace.
```

**Lesson five: run the new check against production data before you write its
tests. Fixtures confirm what you already believe; real data tells you what you
got wrong.**

## Content-addressed, and deliberately undated

One design decision I would repeat in any manifest, config snapshot, or lockfile.

The generated manifest carries **no timestamp and no commit SHA**. Only file
paths, hashes, sizes, and parity tiers.

That sounds like lost information. It buys something better: the file is a pure
function of the tree, so continuous integration can regenerate it and
byte-compare against the committed copy. Change a vendored file without
regenerating the manifest and the build fails. Add a `generated: 2026-09-03`
line and that check dies instantly — the file now differs every day for reasons
that mean nothing, so you have to relax the comparison to "roughly matches,"
which is not a comparison at all.

Provenance lives where provenance belongs: in the consumer's record of what it
vendored and when. The interface itself is content-addressed, and it goes stale
when the payload changes, never merely because time passed.

There is a satisfying consequence. When upstream commits something that does not
touch a vendored file, the sync loop reports *"the content matches, the stamp is
just behind"* and does nothing. No pull request. A re-vendor PR that changes no
vendored byte is noise, and noise is how automation earns its way into a filter
rule.

**Lesson six: if a generated artifact contains a timestamp, you have probably
traded a check you could automate for a fact you could have looked up.**

## Two kinds of drift need two kinds of response

The last piece is the routing rule, borrowed from a loop the same repo already
had.

The weekly sync opens a **pull request** for strict-parity drift: the linter has
one correct value, the machine knows it, apply it and let CI prove it. It opens
an **issue** for text-parity drift: those files carry deliberate local
adaptation, so resolving them means reading upstream's wording, porting the
substance, and keeping the local reflow. That is judgement. A machine that
overwrites them "fixes" the drift by destroying the adaptation, and does it again
next Monday, forever.

Same split the codebase already used for registry reconciliation: renames get
applied automatically because GitHub states them unambiguously; a 404 only gets
reported, because a repo-scoped token 404s on a private repo exactly as it does
on a deleted one, and auto-applying that would eventually deregister something
alive.

**Lesson seven: automation is not one decision. Sort findings by how certain the
signal is, and give each tier a different verb — apply, propose, report. A loop
that treats every finding as actionable will eventually take an action nobody
wanted.**

## On working this way with an AI agent

Some of this generalises to how the session ran, which may be the more portable
part.

**Give the agent the vague complaint, not your diagnosis.** "The repo is stale"
left room to discover that staleness was a *symptom* of unreachability. A more
specific prompt — "add a scheduled workflow to SCHEMA" — would have produced a
scheduled workflow and left the four-way blind spot exactly where it was.

**Insist on evidence from the repository, not from the model.** The strongest
findings here — the empty target list, the truncated warning, the two
disagreeing copies — all came from running something against committed data. An
agent that reads code well will still narrate plausible-sounding conclusions if
you let it. Ask for the command and the output.

**Structural conventions pay for themselves in agent sessions.** Both
repositories carry `SCHEMA.md` contracts, so orienting meant reading four small
files instead of dumping a tree of thousands. That is the whole thesis of the
package, and this session was an unplanned test of it: the agent knew where a
new tool belonged, which table row to add, and which directory was off limits,
without asking.

**Let the tests carry the reasoning.** The most valuable artifacts produced here
are not the two hundred lines of implementation. They are the assertions with
names like `text drift is NEVER overwritten` and `restamp preserves the
hand-written notes` — each one a decision that took real thought, pinned so the
next session cannot quietly undo it. Future agents do not read your commit
messages. They run your tests.

**Delete the dead thing.** Once the fan-out could reach registry-only repos, the
`gap-not-deployable` finding became unreachable code — every remaining case was
already excluded upstream of it. The temptation is to re-aim it at something.
Better to remove it and leave a comment explaining the class is now empty rather
than merely smaller. A diagnostic that cannot fire is worse than no diagnostic,
because it reads as coverage.

## What actually shipped

Upstream: a distribution manifest and the tool that generates and enforces it, a
weekly self-audit that files one deduplicated issue when the package breaks on
its own, an `@claude` handler, Dependabot, and thirty-five new tests.

Downstream: a weekly loop that compares the hub's vendored copies against that
manifest and routes each finding by how certain it is, plus a thirty-line change
that made four repositories reachable by machinery that had been quietly
running for months with nothing to do.

The original complaint was that a repository had gone quiet. It had. But the
interesting answer was not "so commit something to it" — it was that four
separate automations had been told to ignore it by a lookup nobody had
questioned, and that the one alarm designed to say so was scoring 35 in a list
that stops at 65.

Silence is not evidence of health. It is evidence of silence. Go and find out
which.
