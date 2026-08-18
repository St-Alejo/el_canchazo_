# Canchazo

Plataforma de reservas de canchas sintéticas para Pasto, Nariño — el "Airbnb" de las canchas de la ciudad. Los jugadores buscan, comparan y reservan con anticipo sin tener que llamar a cada cancha; los administradores dejan de depender del teléfono para gestionar su agenda.

**Estado**: MVP completo (Fase 1 del roadmap, los 7 sprints). Ver `docs/AVANCE.md` para el detalle sesión por sesión y las limitaciones conocidas.

## Documentación del proyecto

| Archivo | Qué contiene |
|---|---|
| `docs/CLAUDE.md` | Instrucciones fijas para trabajar en este repo con Claude Code |
| `docs/ROADMAP.md` | Plan de construcción por sprints, con criterios de aceptación |
| `docs/AVANCE.md` | Estado actual: qué está hecho, qué falta y qué se dejó documentado como limitación |
| `docs/arquitectura-tecnica.md` | Arquitectura técnica completa: stack, modelo de datos, patrones |

## Cómo correr el proyecto en local

**Backend** (Django + DRF, puerto 8000):

```bash
cd backend
.venv/Scripts/activate        # o el equivalente en tu sistema
python manage.py migrate
python manage.py seed_demo    # datos de demostración (ver nota abajo)
python -m uvicorn config.asgi:application --port 8000
```

**Frontend** (Next.js, puerto 3000):

```bash
cd frontend
npm install
npm run dev
```

Con ambos corriendo, la app queda en `http://localhost:3000`.

### Nota sobre los datos de demostración

`python manage.py seed_demo` crea 8 canchas **ficticias pero plausibles** en barrios reales de Pasto — no son las canchas reales todavía, porque el archivo con esos datos (`docs/prompt-diseno-nextjs-canchazo.md`) no existe en este repositorio. Cuando aparezca, hay que reemplazar la lista `CANCHAS_DEMO` en `backend/canchas/management/commands/seed_demo.py` y volver a correr el comando.

## Cuentas de prueba

Todas las contraseñas de abajo son solo para el entorno local de desarrollo — no existen en producción.

**Administrador de cancha** (panel: marcar asistencia, calificar jugadores, ver reporte):

| Celular o correo | Contraseña |
|---|---|
| `admin.cancha1` (o `admin.cancha1@canchazo.test`) | `canchazo123` |

Hay un admin por cada una de las 8 canchas sembradas (`admin.cancha1` a `admin.cancha8`), todos con la misma contraseña — cada uno administra únicamente su propia cancha.

**Jugador** (buscar, reservar, calificar):

| Celular o correo | Contraseña | Notas |
|---|---|---|
| `jugador.demo` (o `jugador.demo@canchazo.test`) | `canchazo123` | Cuenta limpia, sin reservas — para probar el flujo de reserva desde cero |
| `jugador_e2e` (o `jugador_e2e@test.com`) | `clave12345` | Ya tiene una reserva `completada` con calificación de ambos lados — para ver "Mis reservas" con historial sin tener que reservar primero |

También podés crear tu propia cuenta desde `/registro`.

**Pagos**: no hay llaves de sandbox de Wompi configuradas todavía, así que el checkout usa un simulador propio (claramente marcado en pantalla) — el botón "Reservar con anticipo" te lleva a una página con botones "Aprobar pago" / "Rechazar pago" en vez del checkout real de Wompi. Ver `docs/AVANCE.md` para el detalle.

## Stack

Django + Django REST Framework, servido con Uvicorn (ASGI) · PostgreSQL (local vía Docker en desarrollo; Supabase en producción) · Next.js (App Router) + Tailwind CSS · Wompi para pagos (por ahora, simulado en desarrollo) · Railway o Render (backend) + Vercel (frontend).

Por qué cada pieza y cómo encajan entre sí: `docs/arquitectura-tecnica.md`.

## Cómo está organizado el código

```
backend/
  <app>/models.py
  <app>/services.py     # lógica de negocio, nunca en las vistas
  <app>/views.py
  <app>/adapters/        # Wompi, SMS, etc. — puertos y adaptadores
frontend/
  app/                   # Next.js App Router
  components/
  lib/
docs/
README.md
```

## Licencia

Este es un proyecto privado en etapa de MVP — todos los derechos reservados. Todavía no se ha elegido una licencia formal ni un modelo de distribución (open source vs. propietario); esa es una decisión de negocio pendiente del equipo, no técnica. Si vas a compartir este código fuera del equipo, confirmá antes con quien lo dirige.
