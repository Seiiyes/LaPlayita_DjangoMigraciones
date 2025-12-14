from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from users.decorators import check_user_role
from .models import Cliente, PuntosFidelizacion, ProductoCanjeble, CanjeProducto
from inventory.models import Producto, MovimientoInventario
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
from django.contrib import messages
from decimal import Decimal
import json

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


# ==================== ADMIN & CLIENTE CRUD ====================


@login_required
@check_user_role(allowed_roles=["Administrador", "Vendedor"])
def cliente_list(request):
    """Lista todos los clientes del sistema."""
    clientes = Cliente.objects.all().order_by("nombres")
    es_vendedor = request.user.rol.nombre == "Vendedor"
    return render(
        request,
        "clients/cliente_list.html",
        {"clientes": clientes, "es_vendedor": es_vendedor},
    )


@login_required
@require_POST
@check_user_role(allowed_roles=["Administrador", "Vendedor"])
def cliente_create_ajax(request):
    """Crea un cliente mediante AJAX desde el POS o PQRS."""
    try:
        # Intentar leer como JSON primero, si falla usar POST data
        if request.content_type == "application/json":
            data = json.loads(request.body)
            correo = data.get("email") or data.get("correo")
        else:
            # FormData desde PQRS
            data = request.POST
            correo = data.get("correo")

        documento = data.get("documento")
        if Cliente.objects.filter(documento=documento).exists():
            return JsonResponse(
                {"error": "Ya existe un cliente con este documento."}, status=400
            )

        cliente = Cliente.objects.create(
            nombres=data.get("nombres"),
            apellidos=data.get("apellidos"),
            documento=documento,
            telefono=data.get("telefono"),
            correo=correo,
        )

        return JsonResponse(
            {
                "cliente": {
                    "id": cliente.id,
                    "nombres": cliente.nombres,
                    "apellidos": cliente.apellidos,
                    "documento": cliente.documento,
                }
            }
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@login_required
@check_user_role(allowed_roles=["Administrador"])
def cliente_get_ajax(request, cliente_id):
    """Obtiene los datos de un cliente para editar."""
    try:
        cliente = get_object_or_404(Cliente, pk=cliente_id)
        return JsonResponse({
            "success": True,
            "cliente": {
                "id": cliente.id,
                "nombres": cliente.nombres,
                "apellidos": cliente.apellidos,
                "documento": cliente.documento,
                "correo": cliente.correo,
                "telefono": cliente.telefono,
                "puntos_totales": float(cliente.puntos_totales),
            }
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_POST
@check_user_role(allowed_roles=["Administrador"])
def cliente_update_ajax(request, cliente_id):
    """Actualiza los datos de un cliente."""
    try:
        cliente = get_object_or_404(Cliente, pk=cliente_id)
        data = json.loads(request.body)
        
        # Verificar documento duplicado (excluyendo el cliente actual)
        nuevo_documento = data.get("documento")
        if nuevo_documento and nuevo_documento != cliente.documento:
            if Cliente.objects.filter(documento=nuevo_documento).exclude(id=cliente_id).exists():
                return JsonResponse({"success": False, "error": "Ya existe otro cliente con este documento."}, status=400)
        
        # Verificar correo duplicado (excluyendo el cliente actual)
        nuevo_correo = data.get("correo")
        if nuevo_correo and nuevo_correo != cliente.correo:
            if Cliente.objects.filter(correo=nuevo_correo).exclude(id=cliente_id).exists():
                return JsonResponse({"success": False, "error": "Ya existe otro cliente con este correo."}, status=400)
        
        # Actualizar campos
        cliente.nombres = data.get("nombres", cliente.nombres)
        cliente.apellidos = data.get("apellidos", cliente.apellidos)
        cliente.documento = nuevo_documento or cliente.documento
        cliente.correo = nuevo_correo or cliente.correo
        cliente.telefono = data.get("telefono", cliente.telefono)
        cliente.save()
        
        return JsonResponse({
            "success": True,
            "mensaje": "Cliente actualizado exitosamente",
            "cliente": {
                "id": cliente.id,
                "nombres": cliente.nombres,
                "apellidos": cliente.apellidos,
            }
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


# ==================== PANEL Y PUNTOS ====================


@login_required
def panel_puntos(request, cliente_id):
    """Panel de puntos para un cliente específico (uso administrativo)."""
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    transacciones = PuntosFidelizacion.objects.filter(
        cliente_id=cliente_id
    ).order_by("-fecha_transaccion")[:20]
    productos = ProductoCanjeble.objects.filter(
        activo=True, stock_disponible__gt=0
    ).order_by("puntos_requeridos")
    context = {
        "cliente": cliente,
        "transacciones": transacciones,
        "puntos_totales": cliente.puntos_totales,
        "productos": productos,
    }
    return render(request, "clients/panel_puntos.html", context)


@login_required
def historial_puntos(request, cliente_id):
    """Historial completo de transacciones de puntos de un cliente."""
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    transacciones = PuntosFidelizacion.objects.filter(
        cliente_id=cliente_id
    ).order_by("-fecha_transaccion")
    context = {"cliente": cliente, "transacciones": transacciones}
    return render(request, "clients/historial_puntos.html", context)


@login_required
def mi_panel_puntos(request):
    """
    Muestra el panel de puntos del usuario logueado.
    Si el usuario logueado tiene un cliente asociado, muestra SU información.
    Si es ADMIN sin cliente asociado, redirige a la lista de clientes.
    """
    try:
        cliente = Cliente.objects.get(correo=request.user.email)
    except Cliente.DoesNotExist:
        if request.user.is_staff or request.user.is_superuser:
            return redirect("clients:cliente_list")
        return render(
            request,
            "clients/sin_cliente.html",
            {"mensaje": "No tienes un perfil de cliente asociado en el sistema."},
        )

    transacciones = PuntosFidelizacion.objects.filter(
        cliente_id=cliente.id
    ).order_by("-fecha_transaccion")[:10]
    canjes = CanjeProducto.objects.filter(cliente_id=cliente.id).order_by(
        "-fecha_canje"
    )[:5]
    productos = ProductoCanjeble.objects.filter(
        activo=True, stock_disponible__gt=0
    ).order_by("puntos_requeridos")

    context = {
        "cliente": cliente,
        "transacciones": transacciones,
        "canjes": canjes,
        "productos": productos,
        "puntos_totales": cliente.puntos_totales,
    }
    return render(request, "clients/mi_panel_puntos.html", context)


# ==================== CATÁLOGO DE PRODUCTOS ====================


@login_required
def productos_canjebles(request):
    """Catálogo de productos canjeables disponibles."""
    productos = ProductoCanjeble.objects.filter(
        activo=True, stock_disponible__gt=0
    ).order_by("puntos_requeridos")
    try:
        cliente = Cliente.objects.get(correo=request.user.email)
    except Cliente.DoesNotExist:
        cliente = None
    context = {"productos": productos, "cliente": cliente}
    return render(request, "clients/productos_canjebles.html", context)


# ==================== ADMINISTRACIÓN DE PRODUCTOS CANJEABLES ====================


@login_required
@check_user_role(allowed_roles=["Administrador"])
def administrar_productos_canjebles(request):
    """Lista y administra todos los productos canjeables."""
    productos = ProductoCanjeble.objects.all().order_by(
        "-activo", "puntos_requeridos"
    )
    context = {"productos": productos}
    return render(request, "clients/admin_productos_canjebles.html", context)


@login_required
@check_user_role(allowed_roles=["Administrador"])
@require_http_methods(["GET", "POST"])
def crear_producto_canjeble(request):
    """Crea un nuevo producto canjeable."""
    if request.method == "POST":
        try:
            with transaction.atomic():
                producto_inv_id = request.POST.get("producto_inventario")
                producto_inv = None
                stock_solicitado = int(request.POST.get("stock_disponible"))

                if producto_inv_id:
                    producto_inv = Producto.objects.select_for_update().get(
                        pk=producto_inv_id
                    )
                    if producto_inv.stock_actual < stock_solicitado:
                        raise ValueError(
                            f"Stock insuficiente en inventario. Disponible: {producto_inv.stock_actual}"
                        )

                    # Descontar del inventario
                    producto_inv.stock_actual -= stock_solicitado
                    producto_inv.save()

                    # Registrar movimiento
                    MovimientoInventario.objects.create(
                        producto=producto_inv,
                        cantidad=-stock_solicitado,
                        tipo_movimiento="SALIDA",
                        descripcion=f'Asignación a producto canjeable: {request.POST.get("nombre")}',
                    )

                ProductoCanjeble.objects.create(
                    nombre=request.POST.get("nombre"),
                    descripcion=request.POST.get("descripcion"),
                    puntos_requeridos=Decimal(request.POST.get("puntos_requeridos")),
                    stock_disponible=stock_solicitado,
                    activo=request.POST.get("activo") == "on",
                    producto_inventario=producto_inv,
                )
            messages.success(request, "Producto canjeable creado exitosamente.")
            return redirect("clients:admin_productos_canjebles")
        except Exception as e:
            messages.error(request, f"Error al crear producto: {str(e)}")

    productos_inv = Producto.objects.all().order_by("nombre")
    return render(
        request,
        "clients/crear_producto_canjeble.html",
        {"productos_inv": productos_inv},
    )


@login_required
@check_user_role(allowed_roles=["Administrador"])
@require_http_methods(["GET", "POST"])
def editar_producto_canjeble(request, producto_id):
    """Edita un producto canjeable existente."""
    producto = get_object_or_404(ProductoCanjeble, pk=producto_id)

    if request.method == "POST":
        try:
            with transaction.atomic():
                # Guardar estado anterior
                stock_anterior = producto.stock_disponible
                producto_inv_anterior = producto.producto_inventario

                # Nuevos valores
                nuevo_stock = int(request.POST.get("stock_disponible"))
                producto_inv_id = request.POST.get("producto_inventario")

                producto.nombre = request.POST.get("nombre")
                producto.descripcion = request.POST.get("descripcion")
                producto.puntos_requeridos = Decimal(
                    request.POST.get("puntos_requeridos")
                )
                producto.stock_disponible = nuevo_stock
                producto.activo = request.POST.get("activo") == "on"

                # Manejo de cambio de producto de inventario o ajuste de stock
                if producto_inv_id:
                    nuevo_producto_inv = Producto.objects.select_for_update().get(
                        pk=producto_inv_id
                    )
                    producto.producto_inventario = nuevo_producto_inv

                    if (
                        producto_inv_anterior
                        and producto_inv_anterior.id == nuevo_producto_inv.id
                    ):
                        # Mismo producto, solo ajustar diferencia de stock
                        diferencia = nuevo_stock - stock_anterior
                        if diferencia > 0:
                            if nuevo_producto_inv.stock_actual < diferencia:
                                raise ValueError(
                                    f"Stock insuficiente en inventario para el aumento. Disponible: {nuevo_producto_inv.stock_actual}"
                                )
                            nuevo_producto_inv.stock_actual -= diferencia
                            tipo = "SALIDA"
                            desc = f"Aumento de stock canjeable: {producto.nombre}"
                        else:
                            nuevo_producto_inv.stock_actual += abs(diferencia)
                            tipo = "ENTRADA"
                            desc = (
                                f"Reducción de stock canjeable: {producto.nombre}"
                            )

                        if diferencia != 0:
                            nuevo_producto_inv.save()
                            MovimientoInventario.objects.create(
                                producto=nuevo_producto_inv,
                                cantidad=(
                                    -diferencia
                                    if tipo == "SALIDA"
                                    else abs(diferencia)
                                ),
                                tipo_movimiento=tipo,
                                descripcion=desc,
                            )
                    else:
                        # Cambio de producto: devolver stock al anterior (si había) y restar al nuevo
                        if producto_inv_anterior:
                            producto_inv_anterior.stock_actual += stock_anterior
                            producto_inv_anterior.save()
                            MovimientoInventario.objects.create(
                                producto=producto_inv_anterior,
                                cantidad=stock_anterior,
                                tipo_movimiento="ENTRADA",
                                descripcion=(
                                    f"Devolución por desvinculación de canje: {producto.nombre}"
                                ),
                            )

                        # Restar del nuevo
                        if nuevo_producto_inv.stock_actual < nuevo_stock:
                            raise ValueError(
                                f"Stock insuficiente en nuevo producto de inventario. Disponible: {nuevo_producto_inv.stock_actual}"
                            )

                        nuevo_producto_inv.stock_actual -= nuevo_stock
                        nuevo_producto_inv.save()
                        MovimientoInventario.objects.create(
                            producto=nuevo_producto_inv,
                            cantidad=-nuevo_stock,
                            tipo_movimiento="SALIDA",
                            descripcion=(
                                f"Asignación a producto canjeable: {producto.nombre}"
                            ),
                        )
                else:
                    # Se desvincula el producto
                    producto.producto_inventario = None
                    if producto_inv_anterior:
                        producto_inv_anterior.stock_actual += stock_anterior
                        producto_inv_anterior.save()
                        MovimientoInventario.objects.create(
                            producto=producto_inv_anterior,
                            cantidad=stock_anterior,
                            tipo_movimiento="ENTRADA",
                            descripcion=(
                                f"Devolución por desvinculación de canje: {producto.nombre}"
                            ),
                        )

                producto.save()

            messages.success(request, "Producto actualizado exitosamente.")
            return redirect("clients:admin_productos_canjebles")
        except Exception as e:
            messages.error(request, f"Error al actualizar producto: {str(e)}")

    productos_inv = Producto.objects.all().order_by("nombre")
    context = {"producto": producto, "productos_inv": productos_inv}
    return render(request, "clients/editar_producto_canjeble.html", context)


@login_required
@check_user_role(allowed_roles=["Administrador"])
@require_POST
def eliminar_producto_canjeble(request, producto_id):
    """Desactiva un producto canjeable (soft delete)."""
    try:
        producto = get_object_or_404(ProductoCanjeble, pk=producto_id)
        producto.activo = False
        producto.save()
        return JsonResponse(
            {
                "success": True,
                "mensaje": f'Producto "{producto.nombre}" desactivado exitosamente.',
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


# ==================== CANJEAR PRODUCTO: AJAX ====================


@login_required
@require_POST
def canjear_producto(request, producto_id):
    """
    Procesa el canje de un producto.
    Soporta tanto solicitudes AJAX (JSON) como formularios estándar (POST).
    """
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest" or (
        "application/json" in request.content_type
    )

    try:
        cliente_id = None

        # Intentar obtener datos según el tipo de solicitud
        if is_ajax:
            try:
                data = json.loads(request.body)
                cliente_id = data.get("cliente_id")
            except json.JSONDecodeError:
                pass

        # Si no es AJAX o falló la lectura del JSON, intentar con POST estándar
        if not cliente_id:
            cliente_id = request.POST.get("cliente_id")

        if not cliente_id:
            raise ValueError("ID de cliente no proporcionado")

        cliente = get_object_or_404(Cliente, pk=cliente_id)
        producto = get_object_or_404(ProductoCanjeble, pk=producto_id)

        if producto.stock_disponible <= 0:
            error_msg = "Producto sin stock disponible"
            if is_ajax:
                return JsonResponse({"success": False, "error": error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect("clients:panel_puntos", cliente_id=cliente_id)

        if cliente.puntos_totales < producto.puntos_requeridos:
            error_msg = (
                f"Puntos insuficientes. Requiere {producto.puntos_requeridos} pts, "
                f"tienes {cliente.puntos_totales} pts"
            )
            if is_ajax:
                return JsonResponse({"success": False, "error": error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect("clients:panel_puntos", cliente_id=cliente_id)

        with transaction.atomic():
            # Crear el canje
            canje = CanjeProducto.objects.create(
                cliente_id=cliente.id,
                producto_id=producto.id,
                puntos_gastados=producto.puntos_requeridos,
                estado=CanjeProducto.ESTADO_PENDIENTE,
            )

            # Descontar puntos del cliente
            cliente.puntos_totales -= producto.puntos_requeridos
            cliente.save()

            # Reducir stock del producto
            producto.stock_disponible -= 1
            producto.save()

            # Registrar transacción de puntos
            PuntosFidelizacion.objects.create(
                cliente_id=cliente.id,
                tipo=PuntosFidelizacion.TIPO_CANJE,
                puntos=-producto.puntos_requeridos,
                descripcion=f"Canje de {producto.nombre} (Canje #{canje.id})",
                canje_id=canje.id,
            )

        # Respuesta exitosa
        if is_ajax:
            return JsonResponse(
                {
                    "success": True,
                    "mensaje": f"Canje realizado exitosamente. Canje #{canje.id}",
                    "canje_id": canje.id,
                    "puntos_restantes": float(cliente.puntos_totales),
                    "redirect_url": reverse("clients:detalle_canje", args=[canje.id]),
                }
            )

        messages.success(request, "¡Canje realizado exitosamente!")
        return redirect("clients:detalle_canje", canje_id=canje.id)

    except Exception as e:
        if is_ajax:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
        messages.error(request, f"Error al procesar el canje: {str(e)}")
        if "cliente_id" in locals() and cliente_id:
            return redirect("clients:panel_puntos", cliente_id=cliente_id)
        return redirect("clients:cliente_list")


# ==================== CANJE TRADICIONAL (HTML CON CONFIRMACIÓN) ====================


@login_required
@require_http_methods(["GET", "POST"])
def canjearproducto_web(request, producto_id):
    """
    Vista para canjear productos con confirmación HTML.
    """
    producto = get_object_or_404(ProductoCanjeble, pk=producto_id)

    target_cliente_id = request.GET.get("cliente_id") or request.POST.get("cliente_id")

    if target_cliente_id:
        cliente = get_object_or_404(Cliente, pk=target_cliente_id)
    else:
        try:
            cliente = Cliente.objects.get(correo=request.user.email)
        except Cliente.DoesNotExist:
            # Crear cliente de prueba para admin si no existe
            cliente = Cliente.objects.create(
                nombres=request.user.first_name or request.user.username,
                apellidos=request.user.last_name or "Admin",
                correo=request.user.email,
                documento=f"ADMIN-{request.user.id}",
                telefono="0000000000",
                puntos_totales=Decimal("10000.00"),
            )
            PuntosFidelizacion.objects.create(
                cliente=cliente,
                tipo=PuntosFidelizacion.TIPO_AJUSTE,
                puntos=Decimal("10000.00"),
                descripcion="Bono de Bienvenida (Cliente de Prueba)",
            )
            messages.success(
                request,
                "Perfil de cliente de prueba creado automáticamente con 10,000 puntos.",
            )

    # Validar que no sea el consumidor final (ID 1)
    if cliente.id == 1:
        messages.error(request, "Los consumidores finales no pueden canjear puntos.")
        if target_cliente_id:
            return redirect("clients:panel_puntos", cliente_id=target_cliente_id)
        return redirect("clients:mi_panel_puntos")

    if request.method == "GET":
        puntos_disponibles = cliente.puntos_totales
        puntos_requeridos = producto.puntos_requeridos
        puede_canjear = puntos_disponibles >= puntos_requeridos
        context = {
            "producto": producto,
            "cliente": cliente,
            "puntos_disponibles": puntos_disponibles,
            "puntos_requeridos": puntos_requeridos,
            "puede_canjear": puede_canjear,
            "diferencia": (
                puntos_requeridos - puntos_disponibles if not puede_canjear else 0
            ),
        }
        return render(request, "clients/confirmar_canje.html", context)

    # POST
    puntos_disponibles = cliente.puntos_totales
    puntos_requeridos = producto.puntos_requeridos

    # Validaciones
    if puntos_disponibles < puntos_requeridos:
        messages.error(
            request,
            f"Necesitas {puntos_requeridos} pts y tienes {puntos_disponibles}.",
        )
        return redirect(request.path)

    if producto.stock_disponible <= 0:
        messages.error(request, "Producto sin stock.")
        return redirect(request.path)

    try:
        # Transacción atómica
        with transaction.atomic():
            # 1. Descontar puntos del cliente
            cliente.puntos_totales -= puntos_requeridos
            cliente.save()

            # 2. Reducir stock del producto
            producto.stock_disponible -= 1
            producto.save()

            # 3. Crear el canje
            canje = CanjeProducto.objects.create(
                cliente=cliente,
                producto=producto,
                puntos_gastados=puntos_requeridos,
                estado=CanjeProducto.ESTADO_COMPLETADO,
            )

            # 4. Registrar transacción de puntos
            PuntosFidelizacion.objects.create(
                cliente=cliente,
                tipo=PuntosFidelizacion.TIPO_CANJE,
                puntos=-puntos_requeridos,
                descripcion=f"Canje de {producto.nombre} (Web)",
                canje=canje,
            )

        messages.success(request, "¡Canje realizado correctamente!")
        return redirect("clients:detalle_canje", canje_id=canje.id)
    except Exception as e:
        messages.error(request, f"Error en el canje: {str(e)}")
        return redirect(request.path)


# ==================== ADMINISTRACIÓN DE CANJES ====================


@login_required
@check_user_role(allowed_roles=["Administrador"])
@require_POST
def marcar_canje_entregado(request, canje_id):
    """Marca un canje como entregado."""
    try:
        canje = get_object_or_404(CanjeProducto, pk=canje_id)
        canje.estado = CanjeProducto.ESTADO_COMPLETADO
        canje.save()
        messages.success(request, f"Canje #{canje.id} marcado como entregado.")
    except Exception as e:
        messages.error(request, f"Error al actualizar canje: {str(e)}")

    # Redirigir a la página anterior o al detalle del canje
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("clients:detalle_canje", canje_id=canje_id)


# ==================== DETALLE Y CONFIRMACIÓN DE CANJE ====================


@login_required
def detalle_canje(request, canje_id):
    """
    Muestra los detalles de un canje específico con opciones para:
    - Enviar correo de confirmación
    - Volver al panel de puntos
    """
    canje = get_object_or_404(CanjeProducto, pk=canje_id)

    # Verificar permisos
    puede_ver = False

    # 1. Superusuarios y Staff de Django
    if request.user.is_superuser or request.user.is_staff:
        puede_ver = True

    # 2. Usuarios con roles administrativos
    elif (
        hasattr(request.user, "rol")
        and request.user.rol
        and request.user.rol.nombre in ["Administrador", "Vendedor"]
    ):
        puede_ver = True

    # 3. Cliente dueño del canje
    else:
        try:
            cliente = Cliente.objects.get(correo=request.user.email)
            if canje.cliente_id == cliente.id:
                puede_ver = True
        except Cliente.DoesNotExist:
            pass

    if not puede_ver:
        messages.error(request, "No tienes permiso para ver este canje.")
        return redirect("clients:mi_panel_puntos")

    context = {
        "canje": canje,
        "puede_enviar_correo": bool(canje.cliente.correo),
    }
    return render(request, "clients/detalle_canje.html", context)


@login_required
@require_POST
def enviar_correo_canje(request, canje_id):
    """Envía un correo de confirmación del canje al cliente."""
    try:
        canje = get_object_or_404(CanjeProducto, pk=canje_id)
        cliente = canje.cliente

        if not cliente.correo:
            return JsonResponse(
                {
                    "success": False,
                    "error": "El cliente no tiene correo registrado.",
                },
                status=400,
            )

        asunto = f"Confirmación de Canje #{canje.id} - La Playita"

        contexto = {
            "cliente": cliente,
            "canje": canje,
        }

        # Intentar usar un template HTML si existe
        try:
            html_message = render_to_string("clients/email_canje.html", contexto)
            mensaje = strip_tags(html_message)
        except Exception:
            # Fallback a texto plano
            mensaje = (
                f"Hola {cliente.nombres},\n\n"
                f"Tu canje ha sido procesado exitosamente.\n\n"
                f"Producto: {canje.producto.nombre}\n"
                f"Puntos gastados: {canje.puntos_gastados}\n"
                f"Fecha: {canje.fecha_canje.strftime('%d/%m/%Y')}\n"
                f"Código de canje: #{canje.id}\n\n"
                f"Gracias por ser parte de nuestro programa de fidelización.\n"
                f"Atentamente,\n"
                f"El equipo de La Playita"
            )

        from_email = getattr(
            settings,
            "DEFAULT_FROM_EMAIL",
            "Soporte La Playita <soporte.laplayita@gmail.com>",
        )

        enviados = send_mail(
            asunto,
            mensaje,
            from_email,
            [cliente.correo],
            fail_silently=False,
        )

        if enviados == 0:
            return JsonResponse(
                {
                    "success": False,
                    "error": "No se pudo enviar el correo (enviados = 0).",
                },
                status=500,
            )

        return JsonResponse({"success": True, "email": cliente.correo})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# ==================== HISTORIAL DE CANJES ====================


@login_required
def canjes_cliente(request, cliente_id):
    """Muestra el historial completo de canjes de un cliente."""
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    canjes = CanjeProducto.objects.filter(cliente_id=cliente_id).order_by(
        "-fecha_canje"
    )

    context = {"cliente": cliente, "canjes": canjes}
    return render(request, "clients/canjes_cliente.html", context)


@login_required
def mis_canjes(request):
    """Muestra el historial de canjes del usuario logueado."""
    try:
        cliente = Cliente.objects.get(correo=request.user.email)
    except Cliente.DoesNotExist:
        messages.warning(request, "No tienes un perfil de cliente asociado.")
        return redirect("clients:mi_panel_puntos")

    canjes = CanjeProducto.objects.filter(cliente_id=cliente.id).order_by(
        "-fecha_canje"
    )

    context = {"cliente": cliente, "canjes": canjes}
    return render(request, "clients/mis_canjes.html", context)


# ==================== BÚSQUEDA DE CLIENTES (AJAX) ====================


@login_required
@require_POST
@check_user_role(allowed_roles=["Administrador", "Vendedor"])
def buscar_cliente_ajax(request):
    """Busca clientes por documento o nombre (para el POS)."""
    try:
        data = json.loads(request.body)
        query = data.get("query", "").strip()

        if not query:
            return JsonResponse({"clientes": []})

        # Buscar por documento o nombre
        clientes = (
            Cliente.objects.filter(documento__icontains=query)
            | Cliente.objects.filter(nombres__icontains=query)
            | Cliente.objects.filter(apellidos__icontains=query)
        )

        clientes = clientes.order_by("nombres")[:10]  # Limitar a 10 resultados

        clientes_data = [
            {
                "id": c.id,
                "nombres": c.nombres,
                "apellidos": c.apellidos,
                "documento": c.documento,
                "telefono": c.telefono,
                "correo": c.correo,
                "puntos_totales": float(c.puntos_totales),
            }
            for c in clientes
        ]

        return JsonResponse({"clientes": clientes_data})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
