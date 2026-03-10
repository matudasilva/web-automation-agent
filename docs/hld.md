# HLD — Web Automation Agent Project

## 1. Visión general

### Nombre del proyecto

**Web Automation Agent**

### Propósito

Construir un agente reutilizable que ejecute una secuencia definida de interacciones web con comportamiento consistente, utilizando una capa de automatización de navegador más instrucciones persistentes a nivel de proyecto para asegurar mantenimiento, seguridad y repetibilidad.

### Objetivo principal

Automatizar un flujo web estable, por ejemplo:

- iniciar sesión en un sitio objetivo
- navegar a secciones específicas
- extraer o enviar información
- aplicar reglas determinísticas
- guardar evidencia y resultados
- fallar de forma segura cuando el estado de la página no sea el esperado

### Objetivo secundario

Usar el proyecto como vehículo de aprendizaje para:

- desarrollo guiado por tareas con Codex
- uso de `AGENTS.md` como instrucciones persistentes del proyecto
- automatización web con Playwright
- endurecimiento progresivo de flujos web
- logging estructurado y ejecución reproducible

---

## 2. Problema que resuelve

Muchas tareas en navegador son repetitivas, lentas y propensas a error cuando se hacen manualmente.

El objetivo es crear un agente que pueda ejecutar siempre el mismo comportamiento web de forma consistente, reduciendo esfuerzo manual y aportando trazabilidad mediante logs y artefactos.

Casos de uso típicos:

- flujos repetitivos de backoffice
- chequeos de estado en portales web
- completado de formularios con reglas fijas
- extracción de datos desde dashboards o tablas
- operaciones web semisupervisadas con puntos de revisión humana

---

## 3. Alcance

### Dentro del alcance

- estructura base del proyecto en local
- flujo de desarrollo asistido por Codex
- automatización web con Playwright
- ejecución basada en configuración
- manejo de login y sesión
- ejecución determinística de pasos
- capturas, logs y exportación de resultados
- condiciones de parada segura y reintentos
- soporte para un flujo principal en un sitio web en la versión inicial

### Fuera del alcance en v1

- orquestación multi-tenant
- toma de decisiones autónoma avanzada
- resolución de CAPTCHA
- evasión de detección anti-bot
- ejecución distribuida a gran escala
- acciones sin restricción sobre sitios arbitrarios

---

## 4. Arquitectura de alto nivel

```
+----------------------+
|   Usuario / Dev      |
| Define tarea/reglas  |
+----------+-----------+
           |
           v
+----------------------+
|        Codex         |
| Construye y mantiene |
| artefactos del       |
| proyecto vía tasks   |
+----------+-----------+
           |
           v
+----------------------+
|   Repositorio        |
| AGENTS.md            |
| src/                 |
| configs/             |
| tests/               |
| logs/                |
+----------+-----------+
           |
           v
+----------------------+
| Motor de Automatiz.  |
|     Playwright       |
| Browser + locators   |
| flows + estado       |
+----------+-----------+
           |
           v
+----------------------+
|   Sitio objetivo     |
| login / páginas / UI |
+----------+-----------+
           |
           v
+----------------------+
| Artefactos de salida |
| logs, screenshots,   |
| csv/json results     |
+----------------------+
```

---

## 5. Componentes principales

### 5.1 Capa Codex

Responsable de:

- generar la estructura del proyecto
- crear y refactorizar código
- respetar instrucciones del repo desde `AGENTS.md`
- iterar sobre flujos y tests
- crear workflows de desarrollo reutilizables

Codex se usará como agente de desarrollo del proyecto, no como motor directo de navegación web.

### 5.2 Motor de automatización

Se propone usar **Playwright** para:

- abrir contextos de navegador
- navegar páginas
- interactuar con elementos
- esperar estados estables de la UI
- validar resultados
- manejar sesiones autenticadas

### 5.3 Capa de flujos

Encapsula las acciones de negocio:

- flujo de login
- flujo de navegación
- flujo de búsqueda y filtrado
- flujo de extracción o envío
- flujo de verificación
- flujo de recuperación ante errores

### 5.4 Capa de configuración

Guarda el comportamiento determinístico fuera del código cuando sea posible:

- URL base
- origen de credenciales
- selectores o identificadores de página
- política de reintentos
- modo de ejecución
- rutas de salida
- flags o toggles de reglas

### 5.5 Capa de evidencia y logging

Genera:

- logs de ejecución
- capturas en checkpoints o ante fallos
- resultados exportados en JSON o CSV
- snapshots HTML opcionales

---

## 6. Estructura propuesta del repositorio

```
web-automation-agent/
├─ AGENTS.md
├─ README.md
├─ .env.example
├─ pyproject.toml
├─ package.json                  # opcional si se usa ruta TS/Node
├─ configs/
│  ├─ environments/
│  │  └─ local.yaml
│  └─ rules.yaml
├─ src/
│  ├─ main.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ logger.py
│  │  └─ exceptions.py
│  ├─ browser/
│  │  ├─ session.py
│  │  └─ factory.py
│  ├─ pages/
│  │  ├─ login_page.py
│  │  ├─ dashboard_page.py
│  │  └─ target_flow_page.py
│  ├─ flows/
│  │  ├─ login_flow.py
│  │  ├─ execute_task_flow.py
│  │  └─ export_results_flow.py
│  └─ services/
│     ├─ screenshot_service.py
│     └─ result_writer.py
├─ tests/
│  ├─ e2e/
│  ├─ smoke/
│  └─ fixtures/
├─ logs/
└─ screenshots/
```

---

## 7. Modelo de ejecución

### Modo A — Desarrollo asistido

Vos definís el flujo y Codex crea o ajusta la implementación.

### Modo B — Ejecución manual

Corrés el agente localmente para una tarea concreta:

- abre navegador
- ejecuta flujo
- guarda evidencia
- cierra sesión

### Modo C — Ejecución programada

Fase posterior:

- cron, systemd o Docker schedule
- mismo flujo ejecutado en horarios definidos
- resultados guardados en carpeta o enviados a un canal

---

## 8. Flujo principal de ejecución

```
1. Cargar configuración y reglas de runtime
2. Iniciar contexto de navegador
3. Autenticar o restaurar sesión
4. Navegar a la página objetivo
5. Ejecutar secuencia fija de interacciones
6. Validar estado esperado de la UI
7. Capturar evidencia
8. Exportar resultados
9. Salir limpiamente
10. Ante error: reintentar dentro de límites y luego detenerse de forma segura
```

---

## 9. Principios de diseño

### Determinismo primero

Priorizar reglas explícitas por encima de comportamiento libre.

### Seguro por defecto

No permitir acciones destructivas salvo habilitación explícita.

### Observable

Cada paso importante debe dejar evidencia.

### Mantenible

Centralizar selectores y abstracciones de página.

### Testeable

Cada flujo principal debe tener al menos un smoke test.

### Extensible

La v1 soporta un flujo; la v2 podrá agregar nuevos flujos o sitios.

---

## 10. Seguridad y controles operativos

### Manejo de credenciales

- nunca hardcodear secretos
- usar `.env` o más adelante un secret manager
- separar estado de autenticación del código fuente

### Acciones seguras

- mantener allowlist de dominios permitidos
- mantener allowlist de acciones permitidas
- requerir flag explícito para acciones de submit o finalización

### Auditabilidad

- guardar logs con timestamp
- capturar screenshot antes y después de acciones críticas
- persistir resumen de resultados por ejecución

### Manejo de fallos

- reintentos acotados
- detenerse ante navegación inesperada
- detenerse ante drift de selectores sobre cierto umbral
- emitir artefacto claro de error

---

## 11. Riesgos principales

### Cambios en la UI

El sitio cambia estructura y se rompen locators.

**Mitigación:** usar locators robustos, abstracciones por página y smoke tests.

### Problemas de autenticación o sesión

La sesión expira o cambia el flujo de login.

**Mitigación:** aislar el flujo de autenticación y reutilizar estado autenticado cuando sea válido.

### Esperas frágiles y comportamiento flaky

El uso de sleeps manuales puede volver inestable la automatización.

**Mitigación:** apoyarse en esperas explícitas y primitivas nativas de Playwright.

### Sobreautomatización

El agente ejecuta acciones fuera de lo previsto.

**Mitigación:** restricciones por dominio, acción y pasos permitidos desde config y `AGENTS.md`.

---

## 12. Requisitos no funcionales

- **Confiabilidad:** ejecución repetible del mismo flujo
- **Trazabilidad:** logs + screenshots + archivo de resultados
- **Mantenibilidad:** diseño modular por páginas y flujos
- **Portabilidad:** local-first, preparado para Docker más adelante
- **Seguridad:** superficie de acción restringida
- **Ergonomía de desarrollo:** repo claro y amigable para Codex

---

## 13. Decisiones tecnológicas sugeridas

### Recomendado para v1

- **Lenguaje:** Python
- **Automatización:** Playwright
- **Configuración:** YAML + `.env`
- **Logging:** logging estructurado
- **Testing:** smoke tests + happy path end-to-end
- **Agente de desarrollo:** Codex
- **Instrucciones del proyecto:** `AGENTS.md`

### Motivo de esta elección

Es la ruta más corta hacia:

- código legible
- experimentación rápida en local
- integración limpia con Codex
- patrones sólidos de automatización web

---

## 14. Fases de entrega

### Fase 0 — Bootstrap del proyecto

- inicialización del repo
- README
- AGENTS.md
- template de variables de entorno
- dependencias
- base de logging y configuración

### Fase 1 — Fundación del navegador

- setup de Playwright
- factory de browser session
- ejecución local con navegador visible
- soporte de screenshots

### Fase 2 — Primer flujo estable

- flujo de login
- navegación al objetivo
- secuencia fija de interacción
- exportación de resultados

### Fase 3 — Hardening

- reintentos
- mejora de locators
- reutilización de sesión
- smoke tests
- errores estructurados

### Fase 4 — Extensibilidad controlada

- nuevos módulos de flujo
- corridas programadas
- notificaciones opcionales

---

## 15. Criterios de éxito

La v1 será exitosa si puede:

1. abrir el sitio objetivo
2. autenticarse de forma confiable
3. ejecutar un flujo determinístico completo
4. exportar un resultado útil
5. generar capturas y logs
6. fallar de forma segura ante estados inesperados
7. ser iterada por Codex sin perder estructura

---

# Primer task para Codex

Este sería un muy buen primer prompt para abrir el proyecto en Codex:

```
Inicializa un nuevo proyecto llamado "web-automation-agent".

Objetivo:
Construir un agente de automatización web mantenible para un flujo determinístico en navegador usando Python y Playwright.

Requisitos:
- Crear una estructura de proyecto limpia
- Agregar README.md con propósito del proyecto, setup y forma de ejecución
- Agregar AGENTS.md con reglas del proyecto y convenciones de código
- Agregar .env.example para configuración de runtime
- Crear una estructura modular en src/ con:
  - core/
  - browser/
  - pages/
  - flows/
  - services/
- Agregar logging estructurado
- Agregar carga de configuración desde variables de entorno
- Agregar un browser launcher básico con Playwright
- Agregar soporte para screenshots
- Agregar un flujo placeholder de login
- Agregar un flujo placeholder de negocio
- Agregar tests/ con un placeholder de smoke test
- Mantener todo el código, comentarios, documentación y mensajes de commit en inglés

Intención de arquitectura:
- Codex será usado como agente de desarrollo para iteraciones del proyecto
- Playwright será la capa de automatización del navegador
- El diseño debe soportar ejecución determinística basada en reglas
- El proyecto debe ser seguro por defecto y fácil de extender

Entregables:
- scaffold inicial completo
- setup local mínimo ejecutable
- marcadores TODO claros para el primer flujo real sobre un sitio web
```

---

# AGENTS.md inicial sugerido

```
# AGENTS.md

## Propósito del proyecto
Este repositorio contiene un agente de automatización web para flujos determinísticos en navegador.

## Reglas generales
- Mantener la arquitectura simple y modular.
- Priorizar claridad por encima de complejidad innecesaria.
- No hardcodear secretos, credenciales ni valores específicos de entorno.
- Mantener la lógica de negocio fuera de las clases de página siempre que sea posible.
- Usar nombres explícitos para flows, pages y services.
- Priorizar comportamiento determinístico por encima de razonamiento autónomo.

## Reglas de seguridad
- No agregar acciones destructivas por defecto.
- No implementar mecanismos para evadir autenticación ni protecciones anti-bot.
- Requerir flags explícitos para operaciones de submit o finalize.
- Restringir la automatización a dominios aprobados.

## Convenciones de código
- Usar Python para la implementación.
- Mantener código y documentación en inglés.
- Agregar logging alrededor de pasos importantes.
- Capturar screenshots en checkpoints importantes y ante fallos.
- Evitar sleeps arbitrarios cuando Playwright ofrezca mecanismos de espera más sólidos.

## Testing
- Agregar al menos un smoke path por cada flujo importante.
- Mantener selectores centralizados y fáciles de actualizar.
- Preferir locators resilientes.

## Estilo de entrega
- Hacer cambios pequeños y revisables.
- Actualizar README cuando se agregue comportamiento operativo.
- Dejar TODOs claros donde todavía falten detalles del sitio objetivo.
```