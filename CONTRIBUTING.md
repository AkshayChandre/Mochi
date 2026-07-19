# Contributing to Mochi

## Environment

Python 3.10+ in a local virtual environment — always `.venv`, never global:

```powershell
py -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e .[dev]
```

## Branch model

`master` is **protected**. No direct commits — every change lands via a
pull request with green tests. Squash-merge only, so history on master is
one clean commit per change.

### Branch naming (strict)

```
<type>/<short-kebab-description>
```

| Type | Use for |
|------|---------|
| `feat/` | New capability (`feat/voice-wake-word`) |
| `fix/` | Bug fix (`fix/blink-timer-drift`) |
| `refactor/` | No behavior change (`refactor/extract-easing`) |
| `test/` | Tests only (`test/face-transitions`) |
| `docs/` | Documentation (`docs/wiring-diagram`) |
| `chore/` | Tooling, deps, CI (`chore/ruff-bump`) |
| `hw/` | Hardware: CAD, BOM, wiring (`hw/neck-mount-v2`) |

Lowercase, hyphens, no issue numbers in the name (put them in the PR).

### Commit messages (Conventional Commits)

```
<type>(<scope>): <imperative summary, <=50 chars>

Optional body: WHY, not what. Wrap at 72.
```

Examples:

```
feat(face): add surprised emotion with radial pop
fix(voice): drop frames during barge-in to kill echo
chore: pin pygame >=2.5 for SRCALPHA fix
```

Rules: imperative mood ("add", not "added"), no trailing period, scope is
the package dir (`face`, `voice`, `brain`, `body`, `agent`) or omitted for
repo-wide changes.

## Quality gates (run before every PR)

```powershell
ruff check src tests
ruff format --check src tests
pytest
```

All three must pass. New behavior requires a test; the suite runs headless
(`SDL_VIDEODRIVER=dummy` is set by the tests themselves).

## Design rules

- All motion/timing is `dt`-based, never frame-count-based.
- `mochi.body` is the only package allowed to touch GPIO/hardware; everything
  else must run on a plain PC.
- No cloud calls, no paid services, no telemetry. Ever.
