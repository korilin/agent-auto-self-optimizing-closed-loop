# Closed Loop Playbook

## Daily Loop

1. Intake
- Assign task type (`coding`, `debug`, `review`, `docs`, `ops`).
- Check if a matching skill already exists.

2. Execute
- Use the minimum relevant context.
- Prefer existing scripts and references.

3. Verify
- Run tests or static checks when applicable.
- Confirm changed files and output contract.

4. Capture Learning
- For failures or high token usage, add one error entry in `.agent-loop-data/knowledge-base/errors/`.

## Weekly Loop

1. Generate report:

```bash
./scripts/weekly_review.sh
```

2. Review report and decide:
- Which new skills to create.
- Which existing skills to simplify or split.
- Which AGENTS rules to promote or remove.

3. Apply updates:
- Update `AGENTS.md` for stable policies.
- Update skill scripts/references for recurring workflows.

## Skill Creation Checklist

1. Normalize skill name (lowercase hyphen-case).
2. Keep `SKILL.md` short and procedural.
3. Put heavy domain details in `references/`.
4. Put deterministic repeated logic in `scripts/`.
5. Validate with a real usage sample.

## Failure Classification

- `P0`: Production/data-loss level.
- `P1`: User-facing incorrect behavior.
- `P2`: Workflow inefficiency or recoverable defect.
- `P3`: Minor issue with low impact.

## Suggested Cadence

- Error capture: immediate after incident.
- AGENTS update: weekly.
- Skill refactor: weekly or when hit-rate drops.
