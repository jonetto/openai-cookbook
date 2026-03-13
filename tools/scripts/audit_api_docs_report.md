# Colppy API Documentation Audit Report

Generated: 2026-03-12

## Coverage Summary

| | Backend | Docusaurus | OpenAPI |
|--|---------|------------|---------|
| Provisions | **33** | 14 (42%) | 6 (18%) |
| Operations | **498** | 69 (13%) | 24 (4%) |

## Undocumented Provisions

Provisions that exist in backend but have NO Docusaurus documentation.

### Should Document (user-facing)

| Provision | Operations | Key Operations |
|-----------|-----------|----------------|
| **Afip** | 1 | `N/A` |
| **Archivo** | 3 | `alta_archivo`, `borrar_archivo`, `leer_archivo` |
| **CondicionIVA** | 5 | `N/A` |
| **CondicionPago** | 1 | `N/A` |
| **Location** | 3 | `N/A` |
| **PriceList** | 8 | `alta_pricelist`, `editar_pricelist`, `leer_pricelist`, `listar_items_pricelist`, `listar_pricelist` |
| **Retencion** | 4 | `N/A` |
| **Tax** | 10 | `alta_setup_evento`, `editar_evento`, `editar_setup`, `leer_comportamiento`, `listar_eventos` |
| **TipoOperacionCompra** | 1 | `listar_tipo_de_operaciones_compra` |
| **TipoOperacionVenta** | 1 | `listar_tipo_de_operaciones` |

### Internal/Skip

`BillStub`, `Desarrollador`, `Help`, `Importer`, `Integracion`, `Notificaciones`, `Paybook`, `Pos`, `Receipt`, `Referido`, `Socio`, `Tercero`

---

## Per-Provision Analysis


### Afip

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `health_check` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

### Archivo

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `alta_archivo` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `borrar_archivo` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_archivo` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

### Cliente

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `AR_leer_fondos_pagos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_cliente` | ✅ | ✅ | ✅ |  |
| `alta_cliente_importacion` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_cobro` | ✅ | ❌ | ✅ | *(entire operation undocumented)* |
| `alta_mailfactura` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_meliOrdenes` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `ar_listar_totalesiva` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `borrar_items_anulados_ar` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `borrar_meliOrdenes` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `buscar_cliente` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_cliente` | ✅ | ✅ | ✅ |  |
| `editar_cobro` | ✅ | ❌ | ✅ | *(entire operation undocumented)* |
| `editar_retsufridas` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `generar_pdf_recibo_cliente` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `importacion_masiva_clientes` | ✅ | ✅ | ❌ |  |
| `info_importacion_masiva_clientes` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_cliente` | ✅ | ✅ | ✅ |  |
| `leer_cliente_meli` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_cliente_por_cuit` | ✅ | ✅ | ❌ |  |
| `leer_cliente_portal` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_detalle_cliente` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_items_ordenes` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_mailfactura` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_template_mail` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_ultima_sincro_meli` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `lista_decodificadora` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_cliente` | ✅ | ✅ | ✅ |  |
| `listar_cliente_mp` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_cliente_totales` | ✅ | ✅ | ❌ |  |
| `listar_jurisdiccionesRet` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_municipiosIcaEmpresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_ordenes_meli` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_resoluciones` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_retsufridas` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_retsufridasICA` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_retsufridasOtrasSetUp` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_retsufridasOtrasSetUpCO` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_retsufridasSetUp` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_retsufridasotras` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_retsufridasotrasco` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

### CondicionIVA

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `getCondicionIVAporId` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `getCondicionesIVA` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `getIvaPrincipal` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `getPorcentajesIVA` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `getTipoActividad` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

### CondicionPago

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `getCondicionesPago` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

### Contabilidad

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `actualizar_conciliados` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_asiento` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_asiento_conciliacion` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_formato_concepto` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_reporte_diario_general` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_reporte_mm` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `borrar_asiento` | ✅ | ✅ | ❌ |  |
| `borrar_columna_cuenta` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `borrar_concepto_columna` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `borrar_formato_concepto` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `borrar_url_iva_digital` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `buscar_plancuenta` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `descargar_reporte_diario_general` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_asiento` | ✅ | ✅ | ❌ | `isNIIF` |
| `editar_fechaiva` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_formato_concepto` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `enviar_plan_cuentas` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `enviar_reporte_diario_general` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `enviar_reporte_medios_magneticos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `export_iva_digital` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `export_seguimiento_cheques` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `importar_asiento` | ✅ | ✅ | ❌ |  |
| `leer_Plan_De_Cuentas_Empresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_arbol_contabilidad` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_asiento` | ✅ | ✅ | ❌ |  |
| `leer_fechaiva` | ✅ | ✅ | ❌ |  |
| `leer_plan_de_cuenta_manual_enviado` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_plan_de_cuentas_empresa_y_tipo_cuenta` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_saldoCuenta` | ✅ | ✅ | ❌ |  |
| `leer_totales_cuenta` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_Asiento_Empresa_Nueva` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_asientosmanuales` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_columnas_por_formato` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_concept_empresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_concepto_formatos_empresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_conceptos_por_formato` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_cuentasdiario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_format_empresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_formatos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_formatos_empresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_itemsasiento` | ✅ | ✅ | ❌ | `add` |
| `listar_movimientosdiario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `obtener_url_iva_digital` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `test_balance` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `tiene_movimientos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `validar_cuenta` | ✅ | ✅ | ❌ |  |

### Empresa

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `aceptar_delegacion` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `actualizar_MailPortalCliente` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `actualizar_actividades_desde_arca` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `actualizar_mediopago_mp` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `actualizar_typ` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_ccosto` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_empresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_empresa_demo` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_empresa_meli` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_empresa_nueva_demo` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_empresa_socio` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_empresa_wizard` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_mediospagos_contabilidad` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_monedas_empresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `borrar_ccosto` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `buscar_empresa_flag` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `buscar_factura_cliente_portal` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `consultar_delegacion` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `copiar_cliente_semilla` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `copiar_proveedor_semilla` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `crear_datos_facturacion` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `crear_plan_cuentas` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_ccosto` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_datosimpositivos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_empresa` | ✅ | ✅ | ❌ | `isCron`, `usaWizard` |
| `editar_empresa_datos_clienteprov` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_empresa_encabezado_meli` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_empresa_info` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_empresa_integracion_meli` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_nombre_empresa_y_plan` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_plan_empresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_socio` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `eliminar_lista_empresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `eliminar_talonario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `eliminar_transacciones` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `empresa_buscar_por_nombre` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `enviar_datos_atividad_usuario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `formato_impresion` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `generar_delegacion` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `get_planes` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_MailPortalCliente` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_ar_tipo_item` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_caja_bancos_grafico` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_ccosto` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_ccosto_diario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_configuracion_mercado_pago` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_decodificadoraPorTabla` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_empresa` | ✅ | ✅ | ❌ | `autorizar` |
| `leer_empresa_mp` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_mediopago_mp` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_mediospagos_contabilidad` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_numero_recibo` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_paso_wizard_si_unica_empresa_usuario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_plan` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_plan_por_tipo` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_porcentajes_iva` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_provinciasdecodificadora` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_retefuente_cuenta` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_retefuente_cuenta_venta` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_talonario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_talonario_co` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_talonario_mp` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_actividades_empresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_alicuotas_iva_mp` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_ccostos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_cuentas_cobro_mp` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_cuentas_ventas_mp` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_descripcion_id_ccostos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_empresa` | ✅ | ✅ | ❌ |  |
| `listar_empresasportal` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_monedas_por_empresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_municipiosICA` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_muniretrealizadas_co` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_muniretsufridas_co` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_nombresccostos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_resoluciones` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_retencionCREE` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_setuppercsufridas` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_setupretemitidas` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_setupretsufridas` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_talonario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_talonarios_mp` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `notificar_delegacion` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `obtener_cantidad_comprobantes` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `obtener_medio_tipo_pago` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `primer_pago` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `proximo_numero_factura` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `proximo_numero_remito` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `validar_cantidad_comprobantes` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `validar_cantidad_comprobantes_mp` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `validar_cantidad_empresas_administradas` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `validar_chat` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `validar_empresa_desactivada` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `validar_iva` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `validar_plan_contador` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `validar_upsell_empresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

⚠️ **In docs but NOT in backend:** `alta_empresa_basica`, `listar_talonarios`

### FacturaCompra

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `alta_factura_compra_importada` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_facturacompra` | ✅ | ✅ | ✅ |  |
| `editar_facturacompra` | ✅ | ✅ | ❌ | `fechaPago`, `rate` |
| `importar_facturas` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_detallefacturacompra` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_factura_datosadicionales` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_facturacompra` | ✅ | ✅ | ✅ |  |
| `leer_fondosPagoFactura` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_pagos_factura` | ✅ | ✅ | ❌ |  |
| `listar_comprobantes_compra_detalle` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_facturasTotales` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_facturascompra` | ✅ | ✅ | ✅ | `group`, `order` |
| `tipificar_importacion_facturas` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `validar_estructura_miscomprobantes` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

### FacturaVenta

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `alta_FE_incompleta` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_comprobante_electronico` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_facturaventa` | ✅ | ✅ | ✅ | `NCV`, `NVE`, `extra_data`, `idTalonario`, `letra`, `not_api`, `orderId`, `pendingInvoice` |
| `alta_facturaventa_importada` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_facturaventarecurrente` | ✅ | ✅ | ❌ | `idFactura` |
| `alta_lista_comprobantes_electronicos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_siguientefacturaventarecurrente` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `crear_impresion_facturas` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_Factura_FEIncompleta` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_facturaventa` | ✅ | ✅ | ❌ | `ItemsCobro`, `NCV`, `NVE`, `codigoActividad`, `debitoCredito`, `fechaPago`, `idEstadoAnterior`, `idOrden` +8 more |
| `enviar_recordatoriovencimiento` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `es_electronica` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `finalizar_facturaventarecurrente` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `importar_facturas` | ✅ | ✅ | ❌ | `IIBBLocal`, `IVA105`, `IVA21`, `IVA27`, `ItemsCobro`, `esresumen`, `fechaFactura`, `fechaPago` +25 more |
| `imprimir_facturas` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_cobros_factura` | ✅ | ✅ | ✅ |  |
| `leer_datos_cliente_empresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_detalle_cobro` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_factura_datosadicionales` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_factura_portal` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_facturas_a_cobrar` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_facturaventa` | ✅ | ✅ | ✅ | `monotributo`, `portal` |
| `leer_fondosPagoFactura` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_link_QR` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_saldoFacturasImpagas` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_ultimo_comprobante_talonario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_comprobantes_a_asociar` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_comprobantes_venta_detalle` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_facturasFEIncompletas` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_facturasTotales` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_facturasventa` | ✅ | ✅ | ✅ | `group` |
| `listar_facturasventaportal` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_facturaventarecurrente` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_totalesiva_ar` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `pagar_facturasportal` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `paginado_facturas_a_cobrar` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `rollback_Factura_FEIncompleta` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `tipificar_importacion_facturas` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `validar_comprobantes_previos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

⚠️ **In docs but NOT in backend:** `Cobros`, `Monedas`

### Inventario

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `alta_ajusteinventario` | ✅ | ✅ | ❌ |  |
| `alta_deposito` | ✅ | ✅ | ❌ |  |
| `alta_disponibilidadinicial` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_iteminventario` | ✅ | ✅ | ❌ | `isCreate` |
| `alta_remito` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_setupinventario` | ✅ | ✅ | ❌ |  |
| `borrar_itemporcodigo` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `borrar_items` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_ajusteinventario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_deposito` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_iteminventario` | ✅ | ✅ | ❌ | `comentarioFactura`, `costoCalculado`, `detalle`, `esKit`, `isEdit`, `items`, `unidadMedida` |
| `editar_precioItems` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_remito` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_remitosfactura` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_setupinventario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `eliminar_ajusteinventario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `eliminar_remito` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `importar_itemsinventario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `importar_preciosinventario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_deposito` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_itemPorCodigo` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_itemPorDesc` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_iteminventario` | ✅ | ✅ | ❌ | `leerYDevolverIds` |
| `leer_itemtotales` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_itemtotales_dep` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_remito` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_remitoPorFactura` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_setupinventario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_ajusteinventario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_comboclientes` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_cuentasAsentables` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_depositos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_dispDeposito` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_itemsinventario` | ✅ | ✅ | ❌ | `date_from_created`, `date_to_created` |
| `listar_itemsremito` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_itemsremitofactura` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_movimientos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_remitos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_remitosPorFactura` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_remitosSinFactura` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `obtener_ajusteinventario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `validar_deposito` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

### Location

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `getCities` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `getCountries` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `getRegions` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

### Moneda

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `actualizar_tiposcambio` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_moneda` | ✅ | ✅ | ❌ |  |
| `listar_monedas` | ✅ | ✅ | ❌ |  |

### Pago

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `alta_pago` | ✅ | ✅ | ✅ |  |
| `data_pago_op` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `data_ultimo_pago` | ✅ | ❌ | ✅ | *(entire operation undocumented)* |
| `imprimir_enviar_pagos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_pago` | ✅ | ❌ | ✅ | *(entire operation undocumented)* |

⚠️ **In docs but NOT in backend:** `detalle_pago`, `ultimo_pago`

### PriceList

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `actualizar_items_pricelist` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_pricelist` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `asociar_items_pricelist` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `duplicar_pricelist` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_pricelist` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_pricelist` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_items_pricelist` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_pricelist` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

### Proveedor

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `alta_proveedor` | ✅ | ✅ | ✅ |  |
| `alta_proveedor_importacion` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `ap_listar_totalesiva` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `borrar_items_anulados_ap` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `buscar_numero_op` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `buscar_proveedor` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `detalle_proveedor` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_proveedor` | ✅ | ✅ | ✅ | `FechaAlta`, `cityId`, `countryId`, `isNit`, `primerApellido`, `primerNombre`, `regionId`, `segundoApellido` +1 more |
| `facturas_impagas_proveedor` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `generar_pdf_pagos_proveedores` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `getCondicionesPago` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `importacion_masiva_proveedores` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `info_importacion_masiva_proveedores` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_proveedor` | ✅ | ✅ | ✅ | `idElemento` |
| `leer_proveedor_por_cuit` | ✅ | ✅ | ❌ |  |
| `leer_template_mail` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_comboproveedores` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_jurisdiccionesPerc` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_jurisdiccionesRetEm` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_municipiosIcaEmpresaProv` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_percsufridas` | ✅ | ✅ | ❌ | `add` |
| `listar_percsufridasSetUp` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_proveedor` | ✅ | ✅ | ✅ |  |
| `listar_proveedor_totales` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_retemitidas` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_retemitidasSetUp` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_retrealizadasICA` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

### Retencion

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `consultaAlicuotaAgip` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `consultaPadronIIBB` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `getRetPorRentaPorId` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `getRetencionPorRenta` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

### Tax

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `activar_setup_evento` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_setup_evento` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `cron_envio_vencimientos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_evento` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_setup` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `exportar_listado_mensual` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_comportamiento` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_eventos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_proximo_evento` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_setup` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

### Tesoreria

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `actualizar_tipo_conciliacion` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_cuenta` | ✅ | ✅ | ❌ |  |
| `alta_cuenta_banco` | ✅ | ✅ | ❌ |  |
| `alta_extracto` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_otrocobro` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `borrar_conciliaciones_cuenta` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `borrar_extracto` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `borrar_movimientos_extracto` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `buscar_proxima_pagina_conciliados` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `conciliar_movimientos_cuenta` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `conciliar_movimientos_extractos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `desconciliar_cuenta_extractos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `desconciliar_movimientos_extractos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_extracto` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_otrocobro` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `importar_extracto` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_asientoingresoscobro` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_balances_banco` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_cheques_diferidos` | ✅ | ✅ | ❌ |  |
| `leer_cheques_valores_cartera` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_extracto` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_fondoscobro` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_origen_fondos2` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_otrocobro` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_tipo_conciliacion` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_totales_extractos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_ultimos_movimientos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listado_banco` | ✅ | ✅ | ❌ |  |
| `listar_extractos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_movimientos_extracto` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_movimientos_extractos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_movimientos_extractos_conciliados` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_movimientos_totales` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `paginado_movimientos_extractos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `paybook_actualizar_condiciones` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `paybook_autenticar` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `paybook_desconectar` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `paybook_sincronizar_movimientos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `paybook_validar_cuenta` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `paybook_ver_credenciales` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `paybook_ver_cuentas` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `paybook_ver_transacciones` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `paybook_verificar_condiciones` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `verificar_cuenta_banco` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `verificar_extractos_conciliados` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `vincular_cuenta_con_paybook` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

⚠️ **In docs but NOT in backend:** `alta_otro_cobro`, `leer_otro_cobro`

### TipoOperacionCompra

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `listar_tipo_de_operaciones_compra` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

### TipoOperacionVenta

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `listar_tipo_de_operaciones` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

### Usuario

| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |
|-----------|:-------:|:----:|:-------:|----------------------------------------|
| `actualizar_paso_wizard` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `agregar_usuario_meli` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_paso_wizard` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_recomendado` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_usuario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_usuario_meli` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_usuario_partner` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `alta_usuario_portal` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `cambiar_password` | ✅ | ✅ | ❌ | `isWizard`, `password`, `passwordAuth`, `passwordExpirada`, `passwordFusionAuth` |
| `cerrar_sesion` | ✅ | ✅ | ✅ |  |
| `confirmar_email` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `dame_el_id_de_mi_primera_empresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `editar_usuario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `envio_Mail_Cambio_Contrasena` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `iniciar_colppy` | ✅ | ✅ | ✅ | `chequearPassword`, `fusionAuth`, `idOp`, `isMobile`, `password`, `passwordAuth` |
| `iniciar_sesion` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `invitar_usuario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `ir_Empresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_datos_atividad_usuario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_nombreusuario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_paso_wizard` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_usuario` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_usuario_datos` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_usuario_por_seller_id` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_usuario_portal` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `leer_usuario_usa_wizard` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_perfil` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `listar_usuarios_empresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `pre_registro` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `recuperar_Clave` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `refresh_fusion_token` | ✅ | ❌ | ✅ | *(entire operation undocumented)* |
| `refresh_token` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `register_invitado_contador` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `register_user` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `registrar_email_contador_robado` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `setear_empresa_demo_como_ultima_empresa` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `setear_nueva_password` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `validar_sesion` | ✅ | ✅ | ✅ |  |
| `validar_sesion_cookies` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |
| `validar_usuario_mail` | ✅ | ❌ | ❌ | *(entire operation undocumented)* |

⚠️ **In docs but NOT in backend:** `enviar_email`

---

## OpenAPI Coverage Gap

Operations documented in Docusaurus but missing from OpenAPI YAML:

| Provision | Operation | In Docs | In OpenAPI |
|-----------|-----------|:-------:|:----------:|
| Cliente | `importacion_masiva_clientes` | ✅ | ❌ |
| Cliente | `leer_cliente_por_cuit` | ✅ | ❌ |
| Cliente | `listar_cliente_totales` | ✅ | ❌ |
| Cobro | `alta_cobro` | ✅ | ❌ |
| Cobro | `editar_cobro` | ✅ | ❌ |
| Cobro | `leer_cobros_factura` | ✅ | ❌ |
| Condiciones | `CondicionIVA` | ✅ | ❌ |
| Condiciones | `CondicionPago` | ✅ | ❌ |
| Contabilidad | `borrar_asiento` | ✅ | ❌ |
| Contabilidad | `editar_asiento` | ✅ | ❌ |
| Contabilidad | `importar_asiento` | ✅ | ❌ |
| Contabilidad | `leer_asiento` | ✅ | ❌ |
| Contabilidad | `leer_fechaiva` | ✅ | ❌ |
| Contabilidad | `leer_saldoCuenta` | ✅ | ❌ |
| Contabilidad | `listar_itemsasiento` | ✅ | ❌ |
| Contabilidad | `validar_cuenta` | ✅ | ❌ |
| Empresa | `alta_empresa_basica` | ✅ | ❌ |
| Empresa | `editar_empresa` | ✅ | ❌ |
| Empresa | `leer_empresa` | ✅ | ❌ |
| Empresa | `listar_empresa` | ✅ | ❌ |
| Empresa | `listar_talonarios` | ✅ | ❌ |
| Factura | `Restricciones` | ✅ | ❌ |
| FacturaCompra | `editar_facturacompra` | ✅ | ❌ |
| FacturaCompra | `leer_pagos_factura` | ✅ | ❌ |
| FacturaVenta | `Cobros` | ✅ | ❌ |
| FacturaVenta | `Monedas` | ✅ | ❌ |
| FacturaVenta | `alta_facturaventarecurrente` | ✅ | ❌ |
| FacturaVenta | `editar_facturaventa` | ✅ | ❌ |
| FacturaVenta | `importar_facturas` | ✅ | ❌ |
| Inventario | `alta_ajusteinventario` | ✅ | ❌ |
| Inventario | `alta_deposito` | ✅ | ❌ |
| Inventario | `alta_iteminventario` | ✅ | ❌ |
| Inventario | `alta_setupinventario` | ✅ | ❌ |
| Inventario | `editar_iteminventario` | ✅ | ❌ |
| Inventario | `leer_iteminventario` | ✅ | ❌ |
| Inventario | `listar_itemsinventario` | ✅ | ❌ |
| Moneda | `leer_moneda` | ✅ | ❌ |
| Moneda | `listar_monedas` | ✅ | ❌ |
| Pago | `detalle_pago` | ✅ | ❌ |
| Pago | `ultimo_pago` | ✅ | ❌ |
| Proveedor | `leer_proveedor_por_cuit` | ✅ | ❌ |
| Proveedor | `listar_percsufridas` | ✅ | ❌ |
| Tesoreria | `alta_cuenta` | ✅ | ❌ |
| Tesoreria | `alta_cuenta_banco` | ✅ | ❌ |
| Tesoreria | `alta_otro_cobro` | ✅ | ❌ |
| Tesoreria | `leer_cheques_diferidos` | ✅ | ❌ |
| Tesoreria | `leer_otro_cobro` | ✅ | ❌ |
| Tesoreria | `listado_banco` | ✅ | ❌ |
| Usuario | `cambiar_password` | ✅ | ❌ |
| Usuario | `enviar_email` | ✅ | ❌ |

---

## Recommended Actions

### High Priority (user-facing, undocumented operations)

- **Cliente**: `alta_cliente_importacion`, `alta_cobro`, `alta_mailfactura`, `alta_meliOrdenes`, `borrar_items_anulados_ar`, `borrar_meliOrdenes`, `editar_cobro`, `editar_retsufridas`, `leer_cliente_meli`, `leer_cliente_portal`, `leer_detalle_cliente`, `leer_items_ordenes`, `leer_mailfactura`, `leer_template_mail`, `leer_ultima_sincro_meli`, `listar_cliente_mp`, `listar_jurisdiccionesRet`, `listar_municipiosIcaEmpresa`, `listar_ordenes_meli`, `listar_resoluciones`, `listar_retsufridas`, `listar_retsufridasICA`, `listar_retsufridasOtrasSetUp`, `listar_retsufridasOtrasSetUpCO`, `listar_retsufridasSetUp`, `listar_retsufridasotras`, `listar_retsufridasotrasco`
- **Contabilidad**: `alta_asiento`, `alta_asiento_conciliacion`, `alta_formato_concepto`, `alta_reporte_diario_general`, `alta_reporte_mm`, `borrar_columna_cuenta`, `borrar_concepto_columna`, `borrar_formato_concepto`, `borrar_url_iva_digital`, `editar_fechaiva`, `editar_formato_concepto`, `leer_Plan_De_Cuentas_Empresa`, `leer_arbol_contabilidad`, `leer_plan_de_cuenta_manual_enviado`, `leer_plan_de_cuentas_empresa_y_tipo_cuenta`, `leer_totales_cuenta`, `listar_Asiento_Empresa_Nueva`, `listar_asientosmanuales`, `listar_columnas_por_formato`, `listar_concept_empresa`, `listar_concepto_formatos_empresa`, `listar_conceptos_por_formato`, `listar_cuentasdiario`, `listar_format_empresa`, `listar_formatos`, `listar_formatos_empresa`, `listar_movimientosdiario`
- **Empresa**: `alta_ccosto`, `alta_empresa`, `alta_empresa_demo`, `alta_empresa_meli`, `alta_empresa_nueva_demo`, `alta_empresa_socio`, `alta_empresa_wizard`, `alta_mediospagos_contabilidad`, `alta_monedas_empresa`, `borrar_ccosto`, `editar_ccosto`, `editar_datosimpositivos`, `editar_empresa_datos_clienteprov`, `editar_empresa_encabezado_meli`, `editar_empresa_info`, `editar_empresa_integracion_meli`, `editar_nombre_empresa_y_plan`, `editar_plan_empresa`, `editar_socio`, `leer_MailPortalCliente`, `leer_ar_tipo_item`, `leer_caja_bancos_grafico`, `leer_ccosto`, `leer_ccosto_diario`, `leer_configuracion_mercado_pago`, `leer_decodificadoraPorTabla`, `leer_empresa_mp`, `leer_mediopago_mp`, `leer_mediospagos_contabilidad`, `leer_numero_recibo`, `leer_paso_wizard_si_unica_empresa_usuario`, `leer_plan`, `leer_plan_por_tipo`, `leer_porcentajes_iva`, `leer_provinciasdecodificadora`, `leer_retefuente_cuenta`, `leer_retefuente_cuenta_venta`, `leer_talonario`, `leer_talonario_co`, `leer_talonario_mp`, `listar_actividades_empresa`, `listar_alicuotas_iva_mp`, `listar_ccostos`, `listar_cuentas_cobro_mp`, `listar_cuentas_ventas_mp`, `listar_descripcion_id_ccostos`, `listar_empresasportal`, `listar_monedas_por_empresa`, `listar_municipiosICA`, `listar_muniretrealizadas_co`, `listar_muniretsufridas_co`, `listar_nombresccostos`, `listar_resoluciones`, `listar_retencionCREE`, `listar_setuppercsufridas`, `listar_setupretemitidas`, `listar_setupretsufridas`, `listar_talonario`, `listar_talonarios_mp`
- **FacturaCompra**: `alta_factura_compra_importada`, `leer_detallefacturacompra`, `leer_factura_datosadicionales`, `leer_fondosPagoFactura`, `listar_comprobantes_compra_detalle`, `listar_facturasTotales`
- **FacturaVenta**: `alta_FE_incompleta`, `alta_comprobante_electronico`, `alta_facturaventa_importada`, `alta_lista_comprobantes_electronicos`, `alta_siguientefacturaventarecurrente`, `editar_Factura_FEIncompleta`, `leer_datos_cliente_empresa`, `leer_detalle_cobro`, `leer_factura_datosadicionales`, `leer_factura_portal`, `leer_facturas_a_cobrar`, `leer_fondosPagoFactura`, `leer_link_QR`, `leer_saldoFacturasImpagas`, `leer_ultimo_comprobante_talonario`, `listar_comprobantes_a_asociar`, `listar_comprobantes_venta_detalle`, `listar_facturasFEIncompletas`, `listar_facturasTotales`, `listar_facturasventaportal`, `listar_facturaventarecurrente`, `listar_totalesiva_ar`
- **Inventario**: `alta_disponibilidadinicial`, `alta_remito`, `borrar_itemporcodigo`, `borrar_items`, `editar_ajusteinventario`, `editar_deposito`, `editar_precioItems`, `editar_remito`, `editar_remitosfactura`, `editar_setupinventario`, `leer_deposito`, `leer_itemPorCodigo`, `leer_itemPorDesc`, `leer_itemtotales`, `leer_itemtotales_dep`, `leer_remito`, `leer_remitoPorFactura`, `leer_setupinventario`, `listar_ajusteinventario`, `listar_comboclientes`, `listar_cuentasAsentables`, `listar_depositos`, `listar_dispDeposito`, `listar_itemsremito`, `listar_itemsremitofactura`, `listar_movimientos`, `listar_remitos`, `listar_remitosPorFactura`, `listar_remitosSinFactura`
- **Pago**: `leer_pago`
- **Proveedor**: `alta_proveedor_importacion`, `borrar_items_anulados_ap`, `leer_template_mail`, `listar_comboproveedores`, `listar_jurisdiccionesPerc`, `listar_jurisdiccionesRetEm`, `listar_municipiosIcaEmpresaProv`, `listar_percsufridasSetUp`, `listar_proveedor_totales`, `listar_retemitidas`, `listar_retemitidasSetUp`, `listar_retrealizadasICA`
- **Tesoreria**: `alta_extracto`, `alta_otrocobro`, `borrar_conciliaciones_cuenta`, `borrar_extracto`, `borrar_movimientos_extracto`, `editar_extracto`, `editar_otrocobro`, `leer_asientoingresoscobro`, `leer_balances_banco`, `leer_cheques_valores_cartera`, `leer_extracto`, `leer_fondoscobro`, `leer_origen_fondos2`, `leer_otrocobro`, `leer_tipo_conciliacion`, `leer_totales_extractos`, `leer_ultimos_movimientos`, `listar_extractos`, `listar_movimientos_extracto`, `listar_movimientos_extractos`, `listar_movimientos_extractos_conciliados`, `listar_movimientos_totales`
- **Usuario**: `alta_paso_wizard`, `alta_recomendado`, `alta_usuario`, `alta_usuario_meli`, `alta_usuario_partner`, `alta_usuario_portal`, `editar_usuario`, `leer_datos_atividad_usuario`, `leer_nombreusuario`, `leer_paso_wizard`, `leer_usuario`, `leer_usuario_datos`, `leer_usuario_por_seller_id`, `leer_usuario_portal`, `leer_usuario_usa_wizard`, `listar_perfil`, `listar_usuarios_empresa`

### Medium Priority (OpenAPI sync needed)

Sync Docusaurus-documented operations into the OpenAPI YAML spec for AI/MCP consumption.

**50 operations** documented in Markdown but missing from OpenAPI.