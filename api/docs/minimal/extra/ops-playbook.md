# Ops Playbook

This doc lives in a subfolder to validate recursive indexing. It outlines a
simple operations playbook used for incident response and routine maintenance.

## Purpose

The goal is to keep operational actions consistent and auditable. Each step is
short, deterministic, and safe to repeat.

## Daily Checks

### Health endpoints

Validate core services using their health endpoints.

- `GET /health`
- `GET /ready`
- `GET /metrics`

### Error budget

Review recent error rates and confirm the budget has not been exhausted. If the
budget is low, pause risky changes.

## Incident Response

### Triage

1. Confirm the alert is real (not a false positive).
2. Identify the affected service and scope.
3. Capture recent logs and request IDs.

### Mitigation

1. Roll back the most recent deploy if the issue aligns with the deploy window.
2. Disable the noisy dependency if it is causing a cascade.
3. Apply traffic shaping only if standard controls fail.

### Resolution

1. Validate that user impact is resolved.
2. Document the root cause and mitigation steps.
3. Schedule a follow-up to prevent recurrence.

## Routine Maintenance

### Index refresh

If doc content changes frequently, rebuild the index after major updates:

```bash
curl -X POST http://127.0.0.1:8002/reindex
```

### Backups

Confirm scheduled backups complete and spot-check a restore on a staging target.

## Postmortems

Postmortems should focus on process and system design. Avoid assigning blame to
individuals and focus on correcting the factors that allowed the incident.
