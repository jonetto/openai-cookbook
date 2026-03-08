# AWS Service Deprecations — Colppy Stack
> Source: AWS documentation and announcements | Fetched: 2026-03-08

## Active Deprecations
| Service | What's Deprecated | Deadline | Impact on Colppy |
|---|---|---|---|
| Aurora MySQL | Aurora MySQL 2 (MySQL 5.7 compat) — extended support only | 28 Feb 2027 (ext. support end) | Colppy runs Aurora MySQL 8.0 (version 3) — no impact |
| Aurora PostgreSQL | Aurora PostgreSQL 12 — extended support only | 29 Feb 2028 (ext. support end) | Colppy runs PostgreSQL 15.12 — no impact |
| Aurora PostgreSQL | Aurora PostgreSQL 13 — standard support ending | 28 Feb 2026 (std. support end) | Must upgrade to 14+ if running PG 13 clusters |
| EKS | Kubernetes 1.29 — extended support only | 23 Mar 2026 (ext. support end) | Verify current EKS version; upgrade to 1.32+ recommended |
| EKS | Kubernetes 1.30 — extended support only | 23 Jul 2026 (ext. support end) | Plan upgrade path if running 1.30 |
| EKS | Kubernetes 1.31 — extended support only | 26 Nov 2026 (ext. support end) | Standard support ended Nov 2025 |
| Lambda | Node.js 18 runtime (`nodejs18.x`) | Deprecated Sep 2025 | Migrate any Node.js 18 functions to nodejs20.x or nodejs22.x |
| Lambda | Python 3.9 runtime (`python3.9`) | Deprecated Dec 2025 | Migrate any Python 3.9 functions to python3.10+ |
| RDS MySQL | MySQL 5.7 — extended support only | 28 Feb 2027 (ext. support end) | No impact if Colppy uses Aurora MySQL 8.0 |
| RDS MariaDB | MariaDB 10.5 — community EOL passed | Aug 2026 (RDS support end) | Relevant only if MariaDB migration is pursued |

## Recently Completed Deprecations
| Service | What | Completed | Notes |
|---|---|---|---|
| Aurora MySQL | Aurora MySQL 1 (MySQL 5.6) | Feb 2023 | Fully removed |
| Aurora PostgreSQL | Aurora PostgreSQL 11 | Feb 2024 (std. support) | Extended support until Mar 2027 |
| Lambda | Node.js 16 runtime | Jun 2024 | Block on create/update applied |
| Lambda | Node.js 14 runtime | Dec 2023 | Fully blocked |
| Lambda | Python 3.8 runtime | Oct 2024 | Block on create/update applied |
| Lambda | Python 3.7 runtime | Dec 2023 | Fully blocked |
| Lambda | Java 8 (original AL1) | Jan 2024 | Must use java8.al2 |
| RDS MariaDB | MariaDB 10.3 | Deprecated | No longer available for new instances |
| EKS | Kubernetes 1.28 and earlier | Various | No longer in any support tier |

## Upcoming Changes (Pre-Announced)
| Service | Change | Expected Date | Impact |
|---|---|---|---|
| Lambda | Amazon Linux 2 EOL — affects java8.al2, java11, java17, python3.10, python3.11 runtimes | 30 Jun 2026 | AWS will release AL2023 variants for Java 8/11/17 before Q2 2026; plan migration |
| Lambda | Node.js 20 deprecation | 30 Apr 2026 | Migrate to nodejs22.x; block on create Aug 2026, block on update Sep 2026 |
| Lambda | Python 3.10 deprecation | 31 Oct 2026 | Migrate to python3.11+; block on create Nov 2026 |
| RDS MySQL | MySQL 8.0 standard support end | 31 Jul 2026 | Extended support available until Jul 2029; plan upgrade to 8.4 |
| RDS MariaDB | MariaDB 10.6 standard support end | Aug 2026 | If pursuing MariaDB, use 10.11 or 11.4 |
| EKS | Kubernetes 1.32 standard support end | 23 Mar 2026 | Upgrade to 1.33+ for continued standard support |
| Aurora PostgreSQL | PostgreSQL 14 standard support end | 28 Feb 2027 | Plan upgrade to PG 15 or 16 |
| CloudFront | No active deprecations identified | — | CloudFront functions and Lambda@Edge both fully supported |
| ECS Fargate | No active deprecations identified | — | Fargate platform versions remain supported |
| S3 | No active deprecations identified | — | Path-style URLs deprecated for new buckets (virtual-hosted style required) |
| ECR | No active deprecations identified | — | Service fully supported |
| Secrets Manager | No active deprecations identified | — | Service fully supported |
| CodeDeploy | No active deprecations identified | — | Service fully supported |
