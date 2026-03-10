# Database Migration — Jira Audit

**Audit date:** 2026-03-07  
**Scope:** Migration-related tickets (MySQL, MariaDB, RDS, Aurora, DB migration) created after September 2025  
**Source:** Colppy Jira (colppy.atlassian.net)

---

## Summary

| Ticket | Summary | Type | Status | Created | Assignee |
|--------|---------|------|--------|---------|----------|
| [KAN-11967](https://colppy.atlassian.net/browse/KAN-11967) | [Discovery] Estrategia de migración y segmentación DB | Story | Done | 2025-12-09 | Ignacio Benedetti |
| [KAN-12021](https://colppy.atlassian.net/browse/KAN-12021) | Investigar implementación de Decimales en MySQL, PHP y JS | Story | Done | 2026-01-15 | Ignacio Benedetti |
| [KAN-12080](https://colppy.atlassian.net/browse/KAN-12080) | Tesoreria > Cheques y echeqs desaparecieron con fecha >31-01-2026 | Bug | Done | 2026-02-05 | Jorge Ross |
| [KAN-12084](https://colppy.atlassian.net/browse/KAN-12084) | Historia Técnica: Migración a AWS SQS - Paybook | Technical Sub-Task | In Test | 2026-02-09 | Mario Moreno |
| [KAN-12133](https://colppy.atlassian.net/browse/KAN-12133) | [MIGRATION] Migración MySQL 5.6 → MariaDB 10.11 con Estandarización de Precisión Decimal | Story | Analisis Tecnico | 2026-03-05 | — |

---

## Core Database Migration Tickets

### KAN-11967 — [Discovery] Estrategia de migración y segmentación DB

- **Created:** 2025-12-09
- **Status:** Done
- **Assignee:** Ignacio Benedetti
- **Note:** Earliest DB migration ticket in Jira. Discovery/strategy phase. Confirms migration idea started after September 2025.

### KAN-12133 — [MIGRATION] Migración MySQL 5.6 → MariaDB 10.11 con Estandarización de Precisión Decimal

- **Created:** 2026-03-05
- **Status:** Analisis Tecnico (To Do)
- **Assignee:** Unassigned
- **Scope:** MySQL 5.6 → MariaDB on RDS, decimal precision standardization (DECIMAL 15,5), PHP update
- **Labels:** `migration` `critical` `database` `mysql` `mariadb` `performance` `financial-precision` `Q1-2026`

### KAN-12021 — Investigar implementación de Decimales en MySQL, PHP y JS

- **Created:** 2026-01-15
- **Status:** Done
- **Assignee:** Ignacio Benedetti
- **Note:** Research for decimal handling; feeds into KAN-12133.

---

## Related: Tesoreria Zero-Date Bug (MySQL 8.0)

### KAN-12080 — Tesoreria > Cheques y echeqs desaparecieron con fecha >31-01-2026

- **Created:** 2026-02-05
- **Status:** Done
- **Assignee:** Jorge Ross
- **Note:** Cheques/echeqs with dates >31-01-2026 disappear. Known MySQL 8.0 zero-date compatibility issue in Tesoreria. Blocking for migration.

---

## Related: Paybook Queue Migration (not DB engine)

### KAN-12084 — Historia Técnica: Migración a AWS SQS - Paybook

- **Created:** 2026-02-09
- **Status:** In Test
- **Assignee:** Mario Moreno
- **Scope:** Laravel Queue (database driver) → AWS SQS. Removes DB as queue; does not change MySQL/MariaDB engine.

---

## Timeline (post Sept 2025)

```
2025-12-09  KAN-11967  Discovery: Estrategia de migración y segmentación DB
2026-01-15  KAN-12021  Investigar Decimales en MySQL, PHP y JS
2026-02-05  KAN-12080  Tesoreria zero-date bug (cheques >31-01-2026)
2026-02-09  KAN-12084  Migración a AWS SQS (Paybook queues)
2026-03-05  KAN-12133  [MIGRATION] MySQL 5.6 → MariaDB 10.11
```

---

## Cross-References

- [deployment-and-infra.md](../colppy-platform/deployment-and-infra.md) — Terraform Aurora MySQL 8.0 vs prod MySQL 5.6
- [database-schema.md](../colppy-platform/database-schema.md) — 207 tables, Tesoreria domain
- Production DB verified: MySQL 5.6.51-log (2026-03-06)

---

*Last updated: 2026-03-07*
