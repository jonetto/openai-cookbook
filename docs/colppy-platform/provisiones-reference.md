# Provisiones Reference

> Map of 32 top-level Provisiones folders in the Frontera gateway: 31 business modules + `ColppyCommon` shared infrastructure.

---

## What a Provision Is

- Feature module in Frontera 2.0 -- equivalent to a bounded context in DDD
- Each provision handles one business domain (invoicing, customers, tax, inventory, etc.)
- Located at: `nubox-spa/colppy-app/resources/Provisiones/<Name>/`
- Accessed via Frontera API: `{ "service": { "provision": "Name", "operacion": "op_name" } }`
- Version scheme: `<Name>/<Version>/` (typically `1_0_0_0/`) -- allows backward-compatible evolution
- The dispatcher PHP file maps `operacion` strings directly to delegate method calls
- `ColppyCommon/` is **not** a provision -- it is shared infrastructure (DAOs, utils, validators)

---

## Directory Pattern

```text
Provisiones/
├── <Name>/
│   └── 1_0_0_0/
│       ├── config.php                 <- Constants: FM_SERVICES_FOLDER, paths
│       ├── <Name>.php                 <- Operation dispatcher (maps operacion -> delegate)
│       └── delegates/
│           ├── AbstractDelegate.php   <- Base class (constants, shared types)
│           ├── AltaDelegate.php       <- Create operations
│           ├── LeerDelegate.php       <- Read operations
│           ├── EditarDelegate.php     <- Update operations
│           ├── BorrarDelegate.php     <- Delete operations
│           ├── ListarDelegate.php     <- List operations
│           ├── ImportarDelegate.php   <- Bulk import (optional)
│           └── Common.php             <- Shared helpers for this provision
│
└── ColppyCommon/                      <- Shared infrastructure (NOT a provision)
    ├── persistencia/                  <- DAO classes (34 files)
    ├── common/                        <- Utilities, auth, AFIP, encryption
    ├── businessobjects/               <- Business object classes
    ├── validators/                    <- Input validators (CUIT, CBU, NIT)
    ├── lib/                           <- Low-level DB and utility libraries
    ├── GenerarFacturas/               <- Invoice PDF generation
    └── Balance/                       <- Balance sheet generation
```

---

## Delegate Pattern

| Delegate | CRUD Verb | Spanish Meaning | Typical Method Signature |
|----------|-----------|-----------------|--------------------------|
| `Alta` | Create | Registration/creation | `alta_<entity>($parametros)` |
| `Leer` | Read | Read | `leer_<entity>($parametros)` |
| `Editar` | Update | Edit | `editar_<entity>($parametros)` |
| `Borrar` | Delete | Delete | `borrar_<entity>($parametros)` |
| `Listar` | List | List | `listar_<entity>($parametros)` |
| `Importar` | Bulk create | Import | `importar_<entity>($parametros)` |
| `Exportar` | Export | Export | `exportar_<entity>($parametros)` |

- Not all provisions have all delegates
- Some provisions have custom delegates (e.g., `IniciarSesionDelegate`, `PaybookDelegate`)
- Most delegates extend `AbstractDelegate`
- Every public method on the dispatcher class IS the `operacion` value sent via the API

---

## Version Scheme

- Pattern: `<major>_<minor>_<patch>_<build>/` (e.g., `1_0_0_0/`)
- Currently **all 31 business provisions use `1_0_0_0/`** -- no provision has multiple versions
- `ColppyCommon` is shared infrastructure and does not use versioned delegate folders
- The scheme exists to allow backward-compatible API evolution without breaking existing clients
- Each version folder contains its own `config.php`, dispatcher, and `delegates/` directory

---

## All 32 Provisiones Folders

| # | Provision | Purpose | Delegates | Migration |
|---|-----------|---------|-----------|-----------|
| 1 | **Afip** | AFIP tax filing, electronic invoicing (WSFE, WSAA) | Leer | Legacy |
| 2 | **Archivo** | File management / attachments | Alta, Borrar, Leer | Legacy |
| 3 | **BillStub** | Invoice stubs / talonarios | Alta, Listar | Legacy |
| 4 | **Cliente** | Customer management, collections, receipts | Alta, Editar, Leer, Listar, Importar | Partial |
| 5 | **ColppyCommon** | **Shared infrastructure** (NOT a business provision) | N/A | N/A |
| 6 | **CondicionIVA** | VAT conditions catalog | Leer, Listar | Legacy |
| 7 | **CondicionPago** | Payment terms catalog | Listar | Legacy |
| 8 | **Contabilidad** | General ledger, journal entries, chart of accounts | Alta, Borrar, Editar, Enviar, Exportar, Leer, Listar, TestBalance | Migrated |
| 9 | **Desarrollador** | Developer tools / API credentials | Alta, Editar, Leer + 10 custom delegates | Legacy |
| 10 | **Empresa** | Company management, plans, billing, cost centers | Alta, Editar, Leer, Listar, EliminarTransacciones | Partial |
| 11 | **FacturaCompra** | Purchase invoices (accounts payable) | Alta, Editar, Leer, LeerDatosAdicionales, ListarFacturascompra, Importar | Legacy |
| 12 | **FacturaVenta** | Sales invoices (accounts receivable) | Alta, Editar, Leer, LeerDatosAdicionales, Listar, ListarFacturasventa, Pagar, Importar, Imprimir | Legacy |
| 13 | **Help** | In-app help system | Listar | Legacy |
| 14 | **Importer** | Data import orchestration | Editar, Listar | Partial |
| 15 | **Integracion** | Third-party integrations (MercadoLibre, etc.) | Activar, Alta, Leer | Legacy |
| 16 | **Inventario** | Stock / inventory items | Alta, Editar, Leer, Listar, Importar | Migrated |
| 17 | **Location** | Countries, regions, cities catalog | Listar | Legacy |
| 18 | **Moneda** | Currency management, exchange rates | Alta, Leer, Listar | Legacy |
| 19 | **Notificaciones** | Notification system | Send | Legacy |
| 20 | **Pago** | Payment processing logic | Alta, ListarPago, UltimoPago | Legacy |
| 21 | **Paybook** | Banking integration (Mexico) | Banco, Credencial, Cuenta, Message, Token, Usuario | Legacy |
| 22 | **Pos** | Point of sale | Alta, Editar, Leer, Listar | Legacy |
| 23 | **PriceList** | Price lists management | Alta, Editar, Leer, Listar | Migrated |
| 24 | **Proveedor** | Supplier management | Alta, Editar, Leer, Listar, Importar | Partial |
| 25 | **Receipt** | Receipt generation | Alta | Partial |
| 26 | **Referido** | Referral / ambassador program | Referido | Legacy |
| 27 | **Retencion** | Tax withholdings (retenciones) | Leer, Listar | Legacy |
| 28 | **Socio** | Partners / resellers | Alta, Contacto, Leer | Legacy |
| 29 | **Tax** | Tax calendar, expiration events | Alta, Editar, Exportar, Leer, Listar | Migrated |
| 30 | **Tercero** | Unified client/supplier entity | Alta, Editar, Leer, Listar | Migrated |
| 31 | **Tesoreria** | Treasury / banking operations | Alta, AltaOtroCobro, Editar, EditarOtroCobro, Importar, Leer*, Listado, Paybook, Sincronizar | Legacy |
| 32 | **Usuario** | Users, sessions, authentication, wizard | Alta, Editar, Leer, Listar, IniciarSesion, CerrarSesion, IrEmpresa, ValidarSesion, CambioContrasena, ValidarEmail | Legacy |

*Tesoreria `Leer` includes: LeerAsientoIngresosCobro, LeerChequesDiferidos, LeerChequesValoresCartera, LeerFondosCobro, LeerOtroCobro.

---

## Migration Status: Frontera -> Benjamin

| Category | Provisions | How They Delegate |
|----------|-----------|-------------------|
| **Fully Migrated** | Inventario, Tax, PriceList, Tercero | All CRUD via `BenjaminConnector` -> Benjamin REST API |
| **Partially Migrated** | Cliente, Proveedor, Empresa, Contabilidad, FacturaVenta, FacturaCompra, Receipt, Usuario | Some ops via `BenjaminConnector`, others direct DAO |
| **Legacy (No Migration)** | Afip, Paybook, Pos, Tesoreria, Pago, BillStub, Archivo, CondicionIVA, CondicionPago, Location, Moneda, Notificaciones, Help, Referido, Retencion, Socio, Desarrollador, Importer, Integracion | Direct MySQL via DAO classes |

### Benjamin Endpoint Mapping (Migrated Provisions)

| Frontera Provision | Benjamin Endpoint | HTTP Method |
|--------------------|-------------------|-------------|
| Inventario | `/items`, `/items/{id}` | GET, POST, PUT |
| PriceList | `/pricelist/`, `/pricelist/{id}/items/` | GET, POST, PATCH |
| Tax | `/tax/expiration/event/*` | POST, PATCH |
| Tercero | `/terceros`, `/terceros/{id}` | GET, POST, PUT |
| Cliente (partial) | `/terceros`, `/pricelist/{id}/customer` | GET, POST, PUT, DELETE |
| Empresa (partial) | `/company/{id}`, `/empresa/retefuenteventa` | PATCH, GET, POST, DELETE |
| FacturaVenta (partial) | `/invoice/` | GET |
| FacturaCompra (partial) | `/purchaseinvoice/` | GET |
| Receipt (partial) | `/receipt/` | GET |
| Contabilidad (partial) | `/plancuentaempresa`, `/formatos*`, `/conceptos*` | GET, POST, PUT, DELETE |

---

## ColppyCommon Deep Dive

**Path**: `nubox-spa/colppy-app/resources/Provisiones/ColppyCommon/`

### DAO Pattern (`persistencia/`)

- All DAOs implement `DAOInterface` with `getTableName()` and `getClassName()`
- `AbstractDAO` provides `findById($id)`, `findBy($filters)` -- raw SQL via `ColppyDB`
- `ColppyDB` extends `MysqlDB` with hardcoded connection constants (`DB_HOST`, `DB_USER`, `DB_PASS`, `DB_NAME`)
- `Frontera2DB` is a separate DB connection for Frontera's own tables

**34 DAO files** (key ones with table mappings):

| DAO | Table Domain |
|-----|-------------|
| `AbstractDAO` | Base class -- `findById`, `findBy` |
| `ClienteDAO` | `ar_cliente` (customers) |
| `CommonDAO` | Shared queries (country lookup, error logging) |
| `ContabilidadDAO` | `gl_asiento`, `gl_plan_cuenta` |
| `EmpresaDAO` | `empresa` (companies) |
| `FacturaCompraDAO` | `ap_factura` (purchase invoices) |
| `FacturaVentaDAO` | `ar_factura` (sales invoices) |
| `InventarioDAO` | `st_item` (stock items) |
| `ProveedoresDAO` | `ap_proveedor` (suppliers) |
| `TerceroDAO` | Unified third-party entity |
| `TesoreriaDAO` | Treasury/bank accounts |
| `UsuarioDAO` | `usuario`, `usuario_sesion` |

Other DAOs: `AfipProcesamientoFacturasDAO`, `CondicionIVADAO`, `CondicionPagoDAO`, `CrmDAO`, `DecodificadoraDAO`, `EstrategiaPricingDAO`, `HistoriaDAO`, `LocationDAO`, `MonedaDAO`, `PagoDAO`, `PaybookDAO`, `PlanDAO`, `PosDAO`, `ReferidoDAO`, `ReportingDAO`, `RetencionesDAO`, `SocioDAO`, `TaxDAO`, `TipoActividadDAO`, `TokenDAO`, `UsuarioDesarrolladorDAO`.

### UsuarioCommon (Session Validation)

**Path**: `ColppyCommon/common/UsuarioCommon.php`

- `autenticarUsuarioAPI($parametros)` -- entry point for all auth checks
- Supports two auth modes:
  - **OAuth**: Checks `$parametros->oauth` (consumer_key, token, signature, timestamp, nonce)
  - **Session**: Checks `$parametros->sesion->usuario` + `$parametros->sesion->claveSesion`
- Session validation calls `UsuarioDAO->validar_sesion(usuario, userId, claveSesion, isMobile)`
- Auth can be disabled globally via `AUTENTICACION_ACTIVADA` constant
- Throws `ColppyException` (error codes 3000-3005) for OAuth failures
- Throws generic `Exception` for session failures

### FileManagement

**Path**: `ColppyCommon/common/FileManagement/`

| File | Purpose |
|------|---------|
| `FileManager.php` | Main file operations (upload, download, delete) |
| `UploadFile.php` | File upload handler |
| `DownloadArchivoComprobante.php` | Download invoice attachments |
| `CloudFiles/` | Cloud storage integration (legacy, commented out in some provisions) |

### Other Shared Components

| Component | Path | Purpose |
|-----------|------|---------|
| `Common.php` | `common/Common.php` | Shared business logic helpers |
| `FacturaCommon.php` | `common/FacturaCommon.php` | Invoice-shared logic (used by both Venta and Compra) |
| `FronteraCommon.php` | `common/FronteraCommon.php` | Frontera gateway utilities |
| `AESEncryption.php` | `common/AESEncryption.php` | AES encryption for sensitive data |
| `ColppyTransaction.php` | `common/ColppyTransaction.php` | DB transaction wrapper |
| `TextReplace.php` | `common/TextReplace.php` | Template text replacement |
| `afip/` | `common/afip/` | AFIP clients: `AfipWsaa.php`, `AfipWsfev1.php`, `AfipWsfex.php`, `ConsultasAFIP.php` |
| `MercadoPago/` | `common/MercadoPago/` | MercadoPago SDK integration |
| `excepciones/` | `common/excepciones/` | `ColppyException.php` |
| `iibb/` | `common/iibb/` | Ingresos Brutos (gross income tax) helpers |
| `salesforce/` | `common/salesforce/` | Salesforce integration |
| `validators/` | `validators/` | `CUITValidator.php`, `CBUValidator.php`, `NITValidator.php`, `AbstractValidator.php` |
| `GenerarFacturas/` | Root level | Invoice PDF factory: `Factory.php`, `Factura.php`, `FacturaFE.php`, `POS.php`, etc. |

---

## Key Provisions for AI Agents

### FacturaVenta (Sales Invoices)

**Path**: `nubox-spa/colppy-app/resources/Provisiones/FacturaVenta/1_0_0_0/`

| Operation | Delegate | Auth | Notes |
|-----------|----------|------|-------|
| `alta_facturaventa` | AltaDelegate | Yes | Main invoice creation, includes 180s timeout guard |
| `editar_facturaventa` | EditarDelegate | Yes | |
| `leer_facturaventa` | LeerDelegate | Yes | |
| `listar_facturasventa` | ListarFacturasventa | Yes | Note: all lowercase |
| `alta_comprobante_electronico` | AltaDelegate | Yes | AFIP electronic invoice via ColppyCommon/afip |
| `alta_lista_comprobantes_electronicos` | AltaDelegate | Conditional | Batch electronic invoices |
| `alta_facturaventarecurrente` | AltaDelegate | Yes | Recurring invoice setup |
| `listar_facturaventarecurrente` | ListarDelegate | Yes | |
| `importar_facturas` | ImportarDelegate | No | Bulk import |
| `imprimir_facturas` | ImprimirDelegate | No | PDF generation |
| `leer_cobros_factura` | LeerDelegate | Yes | Collections for an invoice |
| `listar_comprobantes_venta_detalle` | ListarFacturasventa | Yes | Detailed voucher list |

### FacturaCompra (Purchase Invoices)

**Path**: `nubox-spa/colppy-app/resources/Provisiones/FacturaCompra/1_0_0_0/`

| Operation | Delegate | Auth | Notes |
|-----------|----------|------|-------|
| `alta_facturacompra` | AltaDelegate | Yes | |
| `editar_facturacompra` | EditarDelegate | Yes | |
| `leer_facturacompra` | LeerDelegate | Yes | |
| `listar_facturasCompra` | ListarFacturascompra | Yes | Note: camelCase `C` |
| `listar_facturasTotales` | ListarFacturascompra | Yes | |
| `listar_comprobantes_compra_detalle` | ListarFacturascompra | Yes | |
| `leer_pagos_factura` | LeerDelegate | Yes | |
| `leer_fondosPagoFactura` | LeerDelegate | Yes | |
| `importar_facturas` | ImportarDelegate | No | |

### Cliente (Customers)

**Path**: `nubox-spa/colppy-app/resources/Provisiones/Cliente/1_0_0_0/`

| Operation | Delegate | Auth | Notes |
|-----------|----------|------|-------|
| `alta_cliente` | AltaDelegate | Yes | Creates Tercero in Benjamin |
| `editar_cliente` | EditarDelegate | Yes | Updates Tercero in Benjamin |
| `leer_cliente` | LeerDelegate | Yes | |
| `listar_cliente` | ListarDelegate | Yes | |
| `leer_cliente_por_cuit` | LeerDelegate | Yes | Lookup by CUIT |
| `alta_cobro` | AltaDelegate | Yes | Create collection receipt |
| `editar_cobro` | EditarDelegate | Yes | |
| `listar_retsufridas` | ListarDelegate | Yes | Withholdings suffered |
| `importacion_masiva_clientes` | ImportarDelegate | Yes | Bulk customer import |
| `generar_pdf_recibo_cliente` | AltaDelegate | Yes | Generate receipt PDF |

### Empresa (Companies)

**Path**: `nubox-spa/colppy-app/resources/Provisiones/Empresa/1_0_0_0/`

| Operation | Delegate | Auth | Notes |
|-----------|----------|------|-------|
| `alta_empresa` | AltaDelegate | Yes | |
| `alta_empresa_wizard` | AltaDelegate | No | Called from onboarding wizard |
| `alta_empresa_demo` | AltaDelegate | No | Demo company creation |
| `editar_empresa` | EditarDelegate | Conditional | Some fields via Benjamin PATCH |
| `editar_datosimpositivos` | EditarDelegate | Yes | Tax settings |
| `crear_plan_cuentas` | AltaDelegate | Conditional | Chart of accounts setup |
| `crear_datos_facturacion` | AltaDelegate | No | Billing data setup |
| `leer_empresa` | LeerDelegate | Yes | |
| `listar_empresa` | ListarDelegate | Yes | |
| `eliminar_transacciones` | EliminarTransaccionesDelegate | Yes | Dangerous: wipes company data |
| `generar_delegacion` | AltaDelegate | Yes | Accountant delegation |

### Tesoreria (Treasury)

**Path**: `nubox-spa/colppy-app/resources/Provisiones/Tesoreria/1_0_0_0/`

| Operation | Delegate | Notes |
|-----------|----------|-------|
| Various alta/editar ops | AltaDelegate, EditarDelegate | Bank accounts, checks, cash |
| `AltaOtroCobro` / `EditarOtroCobro` | Dedicated delegates | Other collection types |
| Leer* (5 variants) | LeerDelegate, LeerChequesDiferidosDelegate, etc. | Different read views |
| Listado | ListadoDelegate | Treasury listing |
| Sincronizar | SincronizarDelegate | Bank reconciliation |
| Paybook | PaybookDelegate | Mexico bank integration |

### Inventario (Stock Items)

**Path**: `nubox-spa/colppy-app/resources/Provisiones/Inventario/1_0_0_0/`

- **Fully migrated** -- all CRUD goes through `BenjaminConnector` -> `/items` endpoint
- Delegates still exist but proxy to Benjamin REST calls
- PriceList association also via Benjamin

---

## Dispatcher Pattern (Code)

Each provision's main PHP file dispatches to delegates. Example from `FacturaVenta.php`:

```php
class FacturaVenta extends JSONWebservice implements http_origin_security {

    public function alta_facturaventa($parametros) {
        autenticarUsuarioAPI($parametros);          // -> UsuarioCommon.php
        $altaDelegate = new AltaDelegate();
        return $altaDelegate->alta_facturaventa($parametros);
    }

    public function listar_facturasventa($parametros) {
        autenticarUsuarioAPI($parametros);
        $leerDelegate = new ListarFacturasventa();
        return $leerDelegate->listar_facturasventa($parametros);
    }
}
```

### Includes and Dependencies (typical provision bootstrap)

```php
// From FacturaVenta.php -- shows the require chain
require_once FM_SERVICES_FOLDER . '/ColppyCommon/lib/snddb.php';       // DB library
require_once FM_SERVICES_FOLDER . '/ColppyCommon/common/Common.php';
require_once FM_SERVICES_FOLDER . '/ColppyCommon/common/FacturaCommon.php';
require_once FM_SERVICES_FOLDER . '/ColppyCommon/common/UsuarioCommon.php'; // Auth
require_once FM_SERVICES_FOLDER . '/ColppyCommon/ColppyDB.php';         // MySQL connection
require_once FM_SERVICES_FOLDER . '/ColppyCommon/persistencia/AbstractDAO.php';
require_once FM_SERVICES_FOLDER . '/ColppyCommon/persistencia/FacturaVentaDAO.php';
// ... more DAOs ...
require_once ROOT_COLPPY . "lib/BenjaminConnector/BenjaminConnector.php";  // Benjamin proxy
require_once ROOT_COLPPY . "lib/BenjaminConnector/ErrorHandler.php";
require_once ROOT_COLPPY . "lib/BenjaminConnector/MessageHandler.php";
```

### BenjaminConnector Usage in Delegates

```php
// Migrated provision example (Inventario, PriceList, Tax, Tercero)
$benjaminConnector = new BenjaminConnector($parametros->sesion->usuario);
$items = $benjaminConnector->get('/items', $params, $idEmpresa);
$result = MessageHandler::handling($items);

// Error handling
try {
    $data = $benjaminConnector->post('/items', $body, [], $idEmpresa);
} catch (BenjaminException $exception) {
    return ErrorHandler::handling($exception);
}
```

### Security Methods (every dispatcher)

```php
public function __http_bypass()    // Operations that skip origin check
public function __http_blacklist() // Blocked origins
public function __http_list()      // Allowed origins
```

---

## Gotchas

- **ColppyCommon is NOT a business provision** -- no version directory, no dispatcher, no delegates. It is shared infrastructure only.
- **All version folders are `1_0_0_0/`** -- despite the versioning scheme, no provision currently has multiple versions deployed.
- **Case-sensitive operation names** -- `listar_facturasCompra` (camelCase `C`) vs `listar_facturasventa` (all lowercase). This is a real inconsistency, not a typo.
- **Some provisions delegate to Benjamin via `BenjaminConnector`** -- Inventario, PriceList, Tax, Tercero are fully migrated; Cliente, Empresa, FacturaVenta, FacturaCompra are partially migrated. Legacy provisions hit MySQL directly via DAOs.
- **The dispatcher method name IS the API `operacion` value** -- there is no routing table. If the class has `public function alta_facturaventa($parametros)`, the API call uses `"operacion": "alta_facturaventa"`.
- **Session validation is opt-in per operation** -- `autenticarUsuarioAPI($parametros)` must be called explicitly at the top of each dispatcher method. Some operations bypass it (e.g., `iniciar_sesion`, `alta_usuario`, `alta_empresa_wizard`).
- **Misleading file headers** -- `FacturaVenta.php` header says "Provisión para manejo de la factura de Compra". `Afip.php` header says "Provisión para manejo de Moneda". Do not trust header comments.
- **AFIP logic is scattered** -- the Afip provision dispatcher has only `health_check`. Actual WSFE/WSAA calls happen inside `FacturaVenta` delegates and `ColppyCommon/common/afip/`.
- **FacturaCompra has no `ListarDelegate`** -- it uses `ListarFacturascompra` (note: capital `F`, lowercase `c`). The operation name is `listar_facturasCompra` (camelCase `C`).
- **PHP 5.6 era code** -- no type hints, no `strict_types`, no namespaces (except DAOInterface). Uses `stdClass` for parameter passing. Raw SQL with string concatenation in DAOs (potential SQL injection surface).
- **`AbstractDelegate` varies per provision** -- each provision has its own `AbstractDelegate.php` with domain-specific constants (e.g., FacturaVenta's has comprobante type maps). These are not shared across provisions.
- **`BenjaminConnector` auth is separate from Frontera auth** -- it uses OAuth2 tokens stored in `usuario_external_tokens`, with automatic refresh. This is transparent to delegates.
- **Timeout guard in FacturaVenta** -- `alta_facturaventa` registers a shutdown function with 180-second timeout tracking via `register_shutdown_function`. No other provision does this.
- **`FacturaCommon`** is shared between FacturaVenta and FacturaCompra -- contains invoice calculation helpers, multimoneda logic.
- **Importar delegates often skip auth** -- `importar_facturas` in both FacturaVenta and FacturaCompra does NOT call `autenticarUsuarioAPI`.

---

## Cross-References

- [Backend Architecture](backend-architecture.md) -- Frontera + Benjamin layers, BenjaminConnector details
- [API Reference](api-reference.md) -- Envelope format for `provision` + `operacion` calls
- [Database Schema](database-schema.md) -- Tables accessed by DAO classes listed above
- [Auth and Sessions](auth-and-sessions.md) -- Session validation flow in UsuarioCommon, OAuth vs claveSesion
- [canonical-counts.md](canonical-counts.md) -- Canonical module/repo counts used across docs

---

*Last updated: 2026-03-03*
