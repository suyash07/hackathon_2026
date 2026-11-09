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

## After

Recorded 2026-11-09 14:05 MST, after PR #9 (`e4d4cb6`) deployed through Argo CD.

- Critical: 0 · High: 0 · Medium: 1 (was 3)
- Fixed `automountServiceAccountToken`: the pod no longer mounts a token. The app never calls the Kubernetes API.
- Fixed `readOnlyRootFs`: root filesystem is read-only. Streamlit writes only to `HOME=/tmp`, an `emptyDir`.
- Kept `singleReplica` on purpose: Streamlit keeps each session on one pod, so spreading requests
  across replicas would break uploads and session state.
