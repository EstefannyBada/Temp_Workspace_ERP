# Sprint 4 Retrospective — ERP Django
## Semanas W13–W15 · Espiral 5: E-commerce y Pagos

**Fecha:** ___/___/_____

## ¿Qué funcionó bien? (Keep)
1. items_snapshot en el Pedido resolvió elegantemente el problema
   de recuperar los items del carrito después de que la sesión
   fue limpiada.
2. La expresión F() garantizó que el stock nunca quede en negativo
   con múltiples webhooks simultáneos.
3. unittest.mock.patch permitió testear el webhook sin claves reales.

## ¿Qué mejorar? (Improve)
1. El template de checkout podría mostrar un loader más visible
   durante el procesamiento de pago.
2. Documentar el flujo de webhooks en el diagrama de arquitectura.

## Acción de mejora (Kaizen) para Sprint 5
> "En el Sprint 5 (Celery), crearé primero el test que verifica
>  que el correo se envía ANTES de implementar la tarea asíncrona."

## Sprint 4 — Estado final W15

| HU | Estado | Pts |
|---|---|---|
| HU-E5-01 a HU-E5-08 | ✅ Completadas | 26/26 |

## Hito M5 — ALCANZADO ✅
- Catálogo: /catalogo/ → 200 sin auth con filtros
- Carrito: agregar/remover/actualizar/vaciar funcional
- Stripe: tarjeta 4242 → pago exitoso → pedido 'pagado'
- Webhook: payment_intent.succeeded → stock decrementado
- Tests: Ran 147 tests → OK
- Fecha: __/___/_____