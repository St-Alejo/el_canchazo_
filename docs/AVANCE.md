# Avance del proyecto — Canchazo

Este archivo se actualiza cada ~5 mensajes de trabajo, o al cerrar una tarea importante, para llevar registro de qué se ha construido y qué sigue. El detalle completo de cada sprint está en `ROADMAP.md`; acá solo va el estado y notas cortas.

**Última actualización**: 18 de agosto de 2026 — Sprints 5, 6 y 7 completados. Fase 1 (MVP Pasto) queda completa de punta a punta.

## Estado general

| Fase | Estado |
|---|---|
| 0 · Validar | En curso (fuera del código, a cargo del equipo de producto) |
| 1 · MVP Pasto | **Completa** (los 7 sprints construidos y verificados) |
| 2 · Consolidar | No iniciada |
| 3 · Expandir | No iniciada |

## Fase 1 · MVP Pasto — sprints

| Sprint | Estado | Notas |
|---|---|---|
| 1 · Cimientos del backend | Completado | Ver detalle abajo |
| 2 · Autenticación y permisos | Completado | Ver detalle abajo |
| 3 · API de canchas y disponibilidad | Completado | Ver detalle abajo |
| 4 · Reservas, concurrencia y pagos | Completado | Ver detalle abajo |
| 5 · Frontend: búsqueda | Completado | Ver detalle abajo |
| 6 · Frontend: detalle y reserva | Completado | Ver detalle abajo |
| 7 · Calificaciones y pulido | Completado | Ver detalle abajo |

## Historial de sesiones

### Sprint 1 — 12 de agosto de 2026

- `docs/arquitectura-tecnica.md` llegó como `.docx`; se convirtió a texto/Markdown (mismo nombre, en `docs/`) para poder leerlo en las sesiones de Claude Code. El `.docx` original se conserva junto al `.md`.
- Proyecto Django + DRF creado en `backend/` (proyecto `config`, servido con Uvicorn/ASGI, no Gunicorn/WSGI), con entorno virtual propio en `backend/.venv`.
- Tres apps creadas siguiendo los dominios del modelo de datos: `usuarios` (`Usuario`, `AUTH_USER_MODEL`), `canchas` (`Deporte`, `Cancha`, `FotoCancha`, `HorarioDisponible`), `reservas` (`Reserva`, `Pago`, `Calificacion`) — todas siguiendo `arquitectura-tecnica.md` sección 5 tal cual.
- `Reserva` incluye el `UniqueConstraint` condicional (`horario_unico_por_cancha`) sobre `cancha`+`fecha`+`hora_inicio` cuando el estado es `pendiente_pago` o `confirmada`.
- Los 8 modelos quedaron registrados en Django Admin.
- Base de datos: **Postgres local vía Docker Compose** (`backend/docker-compose.yml`), no Supabase todavía — se decidió así en esta sesión para no bloquear el sprint. La cadena de conexión vive en `backend/.env` (`DATABASE_URL`), fuera de git.
  - Nota técnica: el puerto por defecto 5432 estaba ocupado por un Postgres nativo ya instalado en esta máquina Windows; el contenedor quedó mapeado al puerto **55432** en su lugar (ver `.env` y `.env.example`).
- Migraciones corridas sin errores.
- Criterio de aceptación verificado por script (`manage.py shell`, no por la UI del Admin porque la extensión de Chrome no estaba conectada en esta sesión): se creó una cancha, un horario y una reserva de prueba; un segundo intento de reserva sobre el mismo horario fue rechazado por Postgres con `IntegrityError` (`duplicate key value violates unique constraint "horario_unico_por_cancha"`). Los datos de prueba se borraron después.
- Superusuario de desarrollo creado: `admin` / `canchazo123` (solo para uso local).

### Sprint 2 — 13 de agosto de 2026

- JWT con `djangorestframework-simplejwt` (`SIMPLE_JWT`: access 30 min, refresh 7 días); `DEFAULT_AUTHENTICATION_CLASSES` en DRF apunta a `JWTAuthentication`.
- Backend de autenticación propio (`usuarios/authentication.py`, `CelularOCorreoBackend`) que permite iniciar sesión con celular o correo como identificador, además del `ModelBackend` estándar.
- Endpoints nuevos: `POST /api/usuarios/registro/`, `POST /api/usuarios/login/`, `POST /api/usuarios/token/refresh/`, `GET /api/usuarios/yo/`.
- Registro exige `consentimiento_datos_aceptado=True` (Ley 1581, 400 si falta) y no permite autoasignarse el rol `superadmin`.
- Capa de servicios: `usuarios/services.py` (`registrar_usuario`), `reservas/services.py` (`reservas_visibles_para`) — nunca lógica de negocio en las vistas.
- `GET /api/reservas/` (`ReservaViewSet`, solo lectura por ahora) filtra el queryset por rol: un `admin_cancha` solo ve reservas de su propia cancha, un jugador solo las suyas. Fuera del queryset da 404, no 403.
- 13 pruebas automatizadas (`usuarios/tests.py`, `reservas/tests.py`): registro, login por celular/correo, consentimiento obligatorio, aislamiento de reservas entre usuarios y entre canchas. Todas pasan.
- Nota de entorno: Docker Desktop no estaba corriendo en esta sesión, así que las pruebas corrieron contra sqlite en memoria (`DATABASE_URL=sqlite:///:memory:` solo para el comando de test, sin tocar `.env`). Antes de seguir con desarrollo normal conviene levantar `docker compose up -d` en `backend/` para volver al Postgres local real.

### Sprint 3 — 13 de agosto de 2026

- Capa de servicios `canchas/services.py`: `listar_canchas(filtros)`, `obtener_cancha_publicada(pk)`, `horarios_disponibles(cancha, fecha)`.
- Endpoints públicos (sin autenticación, como corresponde a la búsqueda de un marketplace):
  - `GET /api/canchas/` — lista y filtra por `deporte` (id), `ubicacion` (texto sobre nombre/dirección), `precio_min`/`precio_max` (sobre la tarifa más barata de la cancha, anotada como `precio_desde`), `servicios` (lista separada por comas, coincidencia exacta de subconjunto).
  - `GET /api/canchas/{id}/` — detalle con fotos.
  - `GET /api/canchas/{id}/disponibilidad/?fecha=YYYY-MM-DD` — horarios de `HorarioDisponible` para esa fecha (por `fecha_especifica` o por `dia_semana`, `0`=lunes según `date.weekday()` de Python), excluyendo los que ya tienen una `Reserva` en `pendiente_pago` o `confirmada` ese mismo horario.
- **Solo se listan/muestran canchas con `estado="apto"`** — así queda preparado el filtro para cuando exista el autoregistro (Sprint futuro): una cancha nueva no aparece en búsquedas hasta ser aprobada.
- Filtro de `servicios` implementado en Python dentro de `services.py` (no con el operador `@>` de Postgres) porque el proyecto corrió las pruebas contra sqlite esta sesión (ver nota de entorno) y el volumen de canchas del MVP es pequeño (8 canchas en Pasto) — no hace falta optimizarlo a nivel de base de datos todavía.
- 10 pruebas nuevas (`canchas/tests.py`): filtros combinados, exclusión de canchas no aprobadas, y disponibilidad (excluye horarios reservados y los de otro día de la semana). Total del proyecto: **23 pruebas, todas pasan.**
- **Nota importante**: el `ROADMAP.md` pide que el criterio de aceptación se valide contra "los mismos filtros que ya existen en el mockup de frontend (`canchazo-mockup-v2.jsx`)", pero ese archivo no existe todavía en el repo (tampoco `docs/documento-producto.md` ni `docs/prompt-diseno-nextjs-canchazo.md`, referenciados en otros lados de la documentación). Los filtros de este sprint se diseñaron a partir del modelo de datos y la descripción del roadmap, no contra el mockup real. **Antes del Sprint 5 (frontend de búsqueda) conviene revisar estos filtros contra el mockup real cuando aparezca en el repo**, por si los nombres de query params o el comportamiento de "precio" (¿tarifa mínima? ¿por horario elegido?) necesitan ajustarse.
- Seguimos sin Docker Desktop corriendo esta sesión; pruebas otra vez contra sqlite en memoria, sin tocar `.env`.

### Sprint 4 — 13 de agosto de 2026

- **Puerto de pagos** (`reservas/adapters/pagos.py`, `PuertoPagos`): interfaz con `crear_cobro()`, `validar_firma_webhook()`, `extraer_confirmacion()`.
  - `reservas/adapters/wompi.py` (`AdaptadorWompi`): implementación real usando el **Web Checkout de Wompi** (URL firmada con `signature:integrity`, sin llamada HTTP para "crear" el cobro) y la verificación de firma de sus eventos de webhook (`signature.checksum`).
  - `reservas/adapters/fake.py` (`AdaptadorPagosFalso`): doble de pruebas, usado en toda la suite vía `ADAPTADOR_PAGOS` (setting con ruta punteada, sobreescribible por `.env`/`override_settings`).
- `POST /api/reservas/` (mismo endpoint que ya listaba, ahora también crea): recibe `cancha_id`, `fecha`, `hora_inicio`, `redirect_url`. El **anticipo lo calcula el servidor** a partir de `HorarioDisponible.tarifa` — el cliente no puede mandar un monto propio. Devuelve la reserva en `pendiente_pago` + `url_pago`.
- Comando `python manage.py liberar_reservas_vencidas`: cancela las reservas `pendiente_pago` cuyo `fecha_expiracion_bloqueo` (10 minutos desde la creación) ya pasó. Pensado para correr por cron cada pocos minutos (todavía no hay cron configurado, es manual).
- `POST /api/webhooks/wompi/`: valida la firma del evento con el adaptador: si es inválida, 400; si es válida, aplica la confirmación de forma **idempotente** (un webhook duplicado no reprocesa una reserva ya `confirmada`) y marca `confirmada` solo si el pago fue `APPROVED`.
- **Concurrencia**: el `UniqueConstraint` de `Reserva` (ya existía desde el Sprint 1) sigue siendo la garantía real. `crear_reserva()` hace un pre-chequeo contra `canchas.services.horarios_disponibles` (respuesta rápida y clara, 409) pero además atrapa `IntegrityError` del `INSERT` como red de seguridad para la carrera real — hay una prueba que fuerza justo ese camino (mockeando el pre-chequeo para que quede desactualizado) y confirma que la base de datos es quien de verdad decide.
- 11 pruebas nuevas: creación de reserva (monto derivado del servidor, cancha no aprobada, horario inexistente, doble intento, y el caso de "pre-chequeo desactualizado" antes descrito), webhook (aprobado, firma inválida, duplicado idempotente, rechazado), y el comando de liberación (libera solo las vencidas, no toca las vigentes ni las confirmadas). Total del proyecto: **34 pruebas, todas pasan.**
- **Dos límites honestos de esta sesión, ninguno de los dos verificado contra el sistema real:**
  1. **Sin llaves de sandbox de Wompi.** El adaptador real (`AdaptadorWompi`) se escribió a partir de la documentación pública de Wompi (Web Checkout + Eventos) de memoria, pero nunca se probó contra el servicio real — nombres de campos exactos, mayúsculas del checksum, y la URL de Web Checkout deberían confirmarse contra la documentación vigente antes de usarlo en producción. Mientras tanto, el desarrollo local usa `AdaptadorPagosFalso` (configurado en `backend/.env` vía `ADAPTADOR_PAGOS`).
  2. **Concurrencia probada en sqlite, en un solo hilo.** El criterio de aceptación pide "dos intentos *simultáneos*"; lo que se probó esta sesión es (a) dos requests secuenciales, y (b) un test dirigido que fuerza el camino del `IntegrityError`. Ninguno reproduce una carrera real con hilos/conexiones concurrentes, porque Docker Desktop seguía sin correr y sqlite en memoria no comparte estado entre conexiones de hilos distintos. **Antes de dar el criterio de aceptación por completamente verificado, conviene repetir la prueba con hilos reales contra el Postgres local (`docker compose up -d`).**

### Sesión del 18 de agosto de 2026 — Sprints 5, 6 y 7 (los tres, en una sola sesión larga)

Se pidió explícitamente construir todos los sprints restantes seguidos, probando cada uno, sin pausar a confirmar entre sprints (excepción puntual a la norma de `CLAUDE.md` de confirmar sprint por sprint). Antes de empezar se verificaron dos pendientes de sesiones anteriores:

- **Docker Desktop** estaba disponible esta vez: se corrió toda la suite (34 pruebas de entonces) contra el Postgres local real (no solo sqlite) — pasó igual.
- **Concurrencia con hilos reales contra Postgres** (pendiente desde el Sprint 4): se armó un script ad-hoc con dos hilos reales y `threading.Barrier` disparando `crear_reserva()` al mismo tiempo sobre el mismo horario, contra el Postgres local real. Resultado: exactamente una reserva quedó creada, la otra recibió `HorarioNoDisponibleError`. Este pendiente queda cerrado.

**Datos de demostración**: `docs/prompt-diseno-nextjs-canchazo.md` (con las 8 canchas reales de Pasto) y `canchazo-mockup-v2.jsx` **siguen sin existir en el repo** — se buscaron de nuevo esta sesión y no aparecieron. Se creó `backend/canchas/management/commands/seed_demo.py`, que puebla 8 canchas **ficticias pero plausibles** (barrios reales de Pasto, precios y coordenadas inventados) con horarios toda la semana, para poder construir y probar el frontend de punta a punta. **Cuando aparezca el archivo real, hay que reemplazar `CANCHAS_DEMO` en ese comando por los datos reales** y re-sembrar.

#### Sprint 5 — búsqueda

- Proyecto Next.js 16 (App Router, Turbopack, TypeScript, Tailwind v4) creado en `frontend/`.
- `django-cors-headers` agregado al backend (`CORS_ALLOWED_ORIGINS`, default `localhost:3000`) para que el frontend en otro puerto pueda llamar a la API en desarrollo.
- `app/page.tsx` (server component) lee `searchParams`, llama a `GET /api/canchas/` (Sprint 3) sin caché (`cache: "no-store"`) y renderiza resultados; `components/SearchFilters.tsx` (client) maneja el formulario de ubicación/precio/servicios actualizando la URL.
- **No se pudo verificar contra el mockup real** (no existe, ver nota de datos arriba) — los filtros se diseñaron a partir de la API del Sprint 3, igual que se advirtió en el Sprint 3.
- Probado con `curl` contra el SSR (`http://localhost:3000/?precio_max=...`, `?servicios=...`): los resultados coinciden con los que devuelve la API directamente.

#### Sprint 6 — detalle y reserva

- `app/cancha/[id]/page.tsx` (server component): ficha de la cancha, fotos (o placeholder — no hay fotos reales cargadas todavía), servicios, botón "Cómo llegar" a Google Maps (`latitud`/`longitud` de la cancha) y botón de llamada.
- `components/ReservaWidget.tsx` (client): selector de fecha, trae horarios de `GET /api/canchas/{id}/disponibilidad/` (Sprint 3), resumen de anticipo + $500 de tarifa de servicio, checkbox obligatorio de aceptación de política de cancelación/privacidad antes de habilitar el botón de reservar (Ley 1480), y llamada a `POST /api/reservas/` (Sprint 4) con el JWT del usuario.
- `app/login/page.tsx` y `app/registro/page.tsx`: mínimos, conectados a los endpoints del Sprint 2. `components/AuthProvider.tsx` guarda el JWT en `localStorage` (sin refresh automático todavía — el access token dura 30 min, ver pendientes).
- **Checkout de pago simulado, sin llaves de Wompi reales** (seguían sin existir esta sesión): se modificó `reservas/adapters/fake.py` (`AdaptadorPagosFalso`, el doble de pruebas — el adaptador real de Wompi no se tocó) para que `url_pago` apunte a una página propia del frontend, `app/pago-simulado/[referencia]/page.tsx`, en vez de a una URL inventada que no respondía a nada. Esa página imita el checkout de Wompi: botones "Aprobar pago" / "Rechazar pago" que llaman directamente a `POST /api/webhooks/wompi/` con la firma falsa de pruebas (`AdaptadorPagosFalso.CHECKSUM_VALIDO`, que viaja en la URL) y redirigen a `app/reserva/confirmacion/page.tsx`. Está marcada visiblemente como "solo desarrollo" en la propia página. Requiere `FRONTEND_URL` en el backend (nuevo setting, default `http://localhost:3000`).
- **Criterio de aceptación verificado de punta a punta**, con `curl` reproduciendo exactamente las llamadas que hace el navegador (no se pudo probar clickeando en un navegador real — ver nota de la extensión de Chrome más abajo): registro de jugador → login → `GET disponibilidad` → `POST /api/reservas/` (queda `pendiente_pago`) → `POST /api/webhooks/wompi/` simulando el clic de "Aprobar pago" → la reserva pasa a `confirmada`. Reserva visible en la base de datos (y por lo tanto en Django Admin) con `id=4` de prueba.

#### Sprint 7 — calificaciones y pulido

- **Backend**: campo nuevo `Reserva.asistencia` (`asistio` / `no_asistio` / vacío) — **no es un quinto estado**, sigue habiendo solo los 4 valores de `estado` que pide `CLAUDE.md`; es un dato aparte que el admin de la cancha registra y que dispara el paso a `completada`. `docs/arquitectura-tecnica.md` sección 5 se actualizó para reflejar este campo y el `UniqueConstraint` nuevo de `Calificacion` (`reserva` + `calificado_por`), que es lo que impide calificar dos veces del mismo lado.
- Servicios nuevos en `reservas/services.py`: `marcar_asistencia` (solo el admin de esa cancha, solo sobre `confirmada`, la pasa a `completada`), `calificar_reserva` (decide `calificado_por` según la relación del usuario autenticado con la reserva, nunca por parámetro del cliente; solo sobre `completada`), `reporte_cancha` (conteos por estado, ingresos confirmados, asistencia).
- Endpoints nuevos: `POST /api/reservas/{id}/marcar-asistencia/`, `POST /api/reservas/{id}/calificar/`, `GET /api/reservas/reporte/{cancha_id}/`.
- **Frontend**: `app/mis-reservas/page.tsx` (jugador: ve sus reservas, califica la cancha cuando está `completada`), `app/panel/page.tsx` (admin de cancha: marca asistencia sobre reservas `confirmada`, califica al jugador, ve el reporte por cancha), `components/CalificarForm.tsx`, `components/ReporteCanchaCard.tsx`, `components/EstadoBadge.tsx`. `app/politica-privacidad/` y `app/politica-cancelacion/` son páginas nuevas (borrador, no revisadas legalmente) enlazadas desde el pie de página y desde el checkbox obligatorio del Sprint 6.
- 7 pruebas nuevas (`reservas/tests.py`): asistencia solo por el admin correcto, no se puede calificar antes de marcar asistencia, ciclo completo con calificación bidireccional, no se puede calificar dos veces del mismo lado, usuario ajeno no puede calificar, reporte visible solo por el admin de esa cancha. Total del proyecto: **41 pruebas, todas pasan** (contra Postgres local real).
- **Criterio de aceptación verificado de punta a punta con dos usuarios de prueba distintos** (`jugador_e2e` y el admin sembrado `admin.cancha1`), siguiendo con `curl` el mismo camino que la sesión anterior de reserva: marcar asistencia → la reserva pasa a `completada` → el jugador califica la cancha → la cancha califica al jugador → `GET /api/reservas/reporte/3/` devuelve los números correctos (1 reserva completada, ingresos confirmados $60.000, 1 asistió).

#### Limitaciones honestas de esta sesión

1. **La extensión de Claude para Chrome no estaba conectada** — todo el frontend se verificó con `next build` (compila y tipa sin errores), `eslint` (sin errores) y peticiones `curl` reproduciendo exactamente las llamadas HTTP que dispara cada botón/formulario del navegador, pero **nadie hizo clic de verdad en una página real**. Antes de mostrárselo a una persona real conviene abrir `npm run dev` (frontend) + `uvicorn` (backend) y clickear el flujo completo al menos una vez.
2. **Sin llaves de sandbox de Wompi todavía** (mismo pendiente del Sprint 4): el checkout real (`reservas/adapters/wompi.py`) sigue sin probarse contra el servicio real. El checkout simulado del Sprint 6 reemplaza esa experiencia solo en desarrollo.
3. **Sin refresh automático de JWT en el frontend**: el access token dura 30 minutos (`SIMPLE_JWT`, Sprint 2); si expira, hay que volver a iniciar sesión manualmente. No se implementó el flujo de refresh silencioso.
4. **Sin fotos reales de canchas**: `FotoCancha` sigue vacío para las 8 canchas demo — no hay archivos de imagen en el repo. El detalle de cancha muestra un placeholder cuando no hay fotos.
5. **`app/panel/page.tsx` arma la lista de "mis canchas" a partir de las reservas existentes**, no de un endpoint dedicado — si una cancha todavía no tiene ninguna reserva, su tarjeta de reporte no aparece en el panel hasta la primera reserva. No bloqueante para el MVP (una cancha sin reservas no tiene nada que reportar todavía), pero vale la pena un endpoint `GET /api/canchas/mias/` si esto molesta en uso real.
6. **Páginas de política de privacidad y cancelación son borrador**, escritas para cumplir el criterio de "visibles antes del pago" del roadmap — no reemplazan revisión legal antes de operar con canchas y usuarios reales.

## Qué sigue

La Fase 1 (MVP Pasto) está completa según el roadmap. Antes de considerarla lista para canchas reales:

- **Reemplazar los datos de demostración** (`seed_demo.py`) por las 8 canchas reales de Pasto en cuanto `docs/prompt-diseno-nextjs-canchazo.md` (o el archivo que corresponda) exista en el repo.
- **Probar el flujo completo clickeando en un navegador real** (ver limitación 1 arriba) — la próxima sesión con la extensión de Chrome conectada debería hacer esto antes de cualquier demo a una persona externa.
- Confirmar el adaptador de Wompi (`reservas/adapters/wompi.py`) contra su documentación vigente y una cuenta de sandbox real antes de usarlo en producción; solo entonces cambiar `ADAPTADOR_PAGOS` a `reservas.adapters.wompi.AdaptadorWompi` en el entorno de producción.
- Configurar el cron real que llame a `manage.py liberar_reservas_vencidas` cada pocos minutos (Railway/Render lo soportan de forma nativa).
- Cuando exista el proyecto de Supabase, reemplazar `DATABASE_URL` en `backend/.env` por la cadena de conexión real (y Supabase Storage para las fotos de cancha, hoy en filesystem local vía `MEDIA_ROOT`).
- Proveedor de SMS/OTP para login por celular (por ahora el login es celular/correo + contraseña, sin OTP).
- Implementar refresh automático de JWT en el frontend antes de que el equipo de producto empiece a usarlo por más de 30 minutos seguidos.
- Endpoint `GET /api/canchas/mias/` si la limitación 5 de arriba resulta molesta en uso real.
- Fase 2 (Consolidar): notificaciones automáticas, Celery + Redis si hace falta, panel de administración más completo — ver `docs/arquitectura-tecnica.md` sección 11. No empezar sin confirmar con la persona, según la norma de `CLAUDE.md`.
