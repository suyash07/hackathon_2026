# Demo story — team hackathon

## Before

Recorded 2026-11-09 13:56 MST, right after the first GitOps deploy (`512dfd8`).

Radar Checks: https://app.radarhq.io/checks?scope=DsM8vreed6w&namespace=team-hackathon

- Critical: 0
- High: 0
- Medium: 3
  - `automountServiceAccountToken` (Security): Deployment/team-hackathon/app
  - `readOnlyRootFs` (Security): Deployment/team-hackathon/app
  - `singleReplica` (Reliability): Deployment/team-hackathon/app
