# Database Schema Reference

- **Engine**: MySQL (single shared `colppy` database)
- **Access layers**: Frontera (raw PDO via DAOs) and Benjamin (Laravel Eloquent ORM) both read/write the same tables
- **Migration count**: 107 migration files in `nubox-spa/colppy-benjamin/database/migrations/` (2014--2025)
- **Naming convention**: Spanish, snake_case with domain prefixes (`ar_`, `ap_`, `gl_`, `st_`, `te_`, `tx_`, `em_`)

---

## Domain Prefix Legend

| Prefix | Domain | Spanish |
|--------|--------|---------|
| `ar_` | Accounts Receivable (Sales) | Cuentas por cobrar |
| `ap_` | Accounts Payable (Purchases) | Cuentas por pagar |
| `gl_` | General Ledger (Accounting) | Libro mayor |
| `st_` | Stock (Inventory) | Inventario |
| `te_` | Treasury | Tesoreria |
| `tx_` | Tax / AFIP | Impuestos |
| `em_` | Company Settings | Empresa (config) |
| (none) | Core / Auth / Shared | -- |

---

## Core / Auth / Session Tables

| Table | PK | Key Columns | Accessed By |
|-------|----|----|-------------|
| `usuario` | `id` (auto), `idUsuario` (email) | `nombreUsuario`, `telefono`, `country_id`, `fechaRegistro`, `record_insert_ts`, `passwordExpirada`, `idUltimaEmpresa`, `usa_wizard`, `seller_id` | Frontera DAO + Benjamin `User` model |
| `empresa` | `IdEmpresa` | `Nombre`, `razonSocial`, `CUIT`, `idCondicionIva`, `idPlan`, `activa`, `FechaAlta`, `fechaVencimiento`, `country_id`, `tipoOperacion`, `istrial`, `tipoPago`, `esEmpresaDemo`, `estrategiaPricing`, `integracion_meli`, `wsafip_delegation_status`, `calcularpercarba`, `calcularpercagip`, `cbu`, `email`, `telefono`, `recordMixPanel` | Frontera DAO + Benjamin `Company` model |
| `usuario_empresa` | `idUsuarioEmpresa` | `user_id` (FK->usuario.id), `company_id` (FK->empresa.IdEmpresa), `idUsuario` (email), `esAdministrador`, `esContador`, `idRol`, `estado_id`, `ultimoLogin`, `fechaAlta`, `fechaBaja`, `fechaModificacion` | Frontera DAO + Benjamin `UserCompany` model |
| `usuario_sesion` | `idSesion` | `user_id` (FK->usuario.id), `idUsuario`, `idEmpresa`, `claveSesion` (MD5 token), `fechaCreacion`, `fechaAcceso`, `fechaExpira`, `fechaSalida`, `ipCreacion` | Frontera DAO only (legacy auth) |
| `plan` | `idPlan` | `nombre`, `tipo`, `meses`, `precio`, `precio_anual`, `descripcion`, `estrategiaPricing`, `topeFacturas`, `marcaBlanca`, `countryId`, `color`, `popular`, `showInList`, `showInWebSite`, `isDiscountPlan`, `precio_siniva`, `precio_anual_siniva` | Frontera DAO + Benjamin `Plan` model |
| `facturacion` | `IdEmpresa` (FK) | `email`, `razonSocial`, `CUIT`, `idCondicionIva`, `domicilio`, `localidad`, `provincia` | Frontera DAO (billing data) |
| `rol` | `idRol` + `idEmpresa` | `empresa`, `proveedores`, `clientes`, `tesoreria`, `inventario`, `contabilidad`, `tablero` (all boolean-like) | Frontera DAO + svc_settings |
| `pago` (platform billing) | `idPago` | `idUsuario`, `idEmpresa`, `idPlan`, `fechaPago`, `periodo`, `nroOperacion`, `estado`, `importe`, `tipoPago`, `medioPago`, `primerPago`, `cbu`, `cuit`, `idPos` | Benjamin `Payment\Pago` model + svc_settings |

### Key Auth Relationship Chain

```
usuario (id)
  |-- 1:N --> usuario_empresa (user_id, company_id)
                  |-- N:1 --> empresa (IdEmpresa)
                                 |-- N:1 --> plan (idPlan)
                  |-- N:1 --> rol (idRol, idEmpresa)
  |-- 1:N --> usuario_sesion (user_id)
```

### usuario_sesion Detail

- **Token**: `claveSesion` -- MD5 hash, used as session bearer
- **Expiry**: `fechaExpira` -- set via `DATE_ADD(now(), INTERVAL N MINUTE)` where N = `SESION_MINS_DURACION`
- **IP tracking**: `ipCreacion`
- **Lookup pattern**: latest session per user via `MAX(fechaCreacion)` subquery
- See [Auth and Sessions](auth-and-sessions.md) for full auth flow

---

## Sales Domain (ar_)

| Table | PK | Key Columns | Eloquent Model |
|-------|----|----|----------------|
| `ar_factura` | `idFactura` | `idEmpresa`, `idCliente`, `idTipoFactura` (0=A,1=B,2=C,3=E,4=Z,5=L,6=M,7=X,8=T), `idTipoComprobante` (4=Factura,5=NC,6=ND,8=Contado), `nroFactura`, `fechaFactura`, `fechaPago`, `idCondicionPago`, `idEstadoFactura` (1=Borrador,3=Aprobada,4=Anulada,5=Pagada,6=Parcial), `totalFactura`, `netoGravado`, `netoNoGravado`, `totalIVA`, `percepcionIIBB`, `percepcionIVA`, `idCurrency`, `rate`, `cae`, `fechaFe`, `price_list_id`, `is_fce`, `idTalonario`, `descripcion`, `record_insert_ts`, `record_update_ts`, `codigo_actividad`, `codigo_operacion` | `Ar\Factura` |
| `ar_detalle_factura` | composite | `idFactura`, `idEmpresa`, `nro`, `itemId`, `Descripcion`, `Cantidad`, `ImporteUnitario`, `IVA`, `porcDesc`, `idPlanCuenta`, `idAlmacen`, `ccosto1`, `ccosto2`, `unidadMedida` | `Ar\DetalleFactura` |
| `ar_cliente` | `idCliente` | `idEmpresa`, `RazonSocial`, `NombreFantasia`, `CUIT`, `idCondicionIva` | `Ar\Cliente` / `Customer` |
| `ar_cobro` | `idCobro` | `idEmpresa`, `idCliente`, `fechaCobro`, `totalCobro` | `Ar\Cobro` |
| `ar_detalle_factura_cobro` | composite | `idFactura`, `idCobro` | `Ar\DetalleFacturaCobro` |
| `ar_pago_factura_contado` | composite | `idFactura`, `idEmpresa`, `nroCheque`, `Banco`, `importe`, `idMedioCobro`, `idPlanCuenta` | `Ar\PagoFacturaContado` |
| `ar_pago_medio_cobro` | composite | `idPlanCuenta` | `Ar\PagoMedioCobro` |
| `ar_tipoitem` | composite | `idEmpresa`, `idTipoItem`, `idPlanCuenta` | `Ar\TipoItem` |
| `ar_totalesiva` | composite | `idFactura`, IVA breakdown | `Ar\TotalesIva` |
| `ar_retsufridas` | composite | retention details | `Ar\Retsufrida` |
| `ar_retsufridas_otras` | composite | other retention details | `Ar\Retsufridasotras` |
| `ar_cliente_price_list` | composite | `idCliente`, price list link | `Ar\ClientePriceList` |
| `ar_regimen_fce_empresas` | -- | FCE regime per company | `Ar\RegimenFceEmpresas` |
| `ar_regimen_fce_cronograma` | -- | FCE schedule | `Ar\RegimenFceCronograma` |
| `ar_cobro_mail_template` | -- | email templates for collections | -- |

### Sales Relationship Chain

```
ar_factura (idFactura, idEmpresa)
  |-- N:1 --> ar_cliente (idCliente)
  |-- 1:N --> ar_detalle_factura (idFactura)
  |               |-- N:1 --> st_item (itemId)
  |               |-- N:1 --> gl_plan_cuenta (idPlanCuenta)
  |-- 1:N --> ar_totalesiva (idFactura)
  |-- 1:N --> ar_pago_factura_contado (idFactura)  [cash invoices]
  |-- N:1 --> currency (idCurrency)
  |-- N:1 --> talonario (idTalonario)
  |-- 1:N --> diario (idElemento = idFactura, idTabla = 19)
```

---

## Purchase Domain (ap_)

| Table | PK | Key Columns | Eloquent Model |
|-------|----|----|----------------|
| `ap_factura` | `idFactura` | `idEmpresa`, `idProveedor`, `idTipoFactura`, `idTipoComprobante` (1=Compra,2=NC,3=ND,7=Contado), `nroFactura`, `fechaFactura`, `fechaFacturaDoc`, `fechaPago`, `idCondicionPago`, `idEstadoFactura`, `totalFactura`, `netoGravado`, `netoNoGravado`, `totalIVA`, `percepcionIIBB`, `percepcionIVA`, `idCurrency`, `descripcion`, `created_at` | `Ap\Factura` |
| `ap_detalle_factura` | composite | `idFactura`, `idEmpresa`, `nro`, `itemId`, `Descripcion`, `Cantidad`, `ImporteUnitario`, `IVA`, `idPlanCuenta`, `idAlmacen`, `ccosto1`, `ccosto2` | `Ap\DetalleFactura` |
| `ap_proveedor` | `idProveedor` | `idEmpresa`, `RazonSocial`, `NombreFantasia`, `CUIT` | `Ap\Proveedor` |
| `ap_pago` | `idPago` | `idEmpresa`, `idProveedor`, payment details | `Ap\Pago` |
| `ap_detalle_factura_pago` | composite | `idFactura`, `idPago` | `Ap\DetalleFacturaPago` |
| `ap_pago_factura_contado` | composite | cash payment for purchases | `Ap\PagoFacturaContado` |
| `ap_pago_medio_pago` | composite | payment method details | `Ap\PagoMedioPago` |
| `ap_tipoitem` | composite | `idEmpresa`, `idTipoItem`, `idPlanCuenta` | `Ap\TipoItem` |
| `ap_totalesiva` | composite | IVA breakdown | `Ap\TotalesIva` |
| `ap_percsufridas` | composite | `idFactura`, withholding perceptions | `Ap\PercSufridas` |
| `ap_retemitidas` | composite | issued retentions | `Ap\Retemitida` |
| `ap_retencion_ganancias` | composite | income tax retention | `Ap\RetencionGanancias` |

### Purchase Relationship Chain

```
ap_factura (idFactura, idEmpresa)
  |-- N:1 --> ap_proveedor (idProveedor)
  |-- 1:N --> ap_detalle_factura (idFactura)
  |-- 1:N --> ap_totalesiva (idFactura)
  |-- 1:N --> ap_percsufridas (idFactura)
  |-- 1:N --> ap_pago_factura_contado (idFactura)
  |-- N:1 --> currency (idCurrency)
  |-- 1:N --> diario (idElemento = idFactura)
```

---

## Accounting / General Ledger (gl_)

| Table | PK | Key Columns | Eloquent Model |
|-------|----|----|----------------|
| `gl_asiento` | `idAsiento` + `idEmpresa` (composite) | `fechaContable`, `descAsiento`, `totalDebito`, `totalCredito`, `isNIIF`, `idTipoAsiento` | `Gl\Asiento` |
| `gl_detalle_asiento` | composite | `idEmpresa`, `idAsiento`, `nro`, `idPlanCuenta`, `Debito`, `Credito`, `Comentario`, `ccosto1`, `ccosto2`, `idTercero` | -- (raw PDO) |
| `gl_plan_cuenta` | `Id` | `idEmpresa`, `idPlanCuenta`, `parent`, `Descripcion`, `admiteAsiento`, `saldoHabitual`, `balanceInicial`, `Debito`, `Credito`, `Balance`, `tipoCuenta` | `Gl\PlanAccount` |
| `gl_tipo_cuenta` | -- | account type classification | `Gl\TipoCuenta` |
| `gl_tipo_asiento` | -- | journal entry types | `Gl\TipoAsiento` |
| `gl_indice_inflacion` | -- | inflation adjustment indices | `Gl\IndiceInflacion` |
| `gl_formato` | -- | report format templates | `Gl\Formato` |
| `gl_concepto` | -- | report concepts | `Gl\Concepto` |
| `gl_columna` | -- | report columns | `Gl\Columna` |
| `gl_empresa_formato` | -- | company-format mapping | `Gl\EmpresaFormato` |
| `gl_empresa_concepto` | -- | company-concept mapping | `Gl\EmpresaConcepto` |
| `gl_empresa_concepto_columna` | -- | company-concept-column mapping | `Gl\EmpresaConceptoColumna` |
| `gl_empresa_columna_cuenta` | -- | company-column-account mapping | `Gl\EmpresaColumnaCuenta` |

### Diary (Journal)

| Table | PK | Key Columns | Eloquent Model |
|-------|----|----|----------------|
| `diario` | composite (`idEmpresa`, `idTabla`, `idElemento`, `idDiario`) | `idPlanCuenta`, `DebitoCredito`, `importe`, `FechaContabilizado`, `fechaContable`, `idSubdiario`, `idTablaAplicado`, `idElementoAplicado`, `idObjetoContacto`, `idElementoContacto`, `idItem`, `ccosto1`, `ccosto2`, `Conciliado`, `batch`, `idTercero`, `isNIIF`, `itemId` | `Diary` |

- The `diario` table is the universal journal -- all modules write entries here
- `idTabla` discriminates the source module (e.g., 19 = sales invoice)
- `idElemento` is the FK to the source record in that module

---

## Inventory (st_)

| Table | PK | Key Columns | Eloquent Model |
|-------|----|----|----------------|
| `st_item` | `id` | `idEmpresa`, `idItem`, `codigo`, `descripcion`, `detalle`, `ctaCostoVentas`, `ctaIngresoVentas`, `ctaInventario`, `minimo`, `costoCalculado`, `ultimoPrecioCompra`, `precioVenta`, `iva`, `tipoItem`, `unidadMedida`, `esKit`, `fechaAlta`, `fechaBaja`, `comentarioFactura` | `St\Item` |
| `st_item_kit` | composite | `idParent`, `idItem` (self-join for kit composition) | -- (pivot) |
| `st_deposito` | `idAlmacen` | `idEmpresa`, `nombre` | `St\Deposito` |
| `st_movimiento` | -- | `itemId`, stock movement records | `St\Movement` |
| `st_price_list` | `id` | `description`, price list header | `St\PriceList` |
| `st_price_list_detail` | -- | `st_item_id`, item-level pricing | `St\PriceListDetail` |

---

## Treasury (te_)

| Table | PK | Key Columns | Eloquent Model |
|-------|----|----|----------------|
| `te_banco` | -- | `idEmpresa`, `idPlanCuenta`, bank account config | `Te\Banco` |
| `te_cobro` | `idCobro` | `idEmpresa`, collection records | `Te\Cobro` |
| `te_cobro_medio_cobro` | composite | collection payment method detail | `Te\CobroMedioCobro` |
| `te_medio_cobro` | -- | collection method catalog | `Te\MedioCobro` |
| `te_pago` | `idPago` | `idEmpresa`, payment records | `Te\Pago` |
| `te_pago_medio_pago` | composite | payment method detail | `Te\PagoMedioPago` |
| `te_medio_pago` | -- | payment method catalog | `Te\MedioPago` |
| `te_tipoitem` | composite | `idEmpresa`, `idTipoItem`, `idPlanCuenta` | `Te\TipoItem` |

---

## Tax / AFIP (tx_)

| Table | PK | Key Columns | Eloquent Model |
|-------|----|----|----------------|
| `tx_impuestos` | `id` / `idImpuesto` | `nombre`, `nombre_abbr`, `hexa` (color) | `Tx\Impuesto` |
| `tx_impuestos_fecha` | -- | date-bound tax config | `Tx\ImpuestosFecha` |
| `tx_setup_impuestos` | `id` | `idEmpresa`, `idImpuesto`, `ndias`, `email`, `activo` | `Tx\SetupImpuesto` |
| `tx_contadores_eventos` | -- | `idEmpresa`, `idSetup`, `fecha`, tax calendar events | `Tx\ContadoresEventos` |
| `tx_comportamiento_impuestos` | -- | tax behavior rules | `Tx\ComportamientoImpuestos` |
| `actividades_empresa` | -- | `idEmpresa`, company economic activities | `ActividadEmpresa` |
| `tipos_operacion_venta` | -- | sale operation type catalog | -- |
| `afip_procesamiento_facturas` | -- | AFIP invoice processing log | -- |
| `afip_errores` | -- | AFIP error log | -- |

---

## Company Settings (em_)

| Table | PK | Key Columns | Eloquent Model |
|-------|----|----|----------------|
| `em_pos` | `idPos` | `idEmpresa`, `idTalonario`, `idCaja`, `idCliente`, `activo`, `tipo_plan`, `nombrePos`, `idTalonarioRemito`, `idTalonarioSecundario`, `fechaVencimiento`, `descuento`, `idEstadoFactura` | `Em\Pos` |
| `em_usuario_pos` | `idUsuarioPos` | `user_id`, `idPos` (pivot: user <-> POS) | -- (pivot) |
| `em_ccosto_codigo` | `Id` | `idEmpresa`, `ccosto`, `Codigo` | `Em\Ccosto` |
| `em_promo` | -- | promotional codes / campaigns | `Em\Promo` |
| `em_deactivation_process` | -- | company deactivation tracking | `Em\DeactivationProcess` |
| `em_retefuente_cuenta_venta` | -- | sales retefuente accounts (CO) | `Em\SalesAccountRetefuente` |
| `em_muniretrealizadas_co` | -- | municipal retention accounts (CO) | `Em\PurchaseAccountReteica` |
| `talonario` | `idTalonario` | `idEmpresa`, `idFormatoImpresion`, invoice book config | `Em\Talonario` |

---

## Shared / Lookup Tables

| Table | PK | Purpose | Eloquent Model |
|-------|----|----|----------------|
| `currency` | `id` | Currency catalog (`nombre`, `iso`, `afip_id`) | `Currency` |
| `condicion_pago` | `idElemento` | Payment terms (filtered by `country_id`) | -- |
| `condicion_iva` | -- | IVA condition catalog | `CondicionIva` |
| `porcentajes_iva` | -- | IVA percentage catalog | `PorcentajesIva` |
| `decodificadora` | `idElemento` + `idTabla` + `idEmpresa` | Generic lookup/decoder (used for payment conditions, etc.) | `Decodificadora` |
| `tercero` | -- | Third-party entities | `Tercero` |
| `country` | -- | Country catalog | `Country` |
| `region` | -- | Region/province catalog | `Region` |
| `city` | -- | City catalog | `City` |
| `formato_impresion` | -- | Print format templates | `FormatoImpresion` |
| `help` | -- | In-app help items | `Help` |
| `help_setting` | -- | Help display settings | `HelpSetting` |

---

## Payment / Billing Tables (platform-level)

| Table | PK | Purpose | Eloquent Model |
|-------|----|----|----------------|
| `pago` | `idPago` | Platform subscription payments | `Payment\Pago` |
| `payment_detail` | -- | `payment_id` (FK->pago), detailed payment info (`net_amount`, `iva_amount`, `total_amount`, `payment_gateway`, `external_transaction_id`, `is_first_payment`) | `Payment\PaymentDetail` |
| `payment_detail_status` | -- | Payment status history | `Payment\PaymentDetailStatus` |
| `payment_subscription` | -- | Recurring subscription records | `Payment\PaymentSubscription` |

---

## Eloquent Model Index

Complete list of Benjamin Eloquent models mapped to their tables.

| Model Path | Table |
|------------|-------|
| `Models/User.php` | `usuario` |
| `Models/Company.php` | `empresa` |
| `Models/UserCompany.php` | `usuario_empresa` |
| `Models/Plan.php` | `plan` |
| `Models/Currency.php` | `currency` |
| `Models/Customer.php` | `ar_cliente` |
| `Models/Provider.php` | `ap_proveedor` |
| `Models/Diary.php` | `diario` |
| `Models/Tercero.php` | `tercero` |
| `Models/Decodificadora.php` | `decodificadora` |
| `Models/ActividadEmpresa.php` | `actividades_empresa` |
| `Models/CondicionIva.php` | `condicion_iva` |
| `Models/PorcentajesIva.php` | `porcentajes_iva` |
| `Models/FormatoImpresion.php` | `formato_impresion` |
| `Models/Help.php` | `help` |
| `Models/HelpSetting.php` | `help_setting` |
| `Models/Country.php` | `country` |
| `Models/Region.php` | `region` |
| `Models/City.php` | `city` |
| `Models/Ar/Factura.php` | `ar_factura` |
| `Models/Ar/DetalleFactura.php` | `ar_detalle_factura` |
| `Models/Ar/Cliente.php` | `ar_cliente` |
| `Models/Ar/Cobro.php` | `ar_cobro` |
| `Models/Ar/DetalleFacturaCobro.php` | `ar_detalle_factura_cobro` |
| `Models/Ar/PagoFacturaContado.php` | `ar_pago_factura_contado` |
| `Models/Ar/PagoMedioCobro.php` | `ar_pago_medio_cobro` |
| `Models/Ar/TipoItem.php` | `ar_tipoitem` |
| `Models/Ar/TotalesIva.php` | `ar_totalesiva` |
| `Models/Ar/Retsufrida.php` | `ar_retsufridas` |
| `Models/Ar/Retsufridasotras.php` | `ar_retsufridas_otras` |
| `Models/Ar/ClientePriceList.php` | `ar_cliente_price_list` |
| `Models/Ar/InvoiceImport.php` | (import staging) |
| `Models/Ar/RegimenFceEmpresas.php` | `ar_regimen_fce_empresas` |
| `Models/Ar/RegimenFceCronograma.php` | `ar_regimen_fce_cronograma` |
| `Models/Ap/Factura.php` | `ap_factura` |
| `Models/Ap/DetalleFactura.php` | `ap_detalle_factura` |
| `Models/Ap/Proveedor.php` | `ap_proveedor` |
| `Models/Ap/Pago.php` | `ap_pago` |
| `Models/Ap/DetalleFacturaPago.php` | `ap_detalle_factura_pago` |
| `Models/Ap/PagoFacturaContado.php` | `ap_pago_factura_contado` |
| `Models/Ap/PagoMedioPago.php` | `ap_pago_medio_pago` |
| `Models/Ap/TipoItem.php` | `ap_tipoitem` |
| `Models/Ap/TotalesIva.php` | `ap_totalesiva` |
| `Models/Ap/PercSufridas.php` | `ap_percsufridas` |
| `Models/Ap/Retemitida.php` | `ap_retemitidas` |
| `Models/Ap/RetencionGanancias.php` | `ap_retencion_ganancias` |
| `Models/Gl/Asiento.php` | `gl_asiento` |
| `Models/Gl/PlanAccount.php` | `gl_plan_cuenta` |
| `Models/Gl/TipoCuenta.php` | `gl_tipo_cuenta` |
| `Models/Gl/TipoAsiento.php` | `gl_tipo_asiento` |
| `Models/Gl/IndiceInflacion.php` | `gl_indice_inflacion` |
| `Models/Gl/Formato.php` | `gl_formato` |
| `Models/Gl/Concepto.php` | `gl_concepto` |
| `Models/Gl/Columna.php` | `gl_columna` |
| `Models/Gl/EmpresaFormato.php` | `gl_empresa_formato` |
| `Models/Gl/EmpresaConcepto.php` | `gl_empresa_concepto` |
| `Models/Gl/EmpresaConceptoColumna.php` | `gl_empresa_concepto_columna` |
| `Models/Gl/EmpresaColumnaCuenta.php` | `gl_empresa_columna_cuenta` |
| `Models/St/Item.php` | `st_item` |
| `Models/St/Deposito.php` | `st_deposito` |
| `Models/St/Movement.php` | `st_movimiento` |
| `Models/St/PriceList.php` | `st_price_list` |
| `Models/St/PriceListDetail.php` | `st_price_list_detail` |
| `Models/Te/Banco.php` | `te_banco` |
| `Models/Te/Cobro.php` | `te_cobro` |
| `Models/Te/CobroMedioCobro.php` | `te_cobro_medio_cobro` |
| `Models/Te/MedioCobro.php` | `te_medio_cobro` |
| `Models/Te/Pago.php` | `te_pago` |
| `Models/Te/PagoMedioPago.php` | `te_pago_medio_pago` |
| `Models/Te/MedioPago.php` | `te_medio_pago` |
| `Models/Te/TipoItem.php` | `te_tipoitem` |
| `Models/Tx/Impuesto.php` | `tx_impuestos` |
| `Models/Tx/ImpuestosFecha.php` | `tx_impuestos_fecha` |
| `Models/Tx/SetupImpuesto.php` | `tx_setup_impuestos` |
| `Models/Tx/ContadoresEventos.php` | `tx_contadores_eventos` |
| `Models/Tx/ComportamientoImpuestos.php` | `tx_comportamiento_impuestos` |
| `Models/Em/Pos.php` | `em_pos` |
| `Models/Em/Ccosto.php` | `em_ccosto_codigo` |
| `Models/Em/Talonario.php` | `talonario` |
| `Models/Em/Promo.php` | `em_promo` |
| `Models/Em/DeactivationProcess.php` | `em_deactivation_process` |
| `Models/Payment/Pago.php` | `pago` |
| `Models/Payment/PaymentDetail.php` | `payment_detail` |
| `Models/Payment/PaymentDetailStatus.php` | `payment_detail_status` |
| `Models/Payment/PaymentSubscription.php` | `payment_subscription` |

---

## Frontera DAO Index

DAOs in `nubox-spa/colppy-app/resources/Provisiones/ColppyCommon/persistencia/`.

| DAO | Primary Tables Accessed |
|-----|------------------------|
| `UsuarioDAO.php` | `usuario`, `usuario_empresa`, `usuario_sesion`, `empresa`, `ar_tipoitem`, `ap_tipoitem`, `te_tipoitem`, `rol`, `pago` |
| `EmpresaDAO.php` | `empresa`, `usuario_empresa`, `plan`, `facturacion` |
| `FacturaVentaDAO.php` | `ar_factura`, `ar_detalle_factura`, `ar_cliente`, `ar_pago_factura_contado`, `diario`, `te_banco` |
| `FacturaCompraDAO.php` | `ap_factura`, `ap_detalle_factura`, `ap_proveedor` |
| `ClienteDAO.php` | `ar_cliente` |
| `ProveedoresDAO.php` | `ap_proveedor` |
| `ContabilidadDAO.php` | `gl_asiento`, `gl_detalle_asiento`, `gl_plan_cuenta` |
| `InventarioDAO.php` | `st_item`, `st_deposito`, `st_movimiento` |
| `PlanDAO.php` | `plan` |
| `TaxDAO.php` | `tx_impuestos`, `tx_setup_impuestos`, `tx_contadores_eventos` |
| `TokenDAO.php` | `usuario_sesion` |
| `RetencionesDAO.php` | `ap_retemitidas`, `ap_percsufridas`, `ar_retsufridas` |
| `TesoreriaDAO.php` | `te_cobro`, `te_pago`, `te_banco` |
| `PagoDAO.php` | `pago`, `payment_detail` |
| `MonedaDAO.php` | `currency` |
| `DecodificadoraDAO.php` | `decodificadora` |
| `TerceroDAO.php` | `tercero` |
| `SocioDAO.php` | partner/referral tables |
| `PosDAO.php` | `em_pos`, `em_usuario_pos` |
| `CrmDAO.php` | CRM-related tables |
| `CondicionIVADAO.php` | `condicion_iva` |
| `CondicionPagoDAO.php` | `condicion_pago` |
| `ReportingDAO.php` | Cross-domain reporting queries |

---

## Gotchas

- **Dual write hazard**: Both Frontera (raw PDO in DAOs) and Benjamin (Eloquent ORM) write to the same MySQL tables. There is no locking coordination between them. A race condition is theoretically possible on high-frequency tables like `usuario_sesion`.
- **No `timestamps`**: Most Eloquent models set `$timestamps = false`. Benjamin does not auto-manage `created_at`/`updated_at`. Some tables use `record_insert_ts`/`record_update_ts` instead; others use `created_at` (e.g., `ap_factura`). Inconsistent across domains.
- **Composite PKs**: Several core tables (`gl_asiento`, `diario`, `gl_plan_cuenta` detail tables) use composite primary keys. Eloquent handles these awkwardly (`$primaryKey = ['idEmpresa', 'idAsiento']`), which breaks `find()`, `save()`, and route model binding.
- **PK naming inconsistency**: `empresa` uses `IdEmpresa` (capital I), `usuario` uses `id` (auto) + `idUsuario` (email string). `ar_factura` uses `idFactura`. No convention is enforced.
- **Orphaned tables**: Some tables created in early migrations (2014--2017) are no longer actively used by either Frontera or Benjamin but remain in the schema. The `users` and `password_resets` tables from Laravel's default migration exist but are unused -- Colppy uses `usuario` instead.
- **`idUsuario` is an email**: In the `usuario` table, `idUsuario` stores the user's email address (not a numeric ID). The actual numeric PK is `id`. The same column name `idUsuario` in `usuario_empresa` also stores the email. This is a common source of confusion.
- **`idUltimaEmpresa` shortcut**: The `usuario.idUltimaEmpresa` field stores the last-accessed company ID, used in the session query's `INNER JOIN empresa e ON e.IdEmpresa = u.idUltimaEmpresa`. This is a denormalized shortcut that can go stale.
- **Case-sensitive column refs**: The `empresa` table has `IdEmpresa` (capital I), but many queries reference it as `idEmpresa` (lowercase i). MySQL on Linux is case-sensitive for table/column names depending on `lower_case_table_names` setting.
- **`diario` is the universal journal**: Every financial transaction (sales, purchases, collections, payments, manual entries) writes rows to `diario`. The `idTabla` column is a discriminator that identifies the source module. Cross-module queries must filter on `idTabla`.
- **`decodificadora` as generic lookup**: Instead of dedicated lookup tables, Colppy uses a single `decodificadora` table with `idTabla` + `idElemento` + `idEmpresa` as a composite key. This is used for payment conditions, invoice states, and other enums.
- **svc_settings raw SQL**: The `svc_settings` NestJS service (`colppy/svc_settings/src/fusionauth/services/fusionauth.service.ts`) uses raw SQL string interpolation (not parameterized) for the main `getUserData` query, creating SQL injection risk.
- **Two `ar_cliente` models**: Both `Models/Customer.php` and `Models/Ar/Cliente.php` map to the same `ar_cliente` table. Same for `Models/Provider.php` and `Models/Ap/Proveedor.php` mapping to `ap_proveedor`.

---

## Cross-References

- [Backend Architecture](backend-architecture.md) -- dual Frontera/Benjamin DB access patterns and service boundaries
- [Provisiones Reference](provisiones-reference.md) -- DAO pattern, how Frontera provisions map to DAOs
- [Auth and Sessions](auth-and-sessions.md) -- `usuario_sesion` lifecycle, MD5 token generation, FusionAuth integration
- [API Reference](api-reference.md) -- API data shapes and how they map to these tables

---

*Last updated: 2026-03-03*
