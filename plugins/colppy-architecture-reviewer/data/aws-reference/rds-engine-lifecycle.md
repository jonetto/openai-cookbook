# AWS RDS Engine Lifecycle
> Source: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraMySQLReleaseNotes/AuroraMySQL.release-calendars.html, https://docs.aws.amazon.com/AmazonRDS/latest/AuroraPostgreSQLReleaseNotes/aurorapostgresql-release-calendar.html, https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MariaDB.Concepts.VersionMgmt.html, https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MySQL.Concepts.VersionMgmt.html | Fetched: 2026-03-08

## Aurora MySQL
| Version | Engine Compat. | Standard Support End | Extended Support End |
|---|---|---|---|
| Aurora MySQL 3 | MySQL 8.0 | 30 April 2028 | 31 July 2029 |
| Aurora MySQL 2 (deprecated) | MySQL 5.7 | 31 October 2024 | 28 February 2027 |
| Aurora MySQL 1 (deprecated) | MySQL 5.6 | 28 February 2023 | N/A |

- **LTS versions**: Aurora MySQL 3.04.x, 3.10.x (3-year minor version stability, or until major version EOL)
- Aurora MySQL 2 entered extended support 1 Nov 2024 (charges from 1 Dec 2024)

## Aurora PostgreSQL
| Version | Engine Compat. | Standard Support End | Extended Support End |
|---|---|---|---|
| 17 | PostgreSQL 17 | 28 February 2030 | 28 February 2033 |
| 16 | PostgreSQL 16 | 28 February 2029 | 28 February 2032 |
| 15 | PostgreSQL 15 | 29 February 2028 | 28 February 2031 |
| 14 | PostgreSQL 14 | 28 February 2027 | 29 February 2030 |
| 13 | PostgreSQL 13 | 28 February 2026 | 28 February 2029 |
| 12 | PostgreSQL 12 | 28 February 2025 | 29 February 2028 |
| 11 (deprecated) | PostgreSQL 11 | 29 February 2024 | 31 March 2027 |

- Extended support charges start 1 month after standard support ends
- LTS versions available for PostgreSQL 14, 15, 16

## RDS MariaDB
| Major Version | Community EOL | RDS Standard Support End | Notes |
|---|---|---|---|
| MariaDB 11.8 | June 2030 | June 2030 | Latest major version |
| MariaDB 11.4 | May 2029 | May 2029 | LTS |
| MariaDB 10.11 | 16 February 2028 | February 2028 | LTS (team's proposed target) |
| MariaDB 10.6 | 6 July 2026 | August 2026 | Approaching EOL |
| MariaDB 10.5 | 24 June 2025 | August 2026 | Extended by AWS past community EOL |

- Deprecated: MariaDB 10.0, 10.1, 10.2, 10.3
- No extended support program for RDS MariaDB (support ends at standard support date)

## RDS MySQL
| Major Version | Standard Support End | Extended Support End | Notes |
|---|---|---|---|
| MySQL 8.4 | 31 July 2029 | 31 July 2032 | Current recommended |
| MySQL 8.0 | 31 July 2026 | 31 July 2029 | Colppy's current engine |
| MySQL 5.7 (ext. support only) | 29 February 2024 | 28 February 2027 | No new standard deployments |

- Upgrade paths: MySQL 5.7 -> 8.0 -> 8.4
- MySQL 9.3, 9.4, 9.5 available in Preview only (Innovation releases, not for production)

## Key Migration Notes

### MariaDB on Aurora Serverless v2: NOT SUPPORTED
**Aurora Serverless v2 only supports Aurora MySQL (MySQL 8.0 compat) and Aurora PostgreSQL (13-17).** MariaDB is not an Aurora engine at all -- it is only available as standard RDS (non-Aurora). This means:
- A migration from Aurora MySQL 8.0 to MariaDB 10.11 would require leaving Aurora Serverless v2
- The team would need to provision standard RDS MariaDB instances (not serverless)
- This loses Aurora's serverless auto-scaling, fast failover, and storage auto-growth capabilities

### In-place upgrade support
- **Aurora MySQL 2 -> 3**: In-place major version upgrade supported (MySQL 5.7 -> 8.0 compatibility)
- **Aurora PostgreSQL**: In-place major version upgrades supported between consecutive versions (e.g., 14 -> 15 -> 16)
- **RDS MySQL -> MariaDB**: No in-place upgrade path. Requires dump+restore or DMS migration
- **Aurora MySQL -> RDS MariaDB**: No in-place path. Requires snapshot export + reimport or DMS replication

### MySQL to MariaDB migration constraints
- MariaDB 10.11 is broadly wire-compatible with MySQL 8.0 for DML operations
- Stored procedures, triggers, and system tables may have incompatibilities
- `caching_sha2_password` (MySQL 8.0 default auth) is not supported in MariaDB -- must switch to `mysql_native_password` or MariaDB's `ed25519`
- JSON column type: MariaDB uses LONGTEXT-based JSON (alias), not MySQL's binary JSON format
- Window functions and CTEs are compatible, but optimizer hints differ
- GIS/spatial functions have naming differences
