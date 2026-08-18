# Canchazo

Plataforma de reservas de canchas sintéticas para Pasto, Nariño — el "Airbnb" de las canchas de la ciudad. Los jugadores buscan, comparan y reservan con anticipo sin tener que llamar a cada cancha; los administradores dejan de depender del teléfono para gestionar su agenda.

## Documentación del proyecto

| Archivo | Qué contiene |
|---|---|
| `CLAUDE.md` | Instrucciones fijas para trabajar en este repo con Claude Code |
| `ROADMAP.md` | Plan de construcción por sprints, con criterios de aceptación |
| `AVANCE.md` | Estado actual: qué está hecho y qué falta — se actualiza mientras se construye |
| `docs/documento-producto.md` | Producto completo: problema, mercado, modelo de negocio, alcance |
| `docs/arquitectura-tecnica.md` | Arquitectura técnica completa: stack, modelo de datos, patrones |

## Flujo de la aplicación

**Jugador**: entra a la web → busca canchas cercanas o por nombre/barrio → filtra por precio, horario y servicios → abre la ficha de una cancha (fotos, tarifas, calendario, calificación, cómo llegar) → elige día y horario disponible → paga el anticipo más $500 COP de tarifa de servicio → recibe confirmación → juega → califica la cancha.

**Administrador de cancha**: se suma a la plataforma (al inicio, contactado directamente por el equipo) → crea el perfil de su cancha con fotos, tarifas y horarios → ve las reservas entrantes en un panel, sin contestar llamadas → marca si el cliente llegó → califica al jugador.

**Equipo de Canchazo**: aprueba o rechaza solicitudes de nuevas canchas, da soporte, resuelve disputas del tipo "sí llegó" / "no llegó".

Detalle completo paso a paso: `docs/documento-producto.md`, sección 6.

## Stack

Django + Django REST Framework, servido con Uvicorn (ASGI) · PostgreSQL en Supabase · Supabase Storage · Next.js (App Router) + Tailwind CSS · Wompi para pagos · Railway o Render (backend) + Vercel (frontend).

Por qué cada pieza y cómo encajan entre sí: `docs/arquitectura-tecnica.md`.

## Cómo está organizado el código

```
backend/
  <app>/models.py
  <app>/services.py     # lógica de negocio, nunca en las vistas
  <app>/views.py
  <app>/adapters/        # Wompi, SMS, etc. — puertos y adaptadores
frontend/
  app/                   # Next.js App Router: / y /cancha/[id]
  components/
  lib/
docs/
ROADMAP.md
AVANCE.md
```

## Antes de empezar a construir

Estos plugins y skills de Claude Code ayudan a que el desarrollo salga con buenas prácticas desde el inicio. Los tres primeros son oficiales de Anthropic y se instalan con un comando desde una sesión de Claude Code:

- **`/plugin install security-guidance@claude-plugins-official`** — revisa el código en busca de vulnerabilidades (inyección SQL, secretos hardcodeados, IDOR, deserialización insegura, SSRF) mientras se escribe, no solo al final. Especialmente relevante acá porque el proyecto maneja pagos y datos personales sujetos a la Ley 1581. Gratis, sin configuración adicional para empezar a usarlo.
- **`/code-review`** — revisión de código ya incluida en Claude Code; útil sobre pull requests si el equipo usa GitHub.
- **`/verify`** — comando ya incluido, sin instalación: construye y corre la app para confirmar que un cambio funciona de verdad, en vez de asumir que "debería funcionar".

Además, vale la pena crear un par de skills propias del proyecto — instrucciones que Claude Code aprende una vez y reutiliza con un comando corto — para no repetir las mismas reglas en cada sesión:

- Una skill para crear una app nueva de Django siguiendo la estructura del proyecto (`models.py` + `services.py` + `adapters/`) automáticamente.
- Una skill para crear un adaptador nuevo (puerto + implementación) con el mismo patrón que se usó para Wompi, para cuando llegue el proveedor de SMS en la fase 2.

Basta con pedir "créame una skill para X" y Claude Code la arma en minutos — no hace falta buscarlas en un marketplace externo. Sobre marketplaces de terceros: Anthropic distingue entre su propio marketplace oficial (`claude-plugins-official`), un marketplace comunitario con revisión de seguridad automática, y fuentes sueltas de GitHub sin ninguna revisión. Conviene instalar solo de las dos primeras y ser cauteloso con el resto.

## Empezar a construir

En la carpeta del proyecto: `claude`, y luego "lee CLAUDE.md, ROADMAP.md y AVANCE.md, y empecemos con el Sprint 1". Cada sprint tiene su propio criterio de aceptación, así que se puede avanzar sesión por sesión sin perder el hilo aunque se retome en días distintos.
