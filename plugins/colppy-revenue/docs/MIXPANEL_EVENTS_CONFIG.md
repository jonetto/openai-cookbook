# Mixpanel Events Configuration - Colppy
## Complete Events Reference

**Project ID:** 2201475 (User Level Production)
**Source:** Lexicon CSV Export
**Last Updated:** 2026-03-13
**Total Events:** 590 (385 active, 195 hidden, 10 dropped)
**Custom Events:** 55

---

## KAN-12024 Dual-Group Migration (rolling out since 2026-03-11)

~20% of events now carry enriched super properties from the backend. Detect new-format events by checking for `product_id` field presence.

### New Super Properties on Events (post-KAN-12024)

| Property | Source | Example |
| --- | --- | --- |
| `product_id` (array) | `idEmpresa` — product subscription | `["106472"]` |
| `CUIT` | `facturacion.CUIT` — billing entity | `30716909804` |
| `Razon Social` | `facturacion.razonSocial` | `GIUSEPPE CARULLO` |
| `Nombre Plan` | `plan.nombre` via empresa.idPlan | `Essential` |
| `Plan` | `plan.idPlan` (numeric) | `676` |
| `Estado` | Empresa active status | `Activa` |
| `Es Contador` | Boolean | `0` |
| `Es Demo` | Boolean | `0` |
| `Fecha Alta` | `empresa.FechaAlta` | `2026-01-07T00:00:00` |
| `Fecha Vencimiento` | `empresa.fechaVencimiento` | `2026-04-10T00:00:00` |
| `Condicion Iva` | IVA condition | |
| `Domicilio` | Address | |
| `Rol` | User role (low coverage) | |
| `Mail Facturacion` | Billing email | |

### Handling Mixed Data During Rollout

```python
if event["properties"].get("product_id"):
    # New format — CUIT, Estado, Nombre Plan available directly
    empresa_id = event["properties"]["product_id"][0]  # array!
else:
    # Old format — need --enrich or Engage API
    empresa_id = event["properties"].get("company_id")
```

Validation script: `tools/scripts/mixpanel/kan12024_health_check.py`

---

## Event Categories Summary

| Category | Count | Top Events |
|----------|------:|------------|
| System ($) | 6 | $mp_click, $mp_session_record, $mp_web_page_view |
| Authentication & Registration | 6 | Login, Registro, Validó email |
| Company Management | 28 | Cambia Empresa desde Header, Abrió el módulo configuración de empresa, Editó tasa de cambio aplicado |
| Invoicing & Sales (Venta) | 19 | Abrió el módulo clientes, Generó comprobante de venta, Seleccionó la opción para agregar un comprobante de venta |
| Purchases (Compra) | 18 | Generó comprobante de compra, Abrió el módulo proveedores, Seleccionó la opción para agregar un comprobante de compra |
| Collections & Payments (Cobro/Pago) | 16 | Agregó medio de pago, Agregó medio de cobro, Click en agregar pago |
| Banking & Finance | 13 | Realizó depósito de cheques, Click en botón Conectar banco, Descargó el reporte de cheques en cartera |
| Accounting & Reports | 53 | Click en guardar Asiento, Abrió el módulo contabilidad, Generó asiento contable |
| Payroll (Sueldos) | 4 | Liquidar sueldo, Click en sueldos, cargo Legajos Masivo |
| Inventory | 22 | Click en guardar factura con Lista de precios, Agregó un ítem, Seleccionó agregar ítem |
| Import/Export | 18 | Seleccionó opción para importar, Subió archivo para importar, Finalizó importación |
| Configuration & Setup | 18 | Agregó un talonario, Descargó el plan de cuentas, Configura Talonario FE |
| Mobile App | 40 | app seleccionó crear cuenta gratis, app abrió el módulo tablero, app abrió modulo clientes |
| UI Navigation | 62 | Visualizó inicio colppy, Abrió el módulo tesorería, website_clicks |
| Marketing & Website | 2 | Website, Website_Price_Button |
| NPS & Feedback | 5 | Sugiere idea en ideas.colppy.com, Novedades - Feedback Útil, Completó encuesta NPS |
| Other | 55 | Descargó el mayor, Realizó canje interno de caja, Elige tipo de moneda |

---

## System ($)
*6 events*

| Event | Volume | Query Vol | Props | Tags |
|-------|-------:|----------:|------:|------|
| `$mp_click` | 18,780,127 | 0 | 98 |  |
| `$mp_session_record` | 532,534 | 22 | 18 |  |
| `$mp_web_page_view` | 393,762 | 0 | 83 |  |
| `$identify` | 168,539 | 1,606 | 79 |  |
| `$session_start` | 0 | 90 | 0 |  |
| `$session_end` | 0 | 40 | 0 |  |

**`$mp_click` key properties:** `Administradora Id`, `CUIT`, `Calcula Perc AGIP`, `Calcula Perc ARBA`, `Condicion Iva`, `Domicilio`, `Email`, `Envio Cobro`
**`$mp_session_record` key properties:** `batch_start_time`, `replay_region`, `replay_start_url`, `seq_no`
**`$mp_web_page_view` key properties:** `current_domain`, `current_page_title`, `current_url_path`, `current_url_protocol`, `current_url_search`, `Tipo Plan Empresa`, `company_id`, `Administradora Id`

---

## Authentication & Registration
*6 events*

| Event | Volume | Query Vol | Props | Tags |
|-------|-------:|----------:|------:|------|
| `Login` | 166,265 | 880 | 82 |  |
| `Registro` | 8,068 | 2,253 | 65 |  |
| `Validó email` | 6,032 | 16,835 | 37 |  |
| `esueldos_autoregistro_exitoso` | 103 | 1,451 | 7 |  |
| `esueldos_autoregistro_fallido` | 15 | 0 | 8 |  |
| `Registro email existente` | 0 | 0 | 0 |  |

**`Login` key properties:** `App Type`, `Email de Administrador`, `Fecha de Alta Empresa`, `Nombre de Empresa`, `Pais de Registro`, `Tipo Plan Empresa`, `ad_id`, `adset_id`
**`Registro` key properties:** `gclid`, `utm_campaign`, `utm_medium`, `utm_source`, `wbraid`, `ad_id`, `adset_id`, `fbclid`
**`Validó email` key properties:** `utm_campaign`, `utm_medium`, `utm_source`, `utm_term`, `ad_id`, `adset_id`, `fbclid`, `first_fbclid`

---

## Company Management
*28 events*

| Event | Volume | Query Vol | Props | Tags |
|-------|-------:|----------:|------:|------|
| `Cambia Empresa desde Header` | 74,005 | 0 | 75 |  |
| `Abrió el módulo configuración de empresa` | 15,953 | 4 | 68 |  |
| `Editó tasa de cambio aplicado` | 8,448 | 0 | 67 |  |
| `Cambia solapa en comprobante` | 4,951 | 0 | 67 |  |
| `Cambió de empresa` | 1,488 | 0 | 74 |  |
| `Finalizar Wizard` | 1,370 | 3,536 | 38 |  |
| `Invitó usuario` | 209 | 18 | 55 |  |
| `Click cambiar dia en minicalendario` | 100 | 0 | 36 |  |
| `Agregó una empresa` | 84 | 0 | 66 |  |
| `Click cambiar dia, semana o mes en navegador de fechas` | 81 | 0 | 36 |  |
| `Cambió el medio de pago` | 44 | 0 | 61 |  |
| `Cambió la contraseña` | 37 | 0 | 49 |  |
| `Crear Empresa` | 28 | 289 | 30 | Eventos Sueldos |
| `Click abrir filtro empresas` | 25 | 0 | 35 |  |
| `Click cerrar filtro empresas` | 10 | 0 | 34 |  |
| `Empresa Reactivada` | 2 | 0 | 20 |  |
| `Eliminó las transacciones de la empresa` | 1 | 0 | 21 |  |
| `Click en Empresa Demo` | 0 | 16 | 0 |  |
| `Click en Atras Wizard` | 0 | 0 | 0 |  |
| `Click en Cambiar Plan 497` | 0 | 0 | 0 |  |
| `Click en Cambiar Plan 520` | 0 | 0 | 0 |  |
| `Click en Cambiar Plan 521` | 0 | 0 | 0 |  |
| `Click en Cambiar Plan 522` | 0 | 0 | 0 |  |
| `Click en Cambiar Plan 523` | 0 | 0 | 0 |  |
| `Click en Cambiar Plan 524` | 0 | 0 | 0 |  |
| `Click en Cambiar medio de pago en Notificación pago` | 0 | 0 | 0 |  |
| `Click en Ir a configurar empresa` | 0 | 0 | 0 |  |
| `Click en Siguiente Wizard` | 0 | 0 | 0 |  |

**`Cambia Empresa desde Header` key properties:** `Administradora Id`, `CUIT`, `Calcula Perc AGIP`, `Calcula Perc ARBA`, `Condicion Iva`, `Domicilio`, `Email`, `Envio Cobro`
**`Abrió el módulo configuración de empresa` key properties:** `Administradora Id`, `CUIT`, `Calcula Perc AGIP`, `Calcula Perc ARBA`, `Condicion Iva`, `Domicilio`, `Email`, `Envio Cobro`
**`Editó tasa de cambio aplicado` key properties:** `Tipo Plan Empresa`, `company_id`, `ad_id`, `adset_id`, `fbclid`, `first_fbclid`, `first_utm_campaign`, `first_utm_source`

---

## Invoicing & Sales (Venta)
*19 events*

| Event | Volume | Query Vol | Props | Tags |
|-------|-------:|----------:|------:|------|
| `Abrió el módulo clientes` | 208,758 | 14 | 76 |  |
| `Generó comprobante de venta` | 175,327 | 36 | 87 |  |
| `Seleccionó la opción para agregar un comprobante de venta` | 121,825 | 0 | 77 |  |
| `Imprimió comprobante de venta` | 76,268 | 0 | 69 |  |
| `No generó comprobante de venta` | 45,901 | 0 | 5 |  |
| `Abrió el módulo inventario` | 31,392 | 4 | 68 |  |
| `Click en agregar cliente` | 21,280 | 0 | 67 |  |
| `Agregó un cliente` | 19,721 | 72 | 68 |  |
| `Descargó el libro iva ventas` | 9,877 | 0 | 68 |  |
| `Descargó el listado de comprobantes de venta` | 6,504 | 0 | 68 |  |
| `Generó un ajuste de inventario` | 4,568 | 0 | 65 |  |
| `Descargó el listado de clientes` | 1,124 | 0 | 67 |  |
| `Descargó el listado de comprobantes de venta borrador` | 256 | 0 | 66 |  |
| `Visualizó ventana de upsell` | 253 | 549 | 68 |  |
| `Descargó el listado de ítems de inventario` | 253 | 0 | 68 |  |
| `Importacion Clientes` | 128 | 0 | 66 |  |
| `Contactar a ventas plan contador` | 46 | 0 | 61 |  |
| `Click en ir a items de inventario desde Listas de Precios` | 2 | 0 | 22 |  |
| `Click en reporte IVA Ventas` | 0 | 0 | 0 |  |

**`Abrió el módulo clientes` key properties:** `Administradora Id`, `CUIT`, `Calcula Perc AGIP`, `Calcula Perc ARBA`, `Condicion Iva`, `Domicilio`, `Email`, `Envio Cobro`
**`Generó comprobante de venta` key properties:** `Tipo Plan Empresa`, `amount`, `company_id`, `currency`, `has_price_list`, `invoice_origin`, `is_fce`, `is_fe`
**`Seleccionó la opción para agregar un comprobante de venta` key properties:** `Option`, `Tipo Plan Empresa`, `company_id`, `ad_id`, `adset_id`, `fbclid`, `first_fbclid`, `first_utm_campaign`

---

## Purchases (Compra)
*18 events*

| Event | Volume | Query Vol | Props | Tags |
|-------|-------:|----------:|------:|------|
| `Generó comprobante de compra` | 232,268 | 5 | 79 |  |
| `Abrió el módulo proveedores` | 195,051 | 9 | 70 |  |
| `Seleccionó la opción para agregar un comprobante de compra` | 119,173 | 0 | 70 |  |
| `Agregó un proveedor` | 32,377 | 32 | 68 |  |
| `Click en agregar proveedor` | 19,843 | 0 | 66 |  |
| `Descargó el libro iva compras` | 9,133 | 0 | 68 |  |
| `Click en reporte IVA Compras` | 7,531 | 0 | 67 |  |
| `Descargó el listado de comprobantes de compra` | 3,834 | 0 | 68 |  |
| `Click en reporte Listado Proveedores` | 1,313 | 0 | 67 |  |
| `Descargó el listado de proveedores` | 1,115 | 0 | 68 |  |
| `Imprimió orden de compra` | 881 | 0 | 67 |  |
| `Importacion de Factura de compra - Mis comprobantes` | 734 | 0 | 52 |  |
| `Click en reporte CITI Compras y Ventas` | 478 | 0 | 66 |  |
| `Descargó el listado de comprobantes de compra borrador` | 245 | 0 | 67 |  |
| `Importar proveedores` | 64 | 0 | 62 |  |
| `Descargó el régimen de información de compras y ventas` | 29 | 0 | 22 |  |
| `Importacion de Factura de Compra` | 0 | 0 | 0 |  |
| `Vio anuncio e hizo click en importación factura de compra` | 0 | 0 | 0 |  |

**`Generó comprobante de compra` key properties:** `Tipo Plan Empresa`, `amount`, `company_id`, `currency`, `has_price_list`, `invoice_origin`, `is_fce`, `operaciones`
**`Abrió el módulo proveedores` key properties:** `Administradora Id`, `CUIT`, `Calcula Perc AGIP`, `Calcula Perc ARBA`, `Condicion Iva`, `Domicilio`, `Email`, `Envio Cobro`
**`Seleccionó la opción para agregar un comprobante de compra` key properties:** `Option`, `Tipo Plan Empresa`, `company_id`, `from`, `utm_campaign`, `utm_medium`, `utm_source`, `ad_id`

---

## Collections & Payments (Cobro/Pago)
*16 events*

| Event | Volume | Query Vol | Props | Tags |
|-------|-------:|----------:|------:|------|
| `Agregó medio de pago` | 251,585 | 0 | 70 |  |
| `Agregó medio de cobro` | 182,314 | 0 | 72 |  |
| `Click en agregar pago` | 162,741 | 1 | 71 |  |
| `Generó orden de pago` | 140,147 | 0 | 67 |  |
| `Click en agregar cobro` | 110,101 | 0 | 69 |  |
| `Generó recibo de cobro` | 102,996 | 0 | 68 |  |
| `Genera nuevo pago` | 42,757 | 0 | 67 |  |
| `Envió recibo de cobro` | 6,477 | 0 | 66 |  |
| `Envió orden de pago` | 3,345 | 0 | 66 |  |
| `Descargó el listado de pagos` | 1,295 | 0 | 67 |  |
| `Guardó configuración mercado pago` | 5 | 0 | 60 |  |
| `Notificó pago transferencia anual` | 1 | 0 | 34 |  |
| `Click en Cerrar Notificación pago` | 0 | 0 | 0 |  |
| `Click en Modificar CBU en Notificación pago` | 0 | 0 | 0 |  |
| `Click en integracion con Mercado Pago (MPC)` | 0 | 0 | 0 |  |
| `Genera nuevo cobro` | 0 | 0 | 0 |  |

**`Agregó medio de pago` key properties:** `Administradora Id`, `CUIT`, `Calcula Perc AGIP`, `Calcula Perc ARBA`, `Condicion Iva`, `Document_type`, `Domicilio`, `Email`
**`Agregó medio de cobro` key properties:** `Administradora Id`, `CUIT`, `Calcula Perc AGIP`, `Calcula Perc ARBA`, `Condicion Iva`, `Document_type`, `Domicilio`, `Email`
**`Click en agregar pago` key properties:** `Document_type`, `Tipo Plan Empresa`, `company_id`, `from`, `ad_id`, `adset_id`, `fbclid`, `first_fbclid`

---

## Banking & Finance
*13 events*

| Event | Volume | Query Vol | Props | Tags |
|-------|-------:|----------:|------:|------|
| `Realizó depósito de cheques` | 4,391 | 4 | 66 |  |
| `Click en botón Conectar banco` | 635 | 0 | 67 |  |
| `Descargó el reporte de cheques en cartera` | 606 | 4 | 67 |  |
| `Descargó el reporte de cheques emitidos diferidos` | 519 | 4 | 66 |  |
| `Descargó el reporte de seguimiento de cheques` | 198 | 0 | 51 |  |
| `Conectó el banco` | 133 | 0 | 64 |  |
| `Desconectó el banco` | 109 | 0 | 67 |  |
| `Seleccionó la opción agregar chequera` | 67 | 0 | 52 |  |
| `Agregó una chequera` | 40 | 4 | 52 |  |
| `Click en reporte Cheques emitidos diferidos` | 0 | 4 | 0 |  |
| `Click en reporte Cheques en cartera` | 0 | 4 | 0 |  |
| `Click en Desconectar tu banco` | 0 | 0 | 0 |  |
| `Click en agregar chequera` | 0 | 0 | 0 |  |

**`Realizó depósito de cheques` key properties:** `Tipo Plan Empresa`, `company_id`, `ad_id`, `adset_id`, `fbclid`, `first_fbclid`, `first_utm_campaign`, `first_utm_source`
**`Click en botón Conectar banco` key properties:** `Tipo Plan Empresa`, `company_id`, `ad_id`, `adset_id`, `fbclid`, `first_fbclid`, `first_utm_campaign`, `first_utm_source`
**`Descargó el reporte de cheques en cartera` key properties:** `Tipo Plan Empresa`, `company_id`, `format`, `ad_id`, `adset_id`, `fbclid`, `first_fbclid`, `first_utm_campaign`

---

## Accounting & Reports
*53 events*

| Event | Volume | Query Vol | Props | Tags |
|-------|-------:|----------:|------:|------|
| `Click en guardar Asiento` | 100,465 | 0 | 68 |  |
| `Abrió el módulo contabilidad` | 85,869 | 4 | 70 |  |
| `Generó asiento contable` | 73,734 | 24 | 69 |  |
| `Click en Clonar Asiento a Diario` | 45,725 | 0 | 68 |  |
| `Click en Nuevo Asiento a Diario` | 33,135 | 0 | 66 |  |
| `Click en Botón de Operación Contabilizar` | 16,793 | 0 | 66 |  |
| `Click en reporte Mayor` | 12,659 | 0 | 68 |  |
| `Descargó el retenciones y percepciones` | 7,677 | 0 | 70 |  |
| `Descargó el balance` | 7,184 | 0 | 68 |  |
| `Click en reporte Balance` | 6,384 | 0 | 67 |  |
| `Click en reporte Retenciones y percepciones` | 4,127 | 0 | 67 |  |
| `Click en libro iva digital` | 3,916 | 0 | 67 |  |
| `Agregó una cuenta contable` | 3,347 | 0 | 69 |  |
| `Descargó la posición impositiva mensual` | 3,345 | 0 | 67 |  |
| `Click en reporte Posición impositiva mensual` | 3,230 | 0 | 67 |  |
| `Click en descargar archivos del libro iva digital` | 3,187 | 0 | 67 |  |
| `Descargó el libro iva digital` | 3,186 | 0 | 67 |  |
| `Importacion Asientos` | 2,168 | 0 | 66 |  |
| `Seleccionó la opción asiento de cierre y apertura` | 2,015 | 0 | 66 |  |
| `Click en reporte Diario general` | 1,875 | 0 | 66 |  |
| `Click en reporte Resultado por CCosto` | 1,362 | 0 | 66 |  |
| `Click Terminar e imprimir reporte` | 1,361 | 0 | 66 |  |
| `Seleccionó la opción asiento de refundición` | 1,302 | 0 | 66 |  |
| `Genera reporte listado de movimientos` | 1,216 | 0 | 65 |  |
| `Click en reporte Estado de resultados` | 1,205 | 0 | 66 |  |
| `Click en generar asientos de cierre y apertura de ejercicio` | 1,061 | 0 | 66 |  |
| `Click en reporte listado de movimientos` | 1,016 | 0 | 66 |  |
| `Seleccionó la opción asiento de ajuste por inflación` | 877 | 0 | 66 |  |
| `Click en Generar Asiento de ajuste por inflación` | 731 | 0 | 66 |  |
| `Novedad Masiva` | 435 | 0 | 30 | Eventos Sueldos |
| `Click en reporte disponibilidad por deposito` | 309 | 0 | 61 |  |
| `Genera Reporte disponibilidad por deposito` | 297 | 0 | 61 |  |
| `Click en reporte Estado de flujo de efectivo` | 124 | 0 | 66 |  |
| `Imprimir Facturas Masivamente` | 109 | 0 | 61 |  |
| `Click en desactivar productos en Listas de Precios` | 76 | 0 | 47 |  |
| `Click en activar mi cuenta` | 55 | 0 | 62 |  |
| `Pedido de desactivación` | 43 | 0 | 47 |  |
| `Click en activar productos en Listas de Precios` | 35 | 0 | 21 |  |
| `Click en desactivar lista de precios` | 17 | 0 | 21 |  |
| `Exportar Asiento Contable` | 17 | 0 | 30 | Eventos Sueldos |
| `Click en Generar Asiento de Ajuste de Saldos Iniciales` | 9 | 0 | 21 |  |
| `Click en activar lista de precios` | 6 | 0 | 21 |  |
| `Click en activar impuestos en setup calendario de vencimientos` | 2 | 0 | 21 |  |
| `Click Terminar e Imprimir Reporte` | 0 | 0 | 0 |  |
| `Click en Generar Asiento de Ajuste por Inflación` | 0 | 0 | 0 |  |
| `Click en desactivar impuestos en setup calendario de vencimientos` | 0 | 0 | 0 |  |
| `Click en reporte Diario General` | 0 | 0 | 0 |  |
| `Click en reporte Estado de Flujo de Efectivo` | 0 | 0 | 0 |  |
| `Click en reporte Estado de Resultados` | 0 | 0 | 0 |  |
| `Click en reporte Posición Impositiva Mensual` | 0 | 0 | 0 |  |
| `Click en reporte Retenciones y Percepciones` | 0 | 0 | 0 |  |
| `Estudio contable o consultoría` | 0 | 0 | 0 |  |
| `Genera Reporte Listado de Movimientos` | 0 | 0 | 0 |  |

**`Click en guardar Asiento` key properties:** `Tipo Plan Empresa`, `company_id`, `ad_id`, `adset_id`, `fbclid`, `first_fbclid`, `first_utm_campaign`, `first_utm_source`
**`Abrió el módulo contabilidad` key properties:** `Administradora Id`, `CUIT`, `Calcula Perc AGIP`, `Calcula Perc ARBA`, `Condicion Iva`, `Domicilio`, `Email`, `Envio Cobro`
**`Generó asiento contable` key properties:** `Tipo Plan Empresa`, `company_id`, `type`, `ad_id`, `adset_id`, `fbclid`, `first_fbclid`, `first_utm_campaign`

---

## Payroll (Sueldos)
*4 events*

| Event | Volume | Query Vol | Props | Tags |
|-------|-------:|----------:|------:|------|
| `Liquidar sueldo` | 5,365 | 1,767 | 32 | Eventos Sueldos, Eventos Clave |
| `Click en sueldos` | 1,492 | 374 | 69 |  |
| `cargo Legajos Masivo` | 24 | 265 | 30 |  |
| `Cargo Legajo` | 0 | 292 | 0 |  |

**`Liquidar sueldo` key properties:** `Account_id`, `Company Name`, `Company_id`, `Email`, `Plan_id`, `Product_id`, `Rol`, `User Name`
**`Click en sueldos` key properties:** `Tipo Plan Empresa`, `company_id`, `from`, `utm_campaign`, `utm_medium`, `utm_source`, `ad_id`, `adset_id`
**`cargo Legajos Masivo` key properties:** `Account_id`, `Company Name`, `Company_id`, `Email`, `Plan_id`, `Product_id`, `Rol`, `User Name`

---

## Inventory
*22 events*

| Event | Volume | Query Vol | Props | Tags |
|-------|-------:|----------:|------:|------|
| `Click en guardar factura con Lista de precios` | 7,686 | 0 | 66 |  |
| `Agregó un ítem` | 4,004 | 0 | 67 |  |
| `Seleccionó agregar ítem` | 2,835 | 0 | 67 |  |
| `Click en solapa listas de precios` | 1,562 | 0 | 64 |  |
| `Click en editar precios en Listas de Precios` | 1,490 | 0 | 48 |  |
| `Click en guardar editar precios en Lista de precios` | 1,488 | 0 | 48 |  |
| `Seleccionó la opción actualizar precios en pantalla masivo` | 609 | 0 | 63 |  |
| `Vencimientos - Item Seleccionado` | 506 | 592 | 69 |  |
| `Actualizó precios en pantalla masivo` | 504 | 0 | 49 |  |
| `Importacion de items` | 117 | 0 | 36 |  |
| `Activó impresión de remitos sin precios` | 72 | 0 | 47 |  |
| `Click en agregar lista de precios` | 43 | 0 | 63 |  |
| `Click en productos inactivos de Listas de Precios` | 43 | 0 | 21 |  |
| `Click en editar lista de precios` | 36 | 0 | 22 |  |
| `Click en guardar edición de lista de precios` | 28 | 0 | 21 |  |
| `Click en descargar excel de Lista de precios` | 23 | 0 | 46 |  |
| `Click en guardar nueva lista de precios` | 20 | 0 | 22 |  |
| `Click en duplicar lista de precio` | 6 | 0 | 21 |  |
| `Click en ir a Productos inactivos de Listas de Precios` | 6 | 0 | 22 |  |
| `Click Upselling en listas de precios` | 0 | 0 | 0 |  |
| `Click en guardar factura con Lista de Precios` | 0 | 0 | 0 |  |
| `Completa tour de configurar remito sin precio` | 0 | 0 | 0 |  |

**`Click en guardar factura con Lista de precios` key properties:** `Tipo Plan Empresa`, `company_id`, `ad_id`, `adset_id`, `fbclid`, `first_fbclid`, `first_utm_campaign`, `first_utm_source`
**`Agregó un ítem` key properties:** `Administradora Id`, `CUIT`, `Calcula Perc AGIP`, `Calcula Perc ARBA`, `Condicion Iva`, `Domicilio`, `Email`, `Envio Cobro`
**`Seleccionó agregar ítem` key properties:** `Tipo Plan Empresa`, `company_id`, `ad_id`, `adset_id`, `fbclid`, `first_fbclid`, `first_utm_campaign`, `first_utm_source`

---

## Import/Export
*18 events*

| Event | Volume | Query Vol | Props | Tags |
|-------|-------:|----------:|------:|------|
| `Seleccionó opción para importar` | 18,612 | 0 | 68 |  |
| `Subió archivo para importar` | 10,244 | 0 | 69 |  |
| `Finalizó importación` | 9,789 | 44 | 70 |  |
| `Visualizó detalle de importación` | 8,967 | 0 | 68 |  |
| `Abrió la solapa importación de facturas` | 8,811 | 0 | 68 |  |
| `Seleccionó la opción editar en fila a importar con error` | 6,464 | 0 | 67 |  |
| `Canceló en editar fila a importar con error` | 6,460 | 0 | 67 |  |
| `Corrigió fila a importar con error` | 5,663 | 0 | 67 |  |
| `Click descarga archivo mis comprobantes ARCA recibidos` | 760 | 0 | 66 |  |
| `Click  descarga archivo Mis comprobantes ARCA emitidos` | 708 | 0 | 57 |  |
| `Seleccionó la opción eliminar en filas a importar con error` | 578 | 0 | 69 |  |
| `Eliminó filas a importar con error` | 533 | 0 | 69 |  |
| `Boolfy - Archivo Seleccionado` | 105 | 30 | 66 |  |
| `Boolfy - Archivo Subido` | 102 | 69 | 66 |  |
| `Descargó el modelo de importación del plan de cuentas` | 19 | 24 | 66 |  |
| `Click  descarga archivo Mis comprobantes AFIP emitidos` | 0 | 0 | 0 |  |
| `Click  descarga archivo Mis comprobantes AFIP recibidos` | 0 | 0 | 0 |  |
| `Click descarga archivo mis comprobantes AFIP recibidos` | 0 | 0 | 0 |  |

**`Seleccionó opción para importar` key properties:** `Tipo Plan Empresa`, `company_id`, `importer_type`, `ad_id`, `adset_id`, `fbclid`, `first_fbclid`, `first_utm_campaign`
**`Subió archivo para importar` key properties:** `Tipo Plan Empresa`, `checkbox_altacliente`, `company_id`, `importer_type`, `checkbox_altaproveedor`, `ad_id`, `adset_id`, `fbclid`
**`Finalizó importación` key properties:** `importer_type`, `Tipo Plan Empresa`, `company_id`, `imported_rows_failed`, `imported_rows_ok`, `total_rows`, `ad_id`, `adset_id`

---

## Configuration & Setup
*18 events*

| Event | Volume | Query Vol | Props | Tags |
|-------|-------:|----------:|------:|------|
| `Agregó un talonario` | 972 | 2 | 66 |  |
| `Descargó el plan de cuentas` | 309 | 0 | 67 |  |
| `Configura Talonario FE` | 235 | 0 | 53 |  |
| `Configuró Calculo automatico de ARBA` | 213 | 0 | 62 |  |
| `Click en comenzar primeros pasos` | 199 | 6 | 63 |  |
| `Seleccionó la opción de configurar delegación factura electrónica` | 169 | 0 | 64 |  |
| `Seleccionó la opción nuevo plan de cuentas` | 136 | 0 | 67 |  |
| `Cerró primeros pasos` | 43 | 0 | 63 |  |
| `Inició proceso de configuración FE` | 29 | 0 | 63 |  |
| `Envió el plan de cuentas al contador` | 18 | 0 | 22 |  |
| `Finalizó configuración FE` | 17 | 22 | 5 |  |
| `Configuró Calculo automatico de AGIP` | 16 | 0 | 22 |  |
| `Finalizó primeros pasos` | 16 | 0 | 61 |  |
| `Envió el plan de cuentas a soporte` | 12 | 24 | 36 |  |
| `Adjuntó el plan de cuentas` | 11 | 0 | 36 |  |
| `Click en video para editar Plan de Cuentas` | 0 | 0 | 0 |  |
| `Completó el tour primeros Pasos` | 0 | 0 | 0 |  |
| `Configura Calculo automatico de ARBA` | 0 | 0 | 0 |  |

**`Agregó un talonario` key properties:** `Administradora Id`, `CUIT`, `Calcula Perc AGIP`, `Calcula Perc ARBA`, `Condicion Iva`, `Domicilio`, `Email`, `Envio Cobro`
**`Descargó el plan de cuentas` key properties:** `Tipo Plan Empresa`, `ad_id`, `adset_id`, `company_id`, `fbclid`, `first_fbclid`, `first_utm_campaign`, `first_utm_source`
**`Configura Talonario FE` key properties:** `Tipo Plan Empresa`, `company_id`, `Administradora Id`, `CUIT`, `Calcula Perc AGIP`, `Calcula Perc ARBA`, `Condicion Iva`, `Domicilio`

---

## Mobile App
*40 events*

| Event | Volume | Query Vol | Props | Tags |
|-------|-------:|----------:|------:|------|
| `app seleccionó crear cuenta gratis` | 780 | 0 | 24 | Eventos mobile |
| `app abrió el módulo tablero` | 727 | 0 | 23 | Eventos mobile |
| `app abrió modulo clientes` | 614 | 0 | 23 |  |
| `app login` | 414 | 0 | 24 | Eventos mobile |
| `app seleccionó el listado de clientes` | 159 | 0 | 20 |  |
| `app abrió detalle de comprobante de venta` | 141 | 0 | 21 | Eventos mobile |
| `app seleccionó el listado de facturas cobradas` | 140 | 0 | 21 | Eventos mobile |
| `app abrió el módulo proveedores` | 104 | 0 | 20 | Eventos mobile |
| `app seleccionó el listado de facturas impagas` | 102 | 0 | 21 | Eventos mobile |
| `app abrió el alta de comprobante de venta` | 94 | 0 | 20 | Eventos mobile |
| `app validó que no tiene datos de facturación por defecto` | 68 | 0 | 21 | Eventos mobile |
| `app compartió comprobante de venta` | 64 | 0 | 22 | Eventos mobile |
| `app click en shortcut tablero` | 51 | 0 | 20 |  |
| `app generó comprobante de venta` | 48 | 0 | 40 | Eventos mobile |
| `app abrió consultar productos` | 38 | 0 | 20 | Eventos mobile |
| `app seleccionó el listado de facturas borrador` | 34 | 0 | 21 | Eventos mobile |
| `app abrió el módulo clientes` | 28 | 0 | 18 | Eventos mobile |
| `app seleccionó el listado de proveedores` | 28 | 0 | 20 | Eventos mobile |
| `app cambió de empresa` | 27 | 0 | 22 | Eventos mobile |
| `app imprimió comprobante de venta` | 24 | 0 | 22 | Eventos mobile |
| `app no generó comprobante de venta` | 24 | 0 | 41 | Eventos mobile |
| `app abrió el módulo facturas` | 20 | 0 | 18 | Eventos mobile |
| `app cambió filtro de facturas de clientes` | 20 | 0 | 22 |  |
| `app seleccionó el listado de facturas pagadas` | 16 | 0 | 20 | Eventos mobile |
| `app generó recibo de cobro` | 15 | 0 | 21 | Eventos mobile |
| `app seleccionó el listado de facturas impagas proveedores` | 14 | 0 | 20 | Eventos mobile |
| `app actualizó facturación por defecto` | 13 | 0 | 20 |  |
| `app abrió detalle de comprobante de compra` | 12 | 0 | 20 | Eventos mobile |
| `app seleccionó el listado de Bancos` | 9 | 0 | 21 | Eventos mobile |
| `app abrió escanear productos` | 7 | 0 | 20 | Eventos mobile |
| `app agregó un cliente` | 7 | 0 | 20 | Eventos mobile |
| `app validó que no tiene talonarios` | 7 | 0 | 21 | Eventos mobile |
| `app cambió filtro de facturas de proveedores` | 4 | 0 | 22 |  |
| `app configuró facturación por defecto` | 4 | 0 | 20 | Eventos mobile |
| `app seleccionó el listado de Cajas` | 4 | 0 | 21 | Eventos mobile |
| `app seleccionó lista de precios en la factura` | 2 | 0 | 20 | Eventos mobile |
| `app seleccionó el listado de Tarjetas de crédito` | 1 | 0 | 21 | Eventos mobile |
| `app agregó un proveedor` | 0 | 0 | 0 |  |
| `app agregó un ítem` | 0 | 0 | 0 |  |
| `app seleccionó ver más facturas` | 0 | 0 | 0 | Eventos mobile |

**`app seleccionó crear cuenta gratis` key properties:** `Tipo Plan Empresa`, `company_id`
**`app abrió el módulo tablero` key properties:** `Tipo Plan Empresa`, `company_id`
**`app abrió modulo clientes` key properties:** `Tipo Plan Empresa`, `company_id`

---

## UI Navigation
*62 events*

| Event | Volume | Query Vol | Props | Tags |
|-------|-------:|----------:|------:|------|
| `Visualizó inicio colppy` | 240,233 | 3,842 | 75 |  |
| `Abrió el módulo tesorería` | 94,796 | 4 | 70 |  |
| `website_clicks` | 69,961 | 1,045 | 81 |  |
| `Click en Botón de Operación Conciliar` | 55,683 | 0 | 66 |  |
| `Click en buscar movimientos en la conciliación` | 32,443 | 0 | 69 |  |
| `Seleccionó la opción conciliar` | 26,563 | 0 | 68 |  |
| `Click Tablero` | 11,304 | 0 | 69 |  |
| `Seleccionó agregar remito` | 7,395 | 0 | 67 |  |
| `Click en icono ayuda` | 7,366 | 0 | 68 |  |
| `Click en emitir nota de crédito automática` | 6,562 | 0 | 68 |  |
| `Abrió el módulo mi cuenta colppy` | 5,896 | 0 | 74 |  |
| `Click en guardar nota de crédito automática` | 5,415 | 0 | 70 |  |
| `Click en eliminar movimiento del extracto en la Conciliación` | 4,869 | 0 | 66 |  |
| `Click en Escribinos ahora` | 4,214 | 0 | 68 |  |
| `Click en escribinos ahora` | 4,214 | 0 | 68 |  |
| `Abrió el Calendario de Vencimientos` | 1,208 | 878 | 67 |  |
| `Click en pagar` | 928 | 24 | 67 |  |
| `Click en novedades` | 842 | 4 | 66 |  |
| `Seleccionó la opción perfil` | 721 | 0 | 68 |  |
| `Click en el buscador de Intercom` | 704 | 0 | 67 |  |
| `Seleccionó la opción agregar cuenta de tesorería` | 608 | 0 | 66 |  |
| `Click en ayuda` | 556 | 0 | 67 |  |
| `Seleccionó invitar usuario` | 392 | 0 | 73 |  |
| `Boolfy - Visualización de Créditos` | 332 | 19 | 70 |  |
| `Click en Descargar Papel de Trabajo` | 266 | 0 | 66 |  |
| `Click en el botón “Traer desde ARCA”.` | 230 | 0 | 67 |  |
| `Click en elegir plan` | 230 | 0 | 67 |  |
| `Click en posición de cuenta de tesorería` | 173 | 0 | 62 |  |
| `Click en pregunta frecuente` | 169 | 0 | 67 |  |
| `Click en generar facturas` | 141 | 0 | 49 |  |
| `Vencimientos - Agregar Custom Click` | 128 | 277 | 53 |  |
| `Seleccionó la opción recomendá y ganá` | 105 | 0 | 62 |  |
| `Click cerrar calendario` | 101 | 0 | 37 |  |
| `Click en uso de remitos` | 101 | 0 | 48 |  |
| `Click en capacitaciones` | 96 | 0 | 67 |  |
| `Boolfy - Ver Detalle Click` | 78 | 10 | 69 |  |
| `Click en sugerencias` | 62 | 0 | 53 |  |
| `Click en empty state tablero` | 53 | 0 | 63 |  |
| `Click Upselling` | 40 | 569 | 36 |  |
| `Click en setup calendario de vencimientos` | 40 | 0 | 36 |  |
| `Click en multiples depositos` | 24 | 0 | 21 |  |
| `Novedades - Ver Más Detalles Click` | 22 | 10 | 41 |  |
| `Click cerrar filtro impuestos` | 21 | 0 | 35 |  |
| `Click abrir filtro impuestos` | 15 | 0 | 35 |  |
| `Click en impuestos inactivos en setup calendario de vencimientos` | 9 | 0 | 22 |  |
| `Click en guardar editar en setup calendario de vencimientos` | 4 | 0 | 34 |  |
| `Click en renovación anual` | 3 | 0 | 0 |  |
| `Click en Elegir un plan y pagar en Notificación trial` | 0 | 6 | 0 |  |
| `Click Upselling en Ajuste por inflación` | 0 | 0 | 0 |  |
| `Click Upselling en MIPYME` | 0 | 0 | 0 |  |
| `Click Upselling en abrir setup calendario` | 0 | 0 | 0 |  |
| `Click conectar MELI` | 0 | 0 | 0 |  |
| `Click en Cerrar Notificación trial` | 0 | 0 | 0 |  |
| `Click en Descarga automatica de Movimientos` | 0 | 0 | 0 |  |
| `Click en Quiero que me llamen` | 0 | 0 | 0 |  |
| `Click en quiero que me llamen` | 0 | 0 | 0 |  |
| `Click guardar comentarios calendario de vencimientos` | 0 | 0 | 0 |  |
| `Click pagar evento` | 0 | 0 | 0 |  |
| `Click presentar evento` | 0 | 0 | 0 |  |
| `Click_COM` | 0 | 0 | 0 |  |
| `Hace Click para Integrate Ahora en MELI` | 0 | 0 | 0 |  |
| `Visualizó aviso para delegar factura electrónica` | 0 | 0 | 0 |  |

**`Visualizó inicio colppy` key properties:** `Tipo Plan Empresa`, `company_id`, `utm_campaign`, `utm_medium`, `utm_source`, `gclid`, `ad_id`, `adset_id`
**`Abrió el módulo tesorería` key properties:** `Administradora Id`, `CUIT`, `Calcula Perc AGIP`, `Calcula Perc ARBA`, `Condicion Iva`, `Domicilio`, `Email`, `Envio Cobro`
**`website_clicks` key properties:** `Button Type`, `Href`, `Page URL`, `Tipo Plan Empresa`, `ab_variant`, `ad_id`, `adset_id`, `company_id`

---

## Marketing & Website
*2 events*

| Event | Volume | Query Vol | Props | Tags |
|-------|-------:|----------:|------:|------|
| `Website` | 42,813 | 849 | 77 |  |
| `Website_Price_Button` | 0 | 0 | 0 |  |

**`Website` key properties:** `ad_id`, `adset_id`, `fbclid`, `first_fbclid`, `first_utm_campaign`, `first_utm_source`, `placement`, `source_channel`

---

## NPS & Feedback
*5 events*

| Event | Volume | Query Vol | Props | Tags |
|-------|-------:|----------:|------:|------|
| `Sugiere idea en ideas.colppy.com` | 11 | 0 | 6 |  |
| `Novedades - Feedback Útil` | 7 | 4 | 41 |  |
| `Completó encuesta NPS` | 7 | 0 | 4 |  |
| `Novedades - Feedback No Útil` | 1 | 4 | 26 |  |
| `Respondió Encuesta` | 0 | 0 | 0 |  |

**`Sugiere idea en ideas.colppy.com` key properties:** `Cantidad de Comentarios`, `Descripción`, `Status`, `Título`
**`Novedades - Feedback Útil` key properties:** `Tipo Plan Empresa`, `company_id`, `fecha`, `noticia_categoria`, `noticia_destacada`, `noticia_id`, `noticia_titulo`, `tiene_link`
**`Completó encuesta NPS` key properties:** `Comentario NPS`, `Score`

---

## Other
*55 events*

| Event | Volume | Query Vol | Props | Tags |
|-------|-------:|----------:|------:|------|
| `Descargó el mayor` | 17,359 | 0 | 69 |  |
| `Realizó canje interno de caja` | 9,289 | 0 | 67 |  |
| `Elige tipo de moneda` | 6,877 | 0 | 67 |  |
| `Generó un remito` | 4,067 | 0 | 66 |  |
| `Completó el tour` | 3,341 | 2,232 | 38 |  |
| `Novedad Manual` | 3,261 | 0 | 30 | Eventos Sueldos |
| `Descargó el diario general` | 1,604 | 0 | 67 |  |
| `Descargó el listado de cobranzas` | 1,546 | 0 | 68 |  |
| `Descargó el resultado por centros de costo` | 1,345 | 0 | 67 |  |
| `Vencimientos - Página Vista` | 1,296 | 956 | 69 |  |
| `Descargó el estado de resultados` | 1,272 | 0 | 67 |  |
| `Realizó depósito o extracción de efectivo` | 967 | 0 | 56 |  |
| `Presentar liquidacion` | 701 | 0 | 30 | Eventos Sueldos, Eventos Clave |
| `Descargó movimientos no conciliados` | 555 | 0 | 54 |  |
| `Agregó una cuenta de tesorería` | 284 | 2 | 67 |  |
| `Descargó el estado de flujo de  efectivo` | 98 | 0 | 67 |  |
| `Nuevo Stage en Hubspot: lead` | 97 | 0 | 2 | Funnel Hubspot |
| `Notificaciones - Permiso Aceptado` | 91 | 0 | 56 |  |
| `Nuevo Stage en Hubspot: customer` | 81 | 0 | 2 |  |
| `Subscription Billed` | 68 | 0 | 71 |  |
| `Mi Consultor` | 67 | 0 | 63 |  |
| `Recibió notificación` | 60 | 0 | 23 |  |
| `Modificó perfil` | 59 | 0 | 63 |  |
| `Agregó un depósito` | 53 | 0 | 48 |  |
| `Ir a Demo desde Mi Cuenta` | 40 | 0 | 37 |  |
| `Vencimientos - Suscripción Notificación` | 35 | 630 | 57 |  |
| `Calificado en Hubspot` | 29 | 104 | 2 |  |
| `Lead creado en Hubspot` | 25 | 24 | 4 |  |
| `Agregó centros de costo` | 25 | 0 | 48 |  |
| `Reporta en ARBA` | 17 | 0 | 36 |  |
| `Nuevo Stage en Hubspot: opportunity` | 15 | 0 | 2 |  |
| `Vencimientos - Exportar ICS` | 15 | 0 | 25 |  |
| `Vencimientos - Desuscripción Notificación` | 11 | 611 | 27 |  |
| `Crear Usuario` | 11 | 0 | 30 | Eventos Sueldos |
| `Vencimientos - Eliminar Custom` | 7 | 623 | 27 |  |
| `Contador Invitado a Programa` | 5 | 0 | 23 |  |
| `Vencimientos - Crear Custom` | 3 | 345 | 53 |  |
| `Socio Invitado` | 1 | 0 | 22 |  |
| `Boolfy - Interés en Funcionalidad Demo` | 0 | 19 | 0 |  |
| `Success ThankYouPage` | 0 | 8 | 0 |  |
| `Reenviar validación email` | 0 | 6 | 0 |  |
| `Guardó un nuevo usuario invitado de tipo POS` | 0 | 0 | 0 |  |
| `Invita usuario Pos` | 0 | 0 | 0 |  |
| `Negocio Ganado en Hubspot` | 0 | 0 | 0 |  |
| `Nuevo Stage en Hubspot: 1002818424` | 0 | 0 | 0 | Funnel Hubspot |
| `Quiero que me llamen` | 0 | 0 | 0 |  |
| `Se aceptó la delegación de factura electrónica` | 0 | 0 | 0 |  |
| `Socio Elegido` | 0 | 0 | 0 |  |
| `Vencimientos - Filtro Aplicado` | 0 | 0 | 0 |  |
| `Vende productos` | 0 | 0 | 0 |  |
| `Vende productos o servicios` | 0 | 0 | 0 |  |
| `Vende servicios` | 0 | 0 | 0 |  |
| `cargo novedad Masivo` | 0 | 0 | 0 |  |
| `completa bienvenida` | 0 | 0 | 0 |  |
| `record` | 0 | 0 | 0 |  |

**`Descargó el mayor` key properties:** `Tipo Plan Empresa`, `company_id`, `format`, `ad_id`, `adset_id`, `fbclid`, `first_fbclid`, `first_utm_campaign`
**`Realizó canje interno de caja` key properties:** `Tipo Plan Empresa`, `company_id`, `ad_id`, `adset_id`, `fbclid`, `first_fbclid`, `first_utm_campaign`, `first_utm_source`
**`Elige tipo de moneda` key properties:** `Tipo Plan Empresa`, `company_id`, `ad_id`, `adset_id`, `fbclid`, `first_fbclid`, `first_utm_campaign`, `first_utm_source`

---

## Custom Events (Computed)
*55 defined*

| ID | Display Name | Description | Query Vol | Tags |
|----|-------------|-------------|----------:|------|
| `$custom_event:2005946` | Eventos clave de todos los usuarios en Trial | Todos los evnetos claves de todo tipo de usuario realizado durante una empresa pendiente de pago | 13,065 | Eventos Clave |
| `$custom_event:1177927` | Registro |  | 3,459 |  |
| `$custom_event:1910312` | Top events en pago |  | 1,418 |  |
| `$custom_event:1432575` | Eventos clave de todos los usuarios | Incluye los eventos clave de todos los user persona de administración contabilidad y sueldos en todo | 829 | Eventos Clave, Eventos Críticos |
| `$custom_event:1432881` | Login App & Desktop |  | 352 |  |
| `$custom_event:1921604` | Click cambiar plan(todos los planes) |  | 116 |  |
| `$custom_event:1446223` | Eventos clave del usuario que lleva la administración |  | 76 | Eventos Clave |
| `$custom_event:1177604` | Generó documento |  | 70 |  |
| `$custom_event:2012950` | Visita en Website de Sueldos |  | 48 | Eventos Sueldos, Eventos Website |
| `$custom_event:1429100` | Eventos clave de usuarios que administra inventario |  | 38 | Eventos Clave |
| `$custom_event:1352359` | Eventos clave del usuario que lleva la contabilidad |  | 36 | Eventos Clave |
| `$custom_event:1446644` | Login en pago | Login en una empresa que no es administrada, que no es la demo y que tiene algún plan pago | 25 |  |
| `$custom_event:1926076` | Todos los eventos claves de sueldos |  | 24 |  |
| `$custom_event:2012956` | Cargó Legajo individual o masivo |  | 24 |  |
| `$custom_event:2011729` | Visita en sitio colppy.com |  | 20 | Eventos Website |
| `$custom_event:1446656` | Login en pendiente de pago |  | 8 |  |
| `$custom_event:1871040` | Agregó una empresa adicional |  | 5 |  |
| `$custom_event:1179525` | Generó Reporte |  | 2 |  |
| `$custom_event:1178540` | Subscription billed |  | 0 |  |
| `$custom_event:1179528` | Typ |  | 0 |  |
| `$custom_event:1352876` | Crea Nuevo Contacto |  | 0 |  |
| `$custom_event:1430665` | Generación de reporte para usuarios que llevan contabilidad e impuestos |  | 0 | Eventos Clave |
| `$custom_event:1430667` | Generación de reportes para usuarios que llevan la administración no contable |  | 0 |  |
| `$custom_event:1430960` | Generación de reporte para usuarios que llevan inventario |  | 0 |  |
| `$custom_event:1430961` | Eventos clave de usuarios que intentan configurar y pagar desktop |  | 0 | Eventos Clave |
| `$custom_event:1430969` | Eventos clave de usuarios que administran con app mobile |  | 0 | Eventos Clave, Eventos mobile |
| `$custom_event:1430972` | Eventos clave de usuarios que intentan configurar app |  | 0 | Eventos Clave |
| `$custom_event:1432576` | Eventos clave para todas las implementaciones |  | 0 | Eventos Clave |
| `$custom_event:1556153` | ingreso Empresa |  | 0 |  |
| `$custom_event:1556377` | Agregar Proveedor |  | 0 |  |
| `$custom_event:1556389` | Agregar Cliente |  | 0 |  |
| `$custom_event:1785440` | Login en Empresa Demo |  | 0 |  |
| `$custom_event:1791012` | Agrega proveedor desde importador |  | 0 |  |
| `$custom_event:1801296` | Todas las opciones de Vende productos o servicios y finaliza wizard |  | 0 |  |
| `$custom_event:1838404` | Generó comprobante de venta Multimoneda |  | 0 |  |
| `$custom_event:1855836` | Eventos Clave de usuarios que llevan la administración - Cobranzas y Pagos |  | 0 | Eventos Clave |
| `$custom_event:1856144` | Importación de Facturas Compra y Venta |  | 0 |  |
| `$custom_event:1863352` | Seleccionó opción de pago Visa Débito | Selecciona el checkbox de Visa Débito como medio de pago en la pantalla de Selección de medio de pag | 0 | Auto Tag |
| `$custom_event:1863356` | Seleccionó opción de pago Visa Crédito | En el momento de seleccionar el medio de pago registra si selecciona Visa Crédito | 0 | Auto Tag |
| `$custom_event:1863364` | Click en Solapa Mercado Pago |  | 0 |  |
| `$custom_event:1863368` | Click en botón empty state Mercado Pago |  | 0 |  |
| `$custom_event:1863372` | Click en Buscar en ARCA el CUIT |  | 0 |  |
| `$custom_event:1863376` | Selecciona Dropdown Lista de Precios de Factura | Evento para cuando el cliente abre una factura y hace click en el desplegable para elegir de una lis | 0 |  |
| `$custom_event:1863388` | Click en Retenciones IIBB Pago |  | 0 |  |
| `$custom_event:1863392` | Guardó Retenciones IIBB Compra |  | 0 |  |
| `$custom_event:1863400` | Guardó Retenciones IIBB Venta |  | 0 |  |
| `$custom_event:1863740` | Click en Otras Retenciones Cobro |  | 0 |  |
| `$custom_event:1863744` | Guardó Otras Retenciones Cobros |  | 0 |  |
| `$custom_event:1868432` | Modifica campo Clientes Ventas IIBB |  | 0 |  |
| `$custom_event:1871044` | Agregó una empresa administrada |  | 0 |  |
| `$custom_event:1905024` | Abrió módulo de clientes o proveedores |  | 0 |  |
| `$custom_event:1905752` | Activó |  | 0 |  |
| `$custom_event:1909804` | Registro Validado |  | 0 |  |
| `$custom_event:1909816` | Registro Pendiente Validar |  | 0 |  |
| `$custom_event:1910308` | Top events |  | 0 |  |

---

## Custom Events — Full Compositions

*Resolved via Mixpanel API (`/api/app/projects/{id}/custom_events/{id}`) on 2026-03-10.*
*Custom events are OR unions of their alternatives. Filters narrow specific alternatives.*

### `$custom_event:2005946` — Eventos clave de todos los usuarios en Trial

**Top-level filter:** `Tipo Plan Empresa = "pendiente_pago"`
**Contains:** `$custom_event:1432575` (see below)

This is the primary **trial activation goal** event. It fires when any "key event" happens in a trial (pendiente_pago) company.

---

### `$custom_event:1432575` — Eventos clave de todos los usuarios

**OR union of 5 persona-based custom events:**

| # | Custom Event | Persona |
|---|-------------|---------|
| 1 | `$custom_event:1429100` | Inventario |
| 2 | `$custom_event:1446223` | Administración |
| 3 | `$custom_event:1352359` | Contabilidad |
| 4 | `$custom_event:1430969` | Mobile |
| 5 | `$custom_event:1926076` | Sueldos |

---

### `$custom_event:1446223` — Eventos clave del usuario que lleva la administración

| # | Event | Filter |
|---|-------|--------|
| 1 | `Generó comprobante de venta` | — |
| 2 | `Generó comprobante de compra` | — |
| 3 | `$custom_event:1855836` (Cobranzas y Pagos) | — |
| 4 | `Finalizó importación` | `importer_type` = "Factura de compra - mis comprobantes", "Facturas de compra", "Facturas de venta" |
| 5 | `Agregó medio de cobro` | `Document_type` = "OREC", "REC" |
| 6 | `Agregó medio de pago` | `Document_type` = "OPAG", "PAG" |

---

### `$custom_event:1855836` — Eventos Clave de usuarios que llevan la administración - Cobranzas y Pagos

| # | Event | Filter |
|---|-------|--------|
| 1 | `Genera nuevo cobro` | — |
| 2 | `Genera nuevo pago` | — |
| 3 | `Generó recibo de cobro` | — |
| 4 | `Generó orden de pago` | — |

---

### `$custom_event:1352359` — Eventos clave del usuario que lleva la contabilidad

| # | Event | Filter |
|---|-------|--------|
| 1 | `Generó asiento contable` | — |
| 2 | `$custom_event:1430665` (Reportes contables) | — |
| 3 | `Finalizó importación` | `importer_type` = "Asientos" |

---

### `$custom_event:1430665` — Generación de reporte para usuarios que llevan contabilidad e impuestos

| # | Event |
|---|-------|
| 1 | `Descargó el mayor` |
| 2 | `Descargó el balance` |
| 3 | `Descargó el diario general` |
| 4 | `Descargó el libro iva compras` |
| 5 | `Descargó el libro iva digital` |
| 6 | `Descargó el libro iva ventas` |
| 7 | `Descargó el retenciones y percepciones` |
| 8 | `Descargó el régimen de información de compras y ventas` |
| 9 | `Descargó la posición impositiva mensual` |
| 10 | `Descargó el estado de resultados` |
| 11 | `Descargó el listado de cobranzas` |
| 12 | `Descargó el listado de comprobantes de venta` |
| 13 | `Descargó el listado de comprobantes de venta borrador` |
| 14 | `Descargó el listado de pagos` |
| 15 | `Descargó el listado de comprobantes de compra` |

---

### `$custom_event:1429100` — Eventos clave de usuarios que administra inventario

| # | Event | Filter |
|---|-------|--------|
| 1 | `Generó un ajuste de inventario` | — |
| 2 | `Agregó un ítem` | — |
| 3 | `Finalizó importación` | `importer_type` = "Items" |

---

### `$custom_event:1430969` — Eventos clave de usuarios que administran con app mobile

| # | Event |
|---|-------|
| 1 | `app generó comprobante de venta` |
| 2 | `app generó recibo de cobro` |

---

### `$custom_event:1926076` — Todos los eventos claves de sueldos

| # | Event |
|---|-------|
| 1 | `Liquidar sueldo` |
| 2 | `Presentar liquidacion` |

---

### Flat List: All Raw Events Inside "Eventos clave en Trial" (2005946)

For quick reference — every raw event that triggers the trial activation goal:

**Administración:** `Generó comprobante de venta`, `Generó comprobante de compra`, `Genera nuevo cobro`, `Genera nuevo pago`, `Generó recibo de cobro`, `Generó orden de pago`, `Finalizó importación` (compra/venta), `Agregó medio de cobro` (OREC/REC), `Agregó medio de pago` (OPAG/PAG)

**Contabilidad:** `Generó asiento contable`, `Finalizó importación` (Asientos), + 15 report downloads (mayor, balance, diario general, libro IVA compras/ventas/digital, retenciones, régimen info, posición impositiva, estado resultados, listado cobranzas/pagos/comprobantes venta/compra/borrador)

**Inventario:** `Generó un ajuste de inventario`, `Agregó un ítem`, `Finalizó importación` (Items)

**Mobile:** `app generó comprobante de venta`, `app generó recibo de cobro`

**Sueldos:** `Liquidar sueldo`, `Presentar liquidacion`

---

*Generated from Lexicon CSV export on 2026-03-10*