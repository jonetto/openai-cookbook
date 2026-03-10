# Rediseño del MBR: De ceremonia de reporting a sesión de trabajo

**Fecha**: 2026-03-08
**Estado**: Aprobado
**Primera implementación**: MBR de Febrero 2026 (17 de marzo de 2026)

## Problema

El formato actual del MBR es un deck de 34 slides que pertenece al equipo regional de Finanzas. La dinámica es unidireccional: Finanzas presenta datos, Finanzas hace preguntas (slide de "Preguntas"), y los líderes de área defienden/explican. No hay espacio para que los líderes de área planteen sus propios temas, propongan soluciones o pidan ayuda cross-funcional.

Problemas clave:

- **Sin ownership**: Los líderes de área consumen el deck, no lo construyen
- **Sin tiempo de discusión**: 34 slides de datos no dejan lugar para conversación real
- **Postura reactiva**: Los líderes responden a preguntas de Finanzas en vez de apropiarse proactivamente de su narrativa
- **Sin orientación a la acción**: La reunión genera entendimiento del pasado, no compromisos para el futuro

## Diseño

### Formato: Documento pre-read armado por el CEO + 30 minutos de discusión

Un Google Doc, armado por el CEO, enviado 24-48hs antes de la reunión. La reunión en sí es cero presentación, 100% discusión.

### Estructura del Documento (~4 páginas)

#### Sección 1: Scoreboard (1 página | Finanzas provee datos, CEO arma)

Versión condensada de los actuales slides 2 + 4:

- Key Highlights con semáforo (métricas SaaS + resultados financieros)
- Tabla de métricas clave (ajustadas por inflación, actual vs budget)

Datos puros, sin comentario. Esta es la base compartida de hechos que todos leen.

#### Sección 2: Contexto CEO (3-5 líneas | CEO)

Encuadre estratégico del mes. No son preguntas, no es interrogatorio.

- Qué es lo más importante en este momento
- Dónde quiere el CEO que el equipo ponga energía
- Patrones transversales visibles desde la perspectiva del CEO

#### Sección 3: Temas de Discusión (0.5-1 página | CEO)

2-3 temas específicos que el CEO quiere trabajar con el grupo. Cada tema:

- Qué muestran los datos
- Por qué importa
- Qué espera el CEO de la discusión (una decisión, ideas, alineamiento)

Estos reemplazan el viejo slide de "Preguntas", pero reformulados: no es un interrogatorio de Finanzas, sino temas de discusión del CEO que invitan a proponer y resolver juntos.

#### Sección 4: Anexo de Datos (referencia | Finanzas)

Gráficos y tablas clave para quien quiera profundizar:

- Evolución del ARR
- Evolución de clientes (nuevos/churn/neto)
- Retención por cohortes
- Funnel de ventas
- Resumen de P&L
- Resumen de cash flow

No se discute en la reunión. Material de respaldo para contexto.

### Secciones por Área (Evolución Futura)

A medida que el equipo madure con este formato (objetivo: 3-4 meses), los líderes de área empiezan a contribuir sus propias secciones:

- Revenue, Customer, Product, Platform, People
- Cada uno escribe: **Qué pasó y por qué** + **El Pedido** (qué necesita del grupo)
- Finanzas y Compliance son áreas regionales; proveen datos pero no escriben secciones narrativas

Para el primer MBR (febrero), el CEO escribe todo el documento para modelar cómo se ve bien hecho.

### Estructura de la Reunión (30 minutos)

| Minuto | Qué |
|--------|-----|
| 0:00 | CEO abre: "Leí todo. Hoy discutimos estos temas." |
| 0:02 | Tema #1 — CEO encuadra en 1 min, el grupo discute |
| 0:12 | Tema #2 |
| 0:22 | Tema #3 o espacio abierto |
| 0:27 | Compromisos: quién hace qué para cuándo |
| 0:30 | Fin |

### Cadencia

| Cuándo | Qué | Quién |
|--------|-----|-------|
| Semana 1 del mes | Cierre del mes, números finales | Finanzas |
| Día -2 | CEO arma el doc (datos + análisis + temas de discusión) | CEO |
| Día -1 | Doc enviado como pre-read a todos | CEO |
| Día 0 | MBR de 30 min: solo discusión | Todos |

## Plan de Rollout

### Fase 1: MBR de Febrero (17 de marzo de 2026)

- CEO es dueño de todo el documento
- El equipo experimenta el nuevo formato por primera vez
- Reunión preparatoria con reportes directos el 9 de marzo para presentar el enfoque
- Usar datos de enero como ejemplo en vivo durante la reunión preparatoria

### Fase 2: Meses 2-3

- Líderes de área empiezan a escribir sus propias secciones con "El Pedido"
- CEO sigue armando y encuadrando el doc general
- Loop de feedback: qué funciona, qué ajustar

### Fase 3: Mes 4+

- Modelo completo: cada líder de área es dueño de su sección
- Rol del CEO pasa de autor a curador/editor
- El formato se estabiliza, se vuelve la nueva norma

## Decisiones de Diseño

### Por qué un solo documento, no uno por área

Documentos fragmentados crean silos. El líder de Revenue necesita leer lo que escribió Customer y conectar puntos. Un solo doc fuerza la conciencia cross-funcional.

### Por qué lo escribe el CEO primero, no colaborativo desde el día 1

El equipo nunca escribió narrativas. Si les pedís a 5 líderes que escriban 0.5 páginas cada uno el primer día, vas a recibir listas de bullets o relleno generado por IA. El CEO modela cómo se ve bien hecho primero, después va delegando gradualmente.

### Por qué 30 minutos, no 60

La restricción fuerza la priorización. El CEO elige los 2-3 temas más importantes. Todo lo demás se maneja async o en 1:1s. Esto evita que la reunión vuelva a ser una ceremonia de reporting.

### Por qué pre-read, no lectura en la reunión (estilo Amazon)

El equipo no está entrenado para sesiones de lectura silenciosa. El pre-read es culturalmente más fácil de adoptar. Los líderes pueden usar IA para procesar el doc si quieren — la estructura (headers claros, formato consistente) lo facilita.

### Sobre el uso de IA

Los líderes van a usar IA para leer y escribir. La estructura del doc está diseñada para esto:

- El Scoreboard es data pura (fácil de resumir con IA)
- El Contexto CEO y los Temas de Discusión requieren juicio humano genuino — estas son las secciones que no se pueden delegar a la IA
- Las secciones de "El Pedido" (Fase 2+) fuerzan especificidad que la IA no puede fabricar: blockers reales, decisiones concretas necesarias

## Preparación Trimestral para el Board

Los docs mensuales del MBR se acumulan como fuente natural para las presentaciones trimestrales al board:

- Los Scoreboards muestran la tendencia a lo largo de 3 meses
- Las secciones de Contexto CEO capturan la evolución de la narrativa estratégica
- Los Temas de Discusión y sus resultados documentan qué se decidió y por qué

Esto elimina la carrera de último momento para reconstruir qué pasó cada trimestre.
