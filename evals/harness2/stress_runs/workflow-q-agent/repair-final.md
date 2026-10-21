Fixed and documented: naive datetimes mean UTC; aware datetimes convert to UTC before comparison. Stored timestamps remain unchanged.

- Recorded correction **2/2** in `odd/tasks/stress-workspace.md`.
- CI: **3 tests passed**.
- Real SQLite probes confirmed aware `opened_at` with naive `now` works without `TypeError`.
- Independent review: **APPROVED**.
- Tests unchanged; no commit or deployment.
- Native review blocked by read-only `.git`.

Risk: none.

## Key Learnings:
1. Normalizing both operands preserves timezone offsets’ meaning and strict deadline boundaries.