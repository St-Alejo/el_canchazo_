Arquitectura técnica — Plataforma de reservas de canchas sintéticas
Versión: 2.1 — 5 de agosto de 2026 (capa de servicios y puertos/adaptadores)
Estado: Borrador para equipo de desarrollo
Documento relacionado: documento-producto.md
1. Filosofía de la arquitectura
Simple de construir y mantener con un equipo pequeño
Backend propio en Python/Django: más control, más portable, y aprovecha que el equipo ya conoce el lenguaje
Separación entre lógica de negocio y detalles de infraestructura donde de verdad aporta valor (integraciones externas), sin imponer una arquitectura hexagonal completa que no se justifica para el tamaño del equipo
Web primero, preparada para una app móvil más adelante sin rehacer el backend
El modelo de datos no asume un solo deporte
2. Por qué Django, y qué cambia frente a la versión anterior
La primera versión de este documento proponía apoyarse en las herramientas "todo incluido" de Supabase (Auth, Realtime, Edge Functions) además de su base de datos. Esta versión mueve el backend a Django por razones concretas:
Panel de administración casi gratis: Django Admin genera automáticamente gran parte del panel de moderación de canchas y reservas que había que construir a mano — ahorra trabajo real en la fase 1.
Un solo lenguaje conocido por el equipo: la lógica de negocio (reglas de cancelación, cálculo de tarifas, validaciones) se escribe en Python en lugar de en las funciones serverless de Supabase (Deno/TypeScript).
Portabilidad: autenticación, permisos y tareas programadas quedan en código propio, no atadas a las herramientas específicas de un proveedor.
Control total sobre tareas en segundo plano: liberar una reserva vencida o enviar notificaciones (fase 2) se maneja de forma más natural con Django que con funciones serverless sueltas.
Lo que se mantiene de Supabase: su base de datos Postgres (Django se conecta directo) y, opcionalmente, su servicio de almacenamiento (Supabase Storage) para fotos de canchas, ya que es compatible con el estándar S3.
Lo que Django reemplaza: autenticación (Supabase Auth → Django + Django REST Framework), API (API automática de Supabase → endpoints hechos con DRF), tiempo real (Supabase Realtime → actualización periódica del panel, ver sección 7) y funciones serverless (Edge Functions → vistas de Django y tareas programadas).
3. Organización interna del backend: capa de servicios y puertos para integraciones externas
Django, por diseño, mezcla el modelo de datos con la lógica de persistencia — el ORM hace que un modelo sea a la vez la estructura de datos y la forma de guardarla. Eso es lo opuesto a una arquitectura hexagonal pura, que exige que la lógica de negocio no sepa nada de cómo se guardan los datos. Aplicar hexagonal estricto en Django implicaría mantener una entidad de dominio separada de cada modelo, con código de traducción entre las dos — complejidad real que no se justifica para el tamaño de este equipo y de este proyecto.
En su lugar, se adoptan dos ideas prácticas tomadas de hexagonal, sin la ceremonia completa:
Capa de servicios: la lógica de negocio (reglas de cancelación, cálculo de tarifas, validaciones de reserva) vive en funciones o clases dentro de un módulo services.py por app, no directamente en las vistas de Django REST Framework. Las vistas quedan delgadas: reciben la petición HTTP, llaman al servicio correspondiente, devuelven la respuesta. Esto hace la lógica de negocio más fácil de probar (sin pasar por una petición HTTP de por medio) y más fácil de reutilizar si algún día hace falta desde otro lugar, como un comando de administración o una tarea de Celery.
Puertos y adaptadores solo para integraciones externas: en vez de aplicar esto a toda la aplicación, se aplica donde de verdad se paga: los servicios externos que podrían cambiar con el tiempo. Para pagos, se define una interfaz simple (por ejemplo, con métodos crear_cobro() y verificar_pago()) y Wompi es una implementación concreta de esa interfaz. Lo mismo aplica para el proveedor de SMS en la fase 2. Esto da dos beneficios concretos: se puede probar la lógica de reservas sin pegarle a la API real de Wompi (usando una implementación falsa de la interfaz en las pruebas), y si algún día conviene cambiar de pasarela, el cambio queda contenido en un solo lugar sin tocar el resto del sistema.
Aclaración importante: esto ayuda a la mantenibilidad y facilidad de prueba del código — no es, por sí mismo, lo que hace que la aplicación aguante más tráfico. La escalabilidad de carga se resuelve con otras piezas ya cubiertas en este documento: poder correr varias instancias del backend detrás de Railway/Render, los índices y restricciones de la base de datos, y mover trabajo pesado a tareas en segundo plano (Celery, ver sección 4).
4. Stack recomendado
Capa
Herramienta
Por qué
Backend / API
Django + DRF, con capa de servicios (sección 3), servido con Uvicorn (ASGI, no Gunicorn/WSGI)
Framework maduro, Python, admin incluido; Uvicorn deja la puerta abierta a Django Channels más adelante sin cambiar de servidor
Base de datos
PostgreSQL — se mantiene el proyecto de Supabase como base de datos, conectado directo desde Django
Ya definido; Django tiene soporte de primera clase para Postgres
Autenticación
Django + DRF con JWT (djangorestframework-simplejwt), o django-allauth si se quiere login social
Reemplaza Supabase Auth; control total del flujo de registro y login por celular
Almacenamiento de fotos
Supabase Storage (compatible S3) vía django-storages, o alternativamente Cloudflare R2 / AWS S3
Aprovecha lo ya definido sin depender del resto de Supabase
Tareas programadas
Comando de Django + cron para empezar; Celery + Redis si en la fase 2 hacen falta más tareas en segundo plano
Empieza simple, crece cuando haga falta
Frontend web
Next.js (React) — sin cambios
Sigue siendo válido; ahora consume la API de Django en lugar de la de Supabase
Hosting backend
Railway o Render
Despliegue de Django simple, con variables de entorno y tareas programadas soportadas de forma nativa
Hosting frontend
Vercel — sin cambios
Sigue siendo la opción natural para Next.js
Pagos
Wompi, detrás de un puerto/adaptador (sección 3)
El webhook lo recibe una vista de Django que llama al adaptador de Wompi
 
5. Modelo de datos (como modelos de Django)
class Deporte(models.Model):
    nombre = models.CharField(max_length=50)  # "Fútbol", "Tenis", "Bolos"
 
class Usuario(AbstractUser):
    celular = models.CharField(max_length=20, unique=True)
    rol = models.CharField(choices=[("jugador", "Jugador"), ("admin_cancha", "Admin cancha"), ("superadmin", "Superadmin")])
    consentimiento_datos_aceptado = models.BooleanField(default=False)
    fecha_consentimiento = models.DateTimeField(null=True, blank=True)
 
class Cancha(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField()
    direccion = models.CharField(max_length=255)
    latitud = models.FloatField()
    longitud = models.FloatField()
    telefono = models.CharField(max_length=20)
    deporte = models.ForeignKey(Deporte, on_delete=models.PROTECT)
    servicios = models.JSONField(default=list)  # ["parqueadero", "cubierta", "baño"]
    estado = models.CharField(choices=[("pendiente", "Pendiente"), ("apto", "Apto"), ("no_apto", "No apto")])
    administrador = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha_registro = models.DateTimeField(auto_now_add=True)
 
class FotoCancha(models.Model):
    cancha = models.ForeignKey(Cancha, related_name="fotos", on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to="canchas/")  # vía django-storages -> Supabase Storage
    orden = models.PositiveSmallIntegerField(default=0)
 
class HorarioDisponible(models.Model):
    cancha = models.ForeignKey(Cancha, on_delete=models.CASCADE)
    dia_semana = models.PositiveSmallIntegerField(null=True, blank=True)
    fecha_especifica = models.DateField(null=True, blank=True)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    tarifa = models.DecimalField(max_digits=10, decimal_places=2)
 
class Reserva(models.Model):
    cancha = models.ForeignKey(Cancha, on_delete=models.PROTECT)
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(choices=[
        ("pendiente_pago", "Pendiente de pago"),
        ("confirmada", "Confirmada"),
        ("cancelada", "Cancelada"),
        ("completada", "Completada"),
    ])
    monto_anticipo = models.DecimalField(max_digits=10, decimal_places=2)
    monto_tarifa_servicio = models.DecimalField(max_digits=10, decimal_places=2, default=500)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion_bloqueo = models.DateTimeField(null=True, blank=True)
    # Sprint 7: no es un quinto estado de `estado` (siguen siendo solo los 4 de arriba). Es un
    # dato aparte que registra el admin de la cancha después del horario reservado, y que
    # dispara el paso a `completada` (ver reservas/services.py::marcar_asistencia).
    asistencia = models.CharField(
        null=True, blank=True,
        choices=[("asistio", "Sí llegó"), ("no_asistio", "No llegó")],
    )
 
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cancha", "fecha", "hora_inicio"],
                condition=models.Q(estado__in=["pendiente_pago", "confirmada"]),
                name="horario_unico_por_cancha",
            )
        ]
 
class Pago(models.Model):
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=30)
    referencia_wompi = models.CharField(max_length=100)
    fecha = models.DateTimeField(auto_now_add=True)
 
class Calificacion(models.Model):
    reserva = models.ForeignKey(Reserva, related_name="calificaciones", on_delete=models.CASCADE)
    calificado_por = models.CharField(choices=[("jugador", "Jugador"), ("cancha", "Cancha")])
    puntuacion = models.PositiveSmallIntegerField()
    comentario = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        # Sprint 7: cada lado (jugador o cancha) califica una reserva una sola vez.
        constraints = [
            models.UniqueConstraint(
                fields=["reserva", "calificado_por"],
                name="una_calificacion_por_lado_y_reserva",
            )
        ]
 
6. El problema de la doble reserva (concurrencia), resuelto en Django
Al iniciar el pago, se crea una Reserva en estado pendiente_pago con una hora de expiración corta (ej. 10 minutos).
El UniqueConstraint con condition del modelo Reserva (sección 5) hace que Postgres rechace automáticamente un segundo intento sobre el mismo horario mientras haya una reserva pendiente_pago o confirmada — la base de datos protege la regla, no solo el código de la aplicación.
Un comando de Django (por ejemplo manage.py liberar_reservas_vencidas), ejecutado por cron cada pocos minutos, libera las reservas pendiente_pago que expiraron sin pago confirmado.
Una vista de Django recibe el webhook de Wompi y actualiza el estado a confirmada.
7. Autenticación, permisos y panel "en tiempo real"
Autenticación: Django REST Framework con JWT (djangorestframework-simplejwt); login por celular (código OTP vía un proveedor de SMS) o correo.
Permisos: ya no hay Row Level Security automática de Supabase, así que el control de acceso se implementa en las vistas de DRF — cada administrador de cancha solo consulta reservas donde cancha.administrador == usuario_actual, cada jugador solo ve sus propias reservas. Esto sigue cumpliendo el acceso restringido que exige la Ley 1581 de Habeas Data, solo que ahora vive en código de Django en lugar de en políticas de base de datos — conviene cubrirlo con pruebas automatizadas, ya que no hay una capa de la base de datos garantizándolo por defecto.
Panel "en tiempo real": para la fase 1 alcanza con que el panel de la cancha se actualice solo cada 15-30 segundos o tenga un botón de refrescar — mucho más simple que montar WebSockets. Si más adelante hace falta tiempo real de verdad, Django Channels es el camino natural.
8. Integración de pagos
El jugador elige horario → una vista de DRF crea la reserva en pendiente_pago
El frontend abre el checkout de Wompi por el anticipo + $500 de tarifa de servicio
Wompi llama a un endpoint (/api/webhooks/wompi/) cuando el pago se confirma
Esa vista de Django valida la firma del webhook y llama al servicio de reservas (sección 3), que marca la reserva como confirmada y descarta duplicados — la vista nunca habla directo con la lógica de negocio, pasa siempre por el adaptador de Wompi y el servicio correspondiente
9. Seguridad y cumplimiento
Casilla de consentimiento explícito y obligatoria en el registro (Ley 1581), guardada en el modelo Usuario
Política de privacidad y de cancelación visibles y aceptadas antes del pago (Ley 1480)
HTTPS de punta a punta (por defecto en Railway/Render y Vercel)
Registro de auditoría de cambios de estado en reservas — Django tiene paquetes ya hechos para esto (por ejemplo django-simple-history) en vez de construirlo desde cero
Django Admin ya trae control de acceso por usuario y registro de quién hizo qué, útil para el equipo de moderación sin escribir código adicional
10. Organización del proyecto
Un repositorio de backend (Django + DRF), desplegado en Railway o Render, conectado a la base de datos Postgres de Supabase
Un repositorio de frontend (Next.js), desplegado en Vercel, consumiendo la API de Django
Fotos de canchas en Supabase Storage (o S3/R2), referenciadas desde el modelo FotoCancha
11. Roadmap técnico
Fase
Contenido técnico
1 · MVP Pasto
Django + DRF con capa de servicios, Postgres, autenticación propia, integración de Wompi vía adaptador, panel vía Django Admin y/o vistas propias
2 · Consolidar
Notificaciones automáticas detrás de un adaptador propio (agregar Celery + Redis si hace falta), reportes para el equipo, calificaciones bidireccionales activas
3 · Expandir
Activar más filas en Deporte, evaluar Django Channels si se necesita tiempo real de verdad, PWA o app nativa según volumen
 
12. Decisiones técnicas pendientes
Proveedor de SMS/OTP para login por celular
Railway vs Render para el hosting del backend (ambos son válidos; se sugiere elegir según precio y comodidad del equipo)
Si conviene adoptar Celery desde la fase 1 o esperar a que la fase 2 lo justifique
Si se conecta a Supabase Postgres usando su pooler (modo transacción) o si conviene mover la base de datos a Railway/Render para reducir piezas distintas en el stack
Confirmar con el equipo a qué se refería con "arquitectura de cascada" para evaluar si aplica algo adicional
