# Backend Architecture

> Three-layer backend: Frontera 2.0 (legacy PHP gateway), Benjamin (Laravel modern API), NestJS microservices + Lambda functions.

---

## Architecture Diagram

```text
                        +--------------------------+
                        |       Clients            |
                        | (Vue SPA, Mobile, API)   |
                        +------------+-------------+
                                     |
                                     v
+--------------------------------------------------------------------+
|                      Frontera 2.0  (API Gateway)                   |
|                  nubox-spa/colppy-app/lib/frontera2/               |
|                                                                    |
|  +---------------------------+    +----------------------------+   |
|  | Provisiones MIGRADAS      |    | Provisiones LEGACY         |   |
|  |                           |    |                            |   |
|  | - Inventario              |    | - Afip                     |   |
|  | - Tax                     |    | - FacturaCompra            |   |
|  | - PriceList               |    | - FacturaVenta (partial)   |   |
|  | - Cliente                 |    | - Paybook                  |   |
|  | - Tercero                 |    | - Pos                      |   |
|  | - Contabilidad            |    | - Tesoreria                |   |
|  | - Empresa                 |    | - Pago                     |   |
|  +------------+--------------+    | - BillStub                 |   |
|               |                   | - Location, Moneda, etc.   |   |
|               | BenjaminConnector +-------------+--------------+   |
|               | (Guzzle HTTP)                   |                  |
+--------------------------------------------------------------------+
                |                                 |
                v                                 v
   +------------------------+           +----------------+
   |       Benjamin          |           |     MySQL      |
   |    (Laravel 5.4)        |           |   (Direct DAO) |
   |                         |           +----------------+
   |  - OAuth2 (Passport)    |
   |  - 207 Eloquent models  |
   |  - REST /api/v1/*       |
   |  - Modules:             |
   |    Core, AR, AP,        |
   |    GL, ST, TX           |
   +------------------------+
                |
                v
         +------------+
         |   MySQL     |
         | (same DB)   |
         +------------+

   +--------------------------------------------------+
   |          NestJS Microservices (Layer 3)           |
   |  svc_settings, svc_security, svc_afip,           |
   |  svc_inventory, svc_sales, svc_mercado_pago,     |
   |  svc_importer_data, svc_utils, ...               |
   +--------------------------------------------------+

   +--------------------------------------------------+
   |          Lambda Functions (Layer 4)               |
   |  20 serverless functions (AWS Lambda / SAM)       |
   +--------------------------------------------------+
```

**Key insight**: Frontera and Benjamin share the SAME MySQL database. Benjamin uses Eloquent ORM; Frontera uses raw DAOs. There is no schema isolation.

---

## Layer 1: Frontera 2.0 (Legacy Gateway)

### Entry Point

- **File**: `nubox-spa/colppy-app/lib/frontera2/service.php`
- **Version**: `FM_VERSION = '1.6.21.26'`
- **PHP**: 5.6 (legacy, no type hints)

### Request Dispatch Flow

1. `service.php` bootstraps environment, defines paths (`SERVICEPATH`, `CONFIGPATH`, `INCLUDEPATH`, `INITPATH`, `LIBPATH`)
2. Loads all exception classes, helpers, and system libraries via sequential `include_once` calls
3. `MainController::getInstance()->service()` is called (singleton pattern with `register_shutdown_function`)
4. `WebserviceManager` initializes, `WebserviceRouter` parses the incoming request
5. Dispatcher selection cascade:

| Priority | Condition | Dispatcher |
|----------|-----------|------------|
| 1 | Custom content-type header | Content-specific dispatcher (dynamic class load) |
| 2 | URL contains service/operation | `RESTDispatcher` |
| 3 | CLI invocation (`php_sapi_name() == 'cli'`) | `CommandLineDispatcher` |
| 4 | Empty request body | `DefaultDispatcher` (debug views) |
| 5 | `SOAPAction` header present | `SOAPDispatcher` |
| 6 | `Content-Type: application/soap+xml` | `SOAPDispatcher` |
| 7 | `Content-Type: application/json` | `JSONDispatcher` |
| 8 | `Content-Type: text/xml` | `XMLDispatcher` |
| 9 | Body matches SOAP envelope regex | `SOAPDispatcher` |
| 10 | Body parses as JSON | `JSONDispatcher` |
| 11 | Body parses as XML | `XMLDispatcher` |
| -- | None match | `InvalidRequestContentException` |

1. Dispatcher loads the Provision class from `resources/Provisiones/{ProvisionName}/`
1. Provision reads `operacion` from request and executes the corresponding delegate

### Key Directories

| Directory | Purpose |
|-----------|---------|
| `nubox-spa/colppy-app/lib/frontera2/` | Gateway core: service.php, config, controllers |
| `nubox-spa/colppy-app/lib/frontera2/include/controller/` | `MainController.php` (singleton dispatcher) |
| `nubox-spa/colppy-app/lib/frontera2/include/dispatcher/` | 6 dispatcher types: REST, JSON, XML, SOAP, CLI, Default |
| `nubox-spa/colppy-app/resources/Provisiones/` | 32 business modules (one dir each) |
| `nubox-spa/colppy-app/resources/Provisiones/ColppyCommon/` | Shared DAOs, exceptions, libs |
| `nubox-spa/colppy-app/lib/BenjaminConnector/` | HTTP bridge to Benjamin API |
| `nubox-spa/colppy-app/lib/OAuth/` | OAuth token management |

### Request Format (JSON Envelope)

```json
{
  "auth": {
    "sign": "<md5-hash>",
    "empresa_id": 12345,
    "usuario": "user@email.com",
    "claveSesion": "<session-key>"
  },
  "service": {
    "provision": "FacturaVenta",
    "operacion": "listar_facturasventa"
  },
  "parameters": {
    "filtros": { ... }
  }
}
```

See [API Reference](api-reference.md) for full envelope format.

### All 32 Provisiones

```text
Afip           Archivo        BillStub       Cliente
ColppyCommon   CondicionIVA   CondicionPago  Contabilidad
Desarrollador  Empresa        FacturaCompra  FacturaVenta
Help           Importer       Integracion    Inventario
Location       Moneda         Notificaciones Pago
Paybook        Pos            PriceList      Proveedor
Receipt        Referido       Retencion      Socio
Tax            Tercero        Tesoreria      Usuario
```

See [Provisiones Reference](provisiones-reference.md) for business module details.

---

## Layer 2: Benjamin (Modern Laravel API)

### Overview

| Property | Value |
|----------|-------|
| Path | `nubox-spa/colppy-benjamin/` |
| Framework | Laravel 5.4 |
| Auth | OAuth2 via Laravel Passport |
| Database | 207 Eloquent models, 109 migrations |
| API base | `/api/v1/` |
| Pattern | Repository + Service + Controller layers |

### Database Modules

| Module | Domain | Tables | Key Tables |
|--------|--------|--------|------------|
| Core | Company/User mgmt | 31 | `empresa`, `usuario`, `usuario_sesion`, `plan`, `currency`, `rates` |
| AR | Accounts Receivable / Sales | 24 | `ar_factura`, `ar_cliente`, `ar_detalle_factura`, `ar_cobro`, `ar_recurrencia` |
| AP | Accounts Payable / Purchases | 19 | `ap_factura`, `ap_proveedor`, `ap_detalle_factura`, `ap_pago` |
| GL | General Ledger / Accounting | 15 | `gl_asiento`, `gl_detalle_asiento`, `gl_plan_cuenta`, `gl_conceptos`, `diario` |
| ST | Stock / Inventory | 10 | `st_item`, `st_movimiento`, `st_price_list`, `st_price_list_item` |
| TX | Tax / Impuestos | 8 | Tax expirations, events, country configs |

See [Database Schema](database-schema.md) for shared MySQL access.

### Key REST Endpoints

| Route | Methods | Controller | Provision Proxy |
|-------|---------|-----------|-----------------|
| `/api/v1/terceros` | GET, POST, PUT, DELETE | `TerceroController` | Cliente, Proveedor, Tercero |
| `/api/v1/items` | GET, POST, PUT, DELETE | `ItemController` | Inventario |
| `/api/v1/items/{id}/movements` | GET | `ItemController` | Inventario |
| `/api/v1/movements` | GET | `MovementController` | Inventario |
| `/api/v1/pricelist` | GET, POST, PATCH | `PriceListController` | PriceList |
| `/api/v1/pricelist/{id}/items` | GET, POST | `PriceListController` | PriceList |
| `/api/v1/pricelist/{id}/duplicate` | POST | `PriceListController` | PriceList |
| `/api/v1/pricelist/{id}/customer` | POST, PUT | `PriceListController` | PriceList |
| `/api/v1/tax/expiration/*` | POST, PATCH | `TaxController` | Tax |
| `/api/v1/plancuentaempresa` | GET | `PlanAccountController` | Contabilidad |
| `/api/v1/Gl/*` | various | `Gl/` namespace | Contabilidad |
| `/api/v1/company/{id}` | PATCH | `CompanyController` | Empresa |
| `/api/v1/empresa/retefuenteventa` | GET, POST, DELETE | `SalesAccountRetefuenteController` | Empresa |
| `/api/v1/empresa/reteicacompra` | GET, POST, DELETE | `PurchaseAccountReteicaController` | Empresa |
| `/api/v1/invoice/` | GET | `SalesInvoiceController` | FacturaVenta (list only) |
| `/api/v1/purchaseinvoice/` | GET | `PurchaseInvoiceController` | FacturaCompra (list only) |
| `/api/v1/receipt` | GET | `ReceiptController` | Receipt |
| `/api/v1/payment/last/{company}` | GET | `PaymentController` | Usuario |
| `/api/v1/import/*` | various | `Import/` namespace | Importer |
| `/api/v1/Meli/*` | various | `Meli/` namespace | Integracion |
| `/api/v1/bill_stubs` | GET, POST | `BillStubController` | BillStub |
| `/api/v1/reports` | GET | `ReportsController` | -- |
| `/api/v1/fceEmpresa` | GET | `FceEmpresaController` | -- |
| `/api/v1/notification/mail` | POST | `NotificationController` | -- |
| `/api/v1/webhooks/*` | various | `Webhook/` namespace | -- |

### BenjaminConnector

- **File**: `nubox-spa/colppy-app/lib/BenjaminConnector/BenjaminConnector.php`
- **Transport**: Guzzle HTTP client
- **Auth**: OAuth2 tokens stored in `usuario_external_tokens` table
- **Token refresh**: Automatic when expired (synchronous, blocks request)

```php
// Constructor loads user from UsuarioDAO, stores user_id
$connector = new BenjaminConnector($parametros->sesion->usuario);

// HTTP methods — all accept $idEmpresa for company-scoped requests
$items  = $connector->get('/items', $params, $idEmpresa);
$result = $connector->post('/items', $body, [], $idEmpresa);
$result = $connector->put('/items/' . $id, $data, $idEmpresa);
$result = $connector->patch('/pricelist/' . $id, $data, $idEmpresa);
$result = $connector->delete('/pricelistclient', $params);

// Error handling
try {
    $data   = $connector->get('/items', $params, $idEmpresa);
    $result = MessageHandler::handling($data);
} catch (BenjaminException $exception) {
    return ErrorHandler::handling($exception);
}
```

---

## Migrated vs Legacy Provisiones

| Status | Provisions | Access Path |
|--------|-----------|-------------|
| **Fully migrated** | Inventario, Tax, PriceList, Cliente, Tercero, Contabilidad, Empresa | Frontera -> BenjaminConnector -> Benjamin REST -> Eloquent -> MySQL |
| **Partially migrated** | FacturaVenta (list), FacturaCompra (list), Receipt (read), Usuario (last payment), BillStub (list/create) | List/read via Benjamin; create/edit still in Frontera DAO |
| **Legacy (not migrated)** | Afip, Paybook, Pos, Tesoreria, Pago, Location, Moneda, CondicionIVA, CondicionPago, Help, Archivo, Notificaciones, Referido, Socio, Desarrollador, Retencion | Frontera -> DAO -> MySQL direct |

---

## Layer 3: NestJS Microservices

| Service | Path | Purpose | Key Modules |
|---------|------|---------|-------------|
| svc_settings | `colppy/svc_settings/` | FusionAuth bridge, company config, BFF | `fusionauth/`, `companies/`, `bff/`, `graphs/` |
| svc_security | `colppy/svc_security/` | RBAC permissions, product access | `auth/`, `products/`, `migrations/` |
| svc_afip | `colppy/svc_afip/` | ARCA/AFIP tax web services, voucher processing | `afip-web-services/`, `aws-sqs/`, `circuit-breaker/` |
| svc_inventory | `colppy/svc_inventory/` | Inventory domain service | `database/`, `example/` |
| svc_sales | `colppy/svc_sales/` | Sales domain service | `database/`, `example/` |
| svc_mercado_pago | `colppy/svc_mercado_pago/` | Mercado Pago payment integration | `mercadopago/`, `accounts/`, `aws-sqs/` |
| svc_importer_data | `colppy/svc_importer_data/` | Data import orchestration, bulk imports | `imports/`, `mail/`, `aws-sqs/`, `bff/` |
| svc_utils | `colppy/svc_utils/` | Utility services, CRM integration | -- |
| svc_backoffice | `colppy/svc_backoffice/` | Internal backoffice operations | -- |
| svc_importer | `colppy/svc_importer/` | Legacy importer service | -- |
| svc_integracion_crm | `colppy/svc_integracion_crm/` | CRM integration service | -- |
| svc_integracion_paybook | `colppy/svc_integracion_paybook/` | Paybook banking integration | -- |
| svc_internal_api | `colppy/svc_internal_api/` | Internal API layer | -- |
| svc_reporter | `colppy/svc_reporter/` | Report generation | -- |
| svc_fusionauth | `colppy/svc_fusionauth/` | FusionAuth discovery/config | -- |
| svc_archetype_nestjs | `colppy/svc_archetype_nestjs/` | Template for new NestJS services | -- |

### FusionAuth Bridge (svc_settings)

`svc_settings` bridges FusionAuth (modern IdP) with the legacy Frontera session system:

1. Decodes FusionAuth JWT to extract user `sub` claim
2. Fetches user profile from FusionAuth API using `FUSIONAUTH_AUTHORIZATION_KEY`
3. Queries the SAME MySQL database via raw SQL (6+ JOINs across `usuario`, `empresa`, `usuario_empresa`, `plan`, `usuario_sesion`)
4. Returns unified session info including plan, company, roles, IVA conditions, IIBB jurisdictions

**File**: `colppy/svc_settings/src/fusionauth/services/fusionauth.service.ts`

See [Auth and Sessions](auth-and-sessions.md) for session validation details.

---

## Layer 4: Lambda Functions (20)

### Application Lambdas

| Lambda | Path | Purpose |
|--------|------|---------|
| svc_agip_lambda | `colppy/svc_agip_lambda/` | AGIP (Buenos Aires tax authority) integration |
| svc_api_internal_lambda | `colppy/svc_api_internal_lambda/` | Internal API gateway |
| svc_api_public_lambda | `colppy/svc_api_public_lambda/` | Public API gateway |
| svc_authorization_lambda | `colppy/svc_authorization_lambda/` | Auth/authorization checks |
| svc_calendar_events_lambda | `colppy/svc_calendar_events_lambda/` | Tax calendar event processing |
| svc_create_database_psql_lambda | `colppy/svc_create_database_psql_lambda/` | PostgreSQL database provisioning |
| svc_file_validator_lambda | `colppy/svc_file_validator_lambda/` | File upload validation |
| svc_insert_imports_lambda | `colppy/svc_insert_imports_lambda/` | Bulk import record insertion |
| svc_mandrill_notification_lambda | `colppy/svc_mandrill_notification_lambda/` | Mandrill email notifications |
| svc_parser_lambda | `colppy/svc_parser_lambda/` | Data parsing/transformation |
| svc_product_assistant_lambda | `colppy/svc_product_assistant_lambda/` | AI product assistant |
| svc_public_webhooks_lambda | `colppy/svc_public_webhooks_lambda/` | Public webhook receiver |
| svc_slackassistant_lambda | `colppy/svc_slackassistant_lambda/` | Slack bot/assistant |
| svc_archetype_lambda | `colppy/svc_archetype_lambda/` | Lambda template/archetype |

### Infrastructure Lambdas

| Lambda | Path | Purpose |
|--------|------|---------|
| inf_SNSToSlack_lambda_lambda | `colppy/inf_SNSToSlack_lambda_lambda/` | SNS -> Slack alert forwarding |
| inf_eks_auto_shutdown_startup_lambda | `colppy/inf_eks_auto_shutdown_startup_lambda/` | EKS cluster auto start/stop |
| inf_rds_auto_shutdown_startup_lambda | `colppy/inf_rds_auto_shutdown_startup_lambda/` | RDS instance auto start/stop |
| sas-colppy-auth-lambda | `colppy/sas-colppy-auth-lambda/` | SAS auth layer |
| sas-colppy-cloudops-rdsrestoretostaging-lambda | `colppy/sas-colppy-cloudops-rdsrestoretostaging-lambda/` | RDS prod -> staging restore |
| sas-colppy-commandManagement-lambda | `colppy/sas-colppy-commandManagement-lambda/` | Long-running command dispatch |

---

## Key Files Reference

| Purpose | File Path |
|---------|----------|
| Frontera entry point | `nubox-spa/colppy-app/lib/frontera2/service.php` |
| Main controller (singleton) | `nubox-spa/colppy-app/lib/frontera2/include/controller/MainController.php` |
| REST dispatcher | `nubox-spa/colppy-app/lib/frontera2/include/dispatcher/rest/RESTDispatcher.php` |
| Benjamin connector | `nubox-spa/colppy-app/lib/BenjaminConnector/BenjaminConnector.php` |
| Benjamin exception | `nubox-spa/colppy-app/lib/BenjaminConnector/Exceptions/BenjaminException.php` |
| Benjamin routes (v1) | `nubox-spa/colppy-benjamin/routes/api/v1/api.php` |
| Session validation | `nubox-spa/colppy-app/resources/Provisiones/ColppyCommon/common/UsuarioCommon.php` |
| Session DAO | `nubox-spa/colppy-app/resources/Provisiones/ColppyCommon/persistencia/UsuarioDAO.php` |
| Token DAO | `nubox-spa/colppy-app/resources/Provisiones/ColppyCommon/persistencia/TokenDAO.php` |
| Abstract DAO | `nubox-spa/colppy-app/resources/Provisiones/ColppyCommon/persistencia/AbstractDAO.php` |
| Auth bridge service | `colppy/svc_settings/src/fusionauth/services/fusionauth.service.ts` |
| Frontera request builder | `colppy/svc_settings/src/providers/http/http.service.ts` |

---

## Environment Configuration

### Frontera Constants (service.php)

```php
define('FM_ENVIRONMENT', 'testing');
define('FM_VERSION', '1.6.21.26');
define('SERVICEPATH', dirname(__FILE__) . '/');
define('CONFIGPATH', SERVICEPATH . 'config/');
define('INCLUDEPATH', SERVICEPATH . 'include/');
define('INITPATH', SERVICEPATH . 'init/');
define('LIBPATH', SERVICEPATH . 'lib/');
```

### Benjamin Connector (.env)

```bash
BENJAMIN_URL=https://local.benjamin2.com/
BENJAMIN_CLIENT_ID=8
BENJAMIN_CLIENT_SECRET=<secret>
```

### FusionAuth (svc_settings)

```bash
FUSIONAUTH_URL=<fusionauth-instance-url>
FUSIONAUTH_AUTHORIZATION_KEY=<api-key>
```

---

## Gotchas

- **PHP 5.6 in colppy-app** -- no type hints, no strict types, no return types. All Provision code is untyped.
- **Shared MySQL database** -- Frontera DAOs and Benjamin Eloquent models read/write the SAME tables. No schema isolation. Concurrent writes from both layers can conflict.
- **Dual DB access patterns** -- Frontera uses raw PDO via `AbstractDAO` -> `MysqlDB.php` (`snddb` library). Benjamin uses Eloquent ORM. NestJS services use TypeORM with raw SQL queries. Three different DB access patterns against one schema.
- **BenjaminConnector adds network latency** -- every migrated operation goes Frontera -> Guzzle HTTP -> Benjamin REST -> Eloquent -> MySQL instead of direct DAO -> MySQL.
- **Session validation in UsuarioCommon** -- `autenticarUsuarioAPI()` supports two auth paths: OAuth (`$parametros->oauth`) and session-based (`$parametros->sesion->usuario` + `$parametros->sesion->claveSesion`). Both ultimately call `UsuarioDAO->validar_sesion()`. Session auth can be disabled globally via `AUTENTICACION_ACTIVADA` constant.
- **FusionAuth service uses raw SQL** -- `fusionauth.service.ts` in `svc_settings` builds a large raw SQL query (6+ JOINs across `usuario`, `empresa`, `usuario_empresa`, `plan`) instead of using TypeORM relations. Fragile to schema changes.
- **Partial migrations exist** -- FacturaVenta and FacturaCompra list via Benjamin but create/edit via Frontera DAO. Always check which path handles a given operation.
- **Case-sensitive operation names** -- `listar_facturasCompra` (camelCase `C`) vs `listar_facturasventa` (all lowercase). No consistent convention across Provisiones.
- **OAuth token storage** -- BenjaminConnector stores tokens in `usuario_external_tokens` with manual expiry checks. Token refresh is synchronous and blocks the request.
- **MainController is a singleton** -- `MainController::getInstance()` with `register_shutdown_function` for fatal error handling. Not thread-safe.
- **No API versioning in Frontera** -- Benjamin has `/api/v1/` but Frontera provisions have no version namespace. Breaking changes require coordination.
- **Dispatcher detection is fragile** -- `MainController.service()` cascades through 11 content-type checks (SOAP headers, JSON body parsing, XML regex). Malformed requests can hit the wrong dispatcher.
- **`service.php` accepts GET and POST** -- but production uses POST exclusively. GET is only for debug views (`?xml`, `?json`, `?wsdl`) when `FM_DEBUG_MODE=true`.

---

## Cross-References

- [Provisiones Reference](provisiones-reference.md) -- 32 business modules in detail
- [API Reference](api-reference.md) -- API contracts and envelope format
- [Auth and Sessions](auth-and-sessions.md) -- Dual auth system (FusionAuth + legacy sessions)
- [Repo Directory](repo-directory.md) -- Full repo listing (108 repositories)
- [Database Schema](database-schema.md) -- 207 tables by domain
