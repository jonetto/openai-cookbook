# API Reference

Colppy exposes two API systems: **Frontera** (legacy RPC envelope) and **Benjamin** (modern REST). Both are actively used in production.

## API Systems Overview

| System | Type | Endpoint | Auth | Stack |
|--------|------|----------|------|-------|
| Frontera | JSON-RPC envelope | `POST /lib/frontera2/service.php` | Dev creds (MD5) + `claveSesion` | PHP |
| Benjamin | REST | `/api/v1/{resource}` | JWT (FusionAuth) | Laravel |
| svc_settings | REST | `/{endpoint}` | JWT cookie (`token`) | NestJS |

- Source: `colppy/api-documentation/` -- `nubox-spa/colppy-benjamin/routes/` -- `colppy/svc_settings/src/`
- See [Backend Architecture](backend-architecture.md) for how these systems interconnect

---

## Frontera Envelope Format

All Frontera calls go through a **single endpoint**: `POST https://login.colppy.com/lib/frontera2/service.php`

### Request / Response Structure

```json
// REQUEST
{
  "auth": {
    "usuario": "dev_api_user@example.com",
    "password": "md5_hashed_password"
  },
  "service": {
    "provision": "ProvisionName",
    "operacion": "operation_name"
  },
  "parameters": {
    "sesion": {
      "usuario": "end_user@example.com",
      "userId": 12345,
      "claveSesion": "session_token_abc123"
    }
  }
}

// RESPONSE
{
  "success": true,
  "message": "La operacion se realizo con exito.",
  "data": {}
}
```

### Two-Layer Authentication

| Layer | Purpose | Credential |
|-------|---------|------------|
| `auth` block | Identifies the **developer/integration** | `usuario` + `password` (MD5 hash) |
| `sesion` block | Identifies the **end user** session | `usuario` + `claveSesion` (from `iniciar_colppy`) |

```
1. POST service.php { provision: "Usuario", operacion: "iniciar_colppy" } -> claveSesion
2. POST service.php { provision: "XXX", operacion: "yyy", sesion: { claveSesion } }
3. POST service.php { provision: "Usuario", operacion: "cerrar_sesion" }
```

- Dev credentials obtained from `api.colppy.com` developer portal
- See [Auth and Sessions](auth-and-sessions.md) for full details

---

## Frontera Operations by Provision

### Usuario (Auth)

| Operation | Description |
|-----------|-------------|
| `iniciar_colppy` | Login, returns `claveSesion` |
| `cerrar_sesion` | Close session |
| `validar_sesion` | Validate session is active |
| `cambiar_password` | Change password |
| `enviar_email` | Password recovery email |

### Empresa (Config)

| Operation | Description |
|-----------|-------------|
| `alta_empresa` / `alta_empresa_basica` | Create company (full / simplified) |
| `leer_empresa` / `listar_empresa` | Read / list companies |
| `editar_empresa` | Update company |
| `crear_plan_cuentas` | Create chart of accounts |
| `listar_talonarios` | List invoice books |

### Cliente (Sales - Customers)

| Operation | Description |
|-----------|-------------|
| `alta_cliente` / `editar_cliente` | Create / update customer |
| `leer_cliente` / `leer_cliente_por_cuit` | Read by ID / by CUIT |
| `listar_cliente` / `listar_cliente_totales` | List (paginated) / totals |
| `importacion_masiva_clientes` | Bulk import |
| `alta_cobro` / `editar_cobro` | Register / edit payment collection |

### FacturaVenta (Sales - Invoices)

| Operation | Description |
|-----------|-------------|
| `alta_facturaventa` / `editar_facturaventa` | Create / edit sales invoice |
| `alta_facturaventarecurrente` | Create recurring invoice |
| `leer_facturaventa` / `listar_facturasventa` | Read / list invoices |
| `leer_cobros_factura` | Get collections for invoice |
| `importar_facturas` | Import from CSV |
| `leer_link_QR` | Get AFIP QR code link |

### Proveedor (Purchases - Suppliers)

| Operation | Description |
|-----------|-------------|
| `alta_proveedor` / `editar_proveedor` | Create / update supplier |
| `leer_proveedor` / `leer_proveedor_por_cuit` | Read by ID / by CUIT |
| `listar_proveedor` | List suppliers (paginated) |

### FacturaCompra (Purchases - Invoices)

| Operation | Description |
|-----------|-------------|
| `alta_facturacompra` / `editar_facturacompra` | Create / edit purchase invoice |
| `leer_facturacompra` / `listar_facturascompra` | Read / list purchase invoices |
| `leer_pagos_factura` | Get payments for invoice |

### Tesoreria (Treasury)

| Operation | Description |
|-----------|-------------|
| `alta_cuenta` / `alta_cuenta_banco` | Create bank account / chart account |
| `alta_extracto` | Import bank statement |
| `alta_otro_cobro` / `leer_otro_cobro` | Register / read non-invoice collection |
| `listado_banco` | List banks/accounts |
| `leer_cheques_diferidos` | List deferred checks |
| `conciliar_movimientos_extractos` | Reconcile bank statements |

### Pago (Payments), Contabilidad (Accounting), Inventario (Inventory)

| Provision | Operation | Description |
|-----------|-----------|-------------|
| Pago | `alta_pago` / `detalle_pago` / `ultimo_pago` | Register / read / last payment |
| Contabilidad | `importar_asiento` / `editar_asiento` / `borrar_asiento` | Import / edit / delete journal entry |
| Contabilidad | `leer_asiento` / `listar_itemsasiento` | Read entry / list items |
| Contabilidad | `leer_saldoCuenta` / `leer_fechaiva` / `validar_cuenta` | Account balance / IVA dates / validate |
| Inventario | `alta_iteminventario` / `editar_iteminventario` | Create / edit item |
| Inventario | `leer_iteminventario` / `listar_itemsinventario` | Read / list items |
| Inventario | `alta_deposito` / `alta_remito` / `alta_ajusteinventario` | Warehouse / delivery note / stock adjust |

See [Provisiones Reference](provisiones-reference.md) for parameter schemas per operation.

---

## Reference Data

### IVA Conditions

| ID | Description | Allowed Letters |
|----|-------------|-----------------|
| 1 | Responsable Inscripto | A, B, C, E, M |
| 2 | Exento | B, C |
| 3 | Consumidor Final | B |
| 4 | Monotributista | C |
| 5 | No Responsable | B |
| 6 | Responsable No Inscripto | B |

### Comprobante Types (Sales)

| Code | ID | Description |
|------|----|-------------|
| FAC/NCC/NDC | 1/2/3 | Factura / NC / ND Comun |
| FAV/NCV/NDV | 4/5/6 | Factura / NC / ND Venta |
| FCC | 7 | Factura de Credito |
| FVC | 8 | Factura Venta Contado |

### Invoice Letter Matrix

| Issuer | Receiver | Letter |
|--------|----------|--------|
| RI | RI | A |
| RI | Mono/CF/Exento | B |
| Mono/Exento | Any | C |
| Any | Export | E |

### Invoice States

| ID | State |
|----|-------|
| 1 | Borrador |
| 3 | Aprobada |
| 4 | Anulada |
| 5 | Cobrada |
| 6 | Parc. Cobrada |

### Currencies and Countries

| ID | Currency | Country ID | Country   |
|----|----------|------------|-----------|
| 1  | ARS      | 12         | Argentina |
| 3  | USD      | 45         | Colombia  |

---

## Benjamin REST Endpoints

Base path: `/api/v1/` -- Source: `nubox-spa/colppy-benjamin/routes/api/v1/`

| Method | Path | Description |
|--------|------|-------------|
| CRUD | `/items`, `/items/{id}` | Inventory items (+ `/{id}/movements`) |
| GET | `/movements` | Stock movements |
| CRUD | `/terceros`, `/terceros/{id}` | Third parties |
| CRUD | `/pricelist`, `/pricelist/{id}` | Price lists (+ `/duplicate`, `/items`, `/customer`, `/download`) |
| GET | `/invoice` | Sales invoices |
| GET | `/purchaseinvoice` | Purchase invoices |
| PATCH | `/company/{id}` | Update company |
| POST | `/company/registry` | Register company |
| CRUD | `/empresa/retefuenteventa` | Sales withholdings (Colombia) |
| CRUD | `/empresa/reteicacompra` | Purchase withholdings (Colombia) |
| POST | `/import/suppliers/csv` | Import suppliers from CSV |
| POST | `/import/customers/csv` | Import customers from CSV |
| POST | `/import/sales_invoice/csv` | Import sales invoices from CSV |
| GET | `/import/sales_invoice/open_process` | Check open import process |
| GET | `/Gl/result-closing/close` | Close accounting period |
| GET | `/Gl/validatePeriod` | Validate inflation adjustment period |
| GET | `/Gl/download/{name}` | Download GL report |
| PATCH | `/tax/expiration/event/update/{id}` | Update tax expiration event |
| POST | `/tax/expiration/event/list` | List tax events |
| POST | `/tax/expiration/event/setup` | Save tax event setup |
| GET | `/reports` | Generate reports |
| GET | `/reportstxt` | Generate TXT report |
| GET | `/plancuentaempresa` | Search chart of accounts |
| POST | `/payment` | Register payment |
| GET | `/payment/last/{company}` | Last payment |
| POST | `/notification/mail` | Send email notification |
| POST | `/webhooks/paypertic/payments` | Paypertic webhook |

CRUD = standard GET (list), POST (create), GET/{id}, PUT/{id}, DELETE/{id}

---

## svc_settings Endpoints

Source: `colppy/svc_settings/src/`

### Auth (FusionAuth)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/login` | Authenticate (`{ username, password }`) |
| GET | `/session-info` | Decode JWT from cookie `token` |
| POST | `/finish-onboarding` | Complete company setup (company_id, cuit, iva_condition, etc.) |

### Dashboard BFF

| Method | Path | Description |
|--------|------|-------------|
| GET/PUT | `/charts-settings/{idEmpresa}/{idUsuario}` | Dashboard preferences |
| GET | `/banks-chart/{idEmpresa}/{filtro}` | Cash & banks chart |
| GET | `/income-expenses-chart/{idEmpresa}/{filtro}` | Income vs expenses |
| GET | `/unpaid-invoices-chart/{idEmpresa}/{filtro}` | Unpaid purchase invoices |
| GET | `/receivable-invoices-chart/{idEmpresa}/{filtro}` | Receivable sales invoices |
| GET | `/distribution-expenses-chart/{idEmpresa}/{filtro}` | Expense distribution |
| GET | `/card-sales/{idEmpresa}` | Sales KPI |
| GET | `/card-purchases/{idEmpresa}` | Purchases KPI |
| GET | `/card-pending-payment/{idEmpresa}` | Pending payment KPI |
| GET | `/card-pending-collection/{idEmpresa}` | Pending collection KPI |
| GET | `/first-steps/{idUsuario}/{idEmpresa}` | Onboarding progress |
| PUT | `/first-steps-state/{idUsuario}` | Update onboarding state |
| GET | `/companies/invoice-books/{companyId}` | Invoice books |

Filter values for `{filtro}`: `weekly`, `monthly`, `quarterly`, `yearly`

### Internal Frontera Bridge

svc_settings calls Frontera via `HttpCustomService` (`colppy/svc_settings/src/providers/http/http.service.ts`):

- Env: `FRONTERA_API_URL=https://login.colppy.com/lib/frontera2/service.php`
- Internal calls set `claveSesion: null` (service-to-service bypass)
- Uses `rejectUnauthorized: false` for TLS (dev self-signed certs)

---

## Gotchas

### Single Entry Point
- **All** Frontera operations POST to the same URL; `provision` + `operacion` determines the action
- No RESTful paths -- every operation is a POST to `service.php`

### Case-Sensitive Operation Names
- `listar_facturasCompra` -- camelCase "C" (purchase list)
- `listar_facturasventa` -- all lowercase (sales list)
- Mismatched casing silently fails or returns an error

### Date Format Inconsistency
- Sales (Frontera): `dd-mm-yyyy` -- `"fechaFactura": "20-01-2026"`
- Purchases (Frontera): `yyyy-mm-dd` -- `"fechaFactura": "2026-01-20"`

### Parameter Naming Inconsistencies
- Sales items: `itemsFactura` -- Purchases items: `items`
- Collection methods: `mediospagos` (NOT `fondos`)
- Collection invoices: `cobros` (NOT `itemsAplicados`)
- Receipt: `nroRecibo1` + `nroRecibo2` (NOT `nroRecibo`)

### Auth Block Always Required
- The `auth` block with dev creds is required even for `iniciar_colppy`
- Internal svc_settings calls bypass `claveSesion` with `null`

### Pagination Varies by Provision
- FacturaVenta: `start` + `limit` (offset)
- Cliente: `pagina` + `registrosPorPagina` (page-based)
- Empresa: `start` + `limit` + `filter` string

### Response Field Naming
- `totalaplicado` / `saldoaaplicar` -- no separators, concatenated words
- `has_NC` -- underscore + uppercase
- Field casing inconsistent across provisiones

### Factura Electronica
- Date window: 5 days back to 1 day forward
- Must set `labelfe: "Factura Electronica"` to trigger e-invoicing
- Invoices with CAE cannot be edited
- NC/ND require `extra_data.comp_asociados` linking to original invoice

### FVC vs FAV
- `FVC` bundles collection at creation (`ItemsCobro` array, auto-sets `Cobrada`)
- `FAV` requires separate `Cliente/alta_cobro` call

### Benjamin vs Frontera Overlap
- Some operations exist in both; Benjamin preferred for new integrations
- Benjamin does not cover all Frontera operations

See [Database Schema](database-schema.md) for the underlying data model.
