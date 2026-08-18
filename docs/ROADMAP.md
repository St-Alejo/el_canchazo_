# Roadmap de construcción — Canchazo

Plan de fases y sprints para construir la plataforma. La **Fase 1 (MVP Pasto)** es la que se construye ahora, desglosada en sprints concretos. Las fases 0, 2 y 3 quedan documentadas para contexto, pero no se implementan todavía.

## Fase 0 · Validar (no es trabajo de ingeniería)

En curso por el equipo de producto: contacto directo con las canchas de Pasto identificadas en `docs/documento-producto.md`, sección 2. No requiere código.

## Fase 1 · MVP Pasto — sprints

### Sprint 1 · Cimientos del backend

**Objetivo**: el backend arranca con el modelo de datos completo y administrable.

- Inicializar el proyecto Django + DRF, servido con Uvicorn.
- Conectar a Postgres de Supabase.
- Crear todos los modelos de `docs/arquitectura-tecnica.md` sección 5: `Deporte`, `Usuario`, `Cancha`, `FotoCancha`, `HorarioDisponible`, `Reserva` (con su `UniqueConstraint`), `Pago`, `Calificacion`.
- Registrar los modelos en Django Admin.
- Correr las migraciones sin errores.

**Criterio de aceptación**: se puede crear una cancha, un horario y una reserva de prueba desde Django Admin, y el `UniqueConstraint` rechaza una segunda reserva `pendiente_pago` o `confirmada` sobre el mismo horario.

### Sprint 2 · Autenticación y permisos

**Objetivo**: usuarios reales se registran e inician sesión, con los permisos correctos.

- JWT con `djangorestframework-simplejwt`.
- Registro e inicio de sesión por celular o correo.
- Casilla de consentimiento de datos obligatoria en el registro (Ley 1581).
- Permisos en DRF: un `admin_cancha` solo consulta reservas de su propia cancha; un jugador solo ve las suyas.

**Criterio de aceptación**: pruebas automatizadas que confirmen que un usuario no puede leer reservas de otro usuario ni de otra cancha.

### Sprint 3 · API de canchas y disponibilidad

**Objetivo**: la búsqueda y la disponibilidad real quedan expuestas por API.

- Capa de servicios (`services.py`) para la lógica de negocio, separada de las vistas.
- Endpoints DRF: listar y filtrar canchas (ubicación, precio, servicios, tipo de cancha), horarios disponibles de una cancha en una fecha dada.
- Estado de solicitud de cancha (`pendiente` / `apto` / `no_apto`) para preparar el autoregistro futuro.

**Criterio de aceptación**: la API devuelve resultados filtrados correctos para los mismos filtros que ya existen en el mockup de frontend (precio, servicios).

### Sprint 4 · Reservas, concurrencia y pagos

**Objetivo**: flujo de reserva de punta a punta, con anticipo real.

- Endpoint para crear una reserva en estado `pendiente_pago`.
- Comando programado que libera las reservas vencidas sin pago confirmado.
- Adaptador de Wompi (puerto + implementación) para iniciar el cobro y validar el webhook.
- Webhook de Wompi conectado: confirma el pago y pasa la reserva a `confirmada`.

**Criterio de aceptación**: dos intentos simultáneos de reservar el mismo horario — solo uno se confirma, el otro recibe un error claro. Un pago de prueba en Wompi confirma la reserva correctamente.

### Sprint 5 · Frontend: búsqueda

**Objetivo**: conectar la pantalla de búsqueda del mockup (`canchazo-mockup-v2.jsx`) a la API real.

- Proyecto Next.js con la ruta `/`.
- Reemplazar los datos simulados por llamadas a la API del Sprint 3.
- Mantener el diseño y los filtros ya validados en el mockup.

**Criterio de aceptación**: la búsqueda, los filtros y el orden funcionan igual que en el mockup, pero con datos reales de la base de datos.

### Sprint 6 · Frontend: detalle y reserva

**Objetivo**: conectar la pantalla de detalle y completar el flujo de pago.

- Ruta `/cancha/[id]`.
- Calendario de horarios conectado a la disponibilidad real.
- Botón "Reservar con anticipo" conectado al Sprint 4 (crear reserva + checkout de Wompi).
- "Cómo llegar" con el enlace real a Google Maps ya construido en el mockup.

**Criterio de aceptación**: una persona completa una reserva real de principio a fin, paga el anticipo de prueba, y la reserva queda visible en Django Admin.

### Sprint 7 · Calificaciones y pulido

**Objetivo**: cerrar el círculo de confianza y dejar el MVP listo para las primeras canchas reales.

- Calificación bidireccional (jugador ↔ cancha) tras completar una reserva.
- Marcar asistencia ("sí llegó" / "no llegó").
- Reporte básico de reservas y tráfico por cancha para el equipo.
- Confirmar que la política de cancelación y la política de privacidad estén visibles antes del pago.

**Criterio de aceptación**: se puede completar el ciclo entero (reservar, marcar asistencia, calificar) con al menos dos usuarios de prueba distintos.

## Fase 2 · Consolidar (después del MVP, no en este roadmap todavía)

Notificaciones automáticas, Celery + Redis si hace falta, calificaciones bidireccionales ya activas de fábrica, panel de administración completo. Ver `docs/arquitectura-tecnica.md`, sección 11.

## Fase 3 · Expandir (después del MVP, no en este roadmap todavía)

Otros deportes, otras ciudades, feed social, módulo de torneos. Ver `docs/documento-producto.md`, sección 11.

## Cómo usar este roadmap con Claude Code

Antes de empezar un sprint, confirma con la persona cuál se va a construir en esta sesión — no asumas que se hacen todos seguidos. Al terminar uno, revísalo contra su criterio de aceptación antes de continuar con el siguiente.
