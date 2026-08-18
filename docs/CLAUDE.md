# Canchazo — Plataforma de reservas de canchas sintéticas (Pasto, Nariño)

## Qué es esto

Marketplace tipo Airbnb para canchas sintéticas: los jugadores buscan, ven disponibilidad real y reservan con anticipo; los administradores de cancha dejan de depender del teléfono. Contexto completo del producto en `docs/documento-producto.md`. Plan de construcción por sprints en `ROADMAP.md`. Léelos antes de trabajar si no los has leído en esta sesión.

## Stack

- **Backend**: Django + Django REST Framework, servido con **Uvicorn (ASGI)** — no Gunicorn/WSGI. Deja la puerta abierta a Django Channels más adelante sin cambiar de servidor.
- **Base de datos**: PostgreSQL alojado en Supabase, conexión directa desde Django (no se usa el resto de las herramientas de Supabase).
- **Almacenamiento de archivos**: Supabase Storage (compatible S3) vía `django-storages`, para fotos de canchas.
- **Frontend**: Next.js (App Router) + Tailwind CSS.
- **Pagos**: Wompi, integrado detrás de un adaptador propio (ver "Patrones de arquitectura").
- **Hosting**: backend en Railway o Render; frontend en Vercel.

Detalle completo de cada decisión y el porqué: `docs/arquitectura-tecnica.md`.

## Patrones de arquitectura (no te saltes esto)

- **Capa de servicios**: la lógica de negocio vive en `services.py` por app de Django, nunca directamente en las vistas de DRF. Las vistas son delgadas: reciben la petición, llaman al servicio, devuelven la respuesta.
- **Puertos y adaptadores solo para integraciones externas** (Wompi, y el proveedor de SMS en fase 2): define una interfaz simple y una implementación concreta detrás de ella. No apliques este patrón al resto de la aplicación — Django ya mezcla modelo y persistencia por diseño, y forzar hexagonal puro ahí sería sobre-ingeniería para este equipo.
- **Concurrencia en reservas**: la regla que evita la doble reserva vive en la base de datos, no solo en el código de la aplicación. Usa un `UniqueConstraint` condicional en el modelo `Reserva` (código exacto en `docs/arquitectura-tecnica.md`, sección 5). No la reimplementes solo a nivel de aplicación.

## Estructura del proyecto

```
backend/
  <app>/models.py
  <app>/services.py
  <app>/views.py
  <app>/adapters/     # Wompi, SMS, etc.
frontend/
  app/                # Next.js App Router: / y /cancha/[id]
  components/
  lib/
docs/
  documento-producto.md
  arquitectura-tecnica.md
ROADMAP.md
AVANCE.md
README.md
```

## Convenciones

- Nombres de modelos, campos y variables de negocio en español (`Reserva`, `Cancha`, `monto_anticipo`), coherente con la documentación del proyecto. Nombres técnicos genéricos y comentarios de código en inglés están bien si es más natural para las librerías usadas.
- Todo estado de reserva usa únicamente estos cuatro valores: `pendiente_pago`, `confirmada`, `cancelada`, `completada`. No agregues estados nuevos sin actualizar `docs/arquitectura-tecnica.md`.
- La tarifa de servicio ($500 COP) se cobra al jugador, encima del anticipo. La cancha siempre recibe el 100% de su tarifa acordada. No cambies este modelo sin confirmarlo explícitamente.
- Sigue el modelo de datos de `docs/arquitectura-tecnica.md` (sección 5) tal cual — no lo rediseñes por tu cuenta.

## Cómo trabajar en este repo

- Antes de escribir código para una fase nueva, lee el sprint correspondiente completo en `ROADMAP.md`.
- Al terminar un sprint, revísalo contra su criterio de aceptación antes de pasar al siguiente.
- No asumas que se construyen todos los sprints seguidos en una sola sesión: confirma con la persona cuál sprint toca antes de empezar.
- **Registro de avance**: cada aproximadamente 5 mensajes de trabajo, o al terminar una tarea significativa (lo que ocurra primero), actualiza `AVANCE.md` con lo que se completó, en qué sprint se está, y qué sigue. Esta es una instrucción de comportamiento, no una regla forzada por el sistema — si en una sesión larga notas que no se ha actualizado, pide explícitamente "actualiza AVANCE.md" y se hace de inmediato.
- Plugins y skills recomendados antes de escribir la primera línea de código: ver `README.md`, sección "Antes de empezar a construir".

## Datos de referencia

Las 8 canchas reales de Pasto para poblar datos de prueba (nombre, barrio, precio, coordenadas, servicios) están en la tabla final de `docs/prompt-diseno-nextjs-canchazo.md`.
