<<<<<<< HEAD
### Las 8 entidades del ERP

Registrar en papel o en la libreta. Luego transcribir a `docs/entidades_atributos.md`.

#### Entidad 1 — `Categoria`

| Atributo | Tipo Django | Restricción | Justificación |
|---|---|---|---|
| `id` | `BigAutoField` | PK, auto | Clave primaria generada |
| `nombre` | `CharField(100)` | unique, not null | Sin categorías duplicadas |
| `descripcion` | `TextField` | blank=True | Opcional — puede estar vacía |

#### Entidad 2 — `Proveedor`

| Atributo | Tipo Django | Restricción | Justificación |
|---|---|---|---|
| `id` | `BigAutoField` | PK, auto | Clave primaria generada |
| `nombre` | `CharField(150)` | not null | Nombre comercial del proveedor |
| `contacto` | `CharField(100)` | blank=True | Persona de contacto (opcional) |
| `correo` | `EmailField` | unique, not null | Identificador único de contacto |
| `telefono` | `CharField(20)` | blank=True | Formato libre por región |
| `activo` | `BooleanField` | default=True | Soft-delete: desactivar sin borrar |
| `creado` | `DateTimeField` | auto_now_add | Trazabilidad automática |

#### Entidad 3 — `Cliente`

| Atributo | Tipo Django | Restricción | Justificación |
|---|---|---|---|
| `id` | `BigAutoField` | PK, auto | Clave primaria generada |
| `nombre` | `CharField(150)` | not null | Nombre completo o razón social |
| `correo` | `EmailField` | unique, not null | Login y contacto principal |
| `telefono` | `CharField(20)` | blank=True | Opcional — no todos lo tienen |
| `activo` | `BooleanField` | default=True | Soft-delete |
| `creado` | `DateTimeField` | auto_now_add | Trazabilidad |

#### Entidad 4 — `Producto`

| Atributo | Tipo Django | Restricción | Justificación |
|---|---|---|---|
| `id` | `BigAutoField` | PK, auto | |
| `nombre` | `CharField(200)` | not null | Nombre del artículo |
| `precio` | `DecimalField(10,2)` | MinValueValidator(0) | Precio ≥ 0 siempre |
| `stock` | `IntegerField` | default=0, MinValue(0) | Stock no puede ser negativo |
| `categoria` | `ForeignKey(Categoria)` | PROTECT | Ver decisión D-01 |
| `proveedor` | `ForeignKey(Proveedor)` | SET_NULL, null=True | Ver decisión D-02 |
| `activo` | `BooleanField` | default=True | Soft-delete |
| `creado` | `DateTimeField` | auto_now_add | Trazabilidad |

#### Entidad 5 — `Venta`

| Atributo | Tipo Django | Restricción | Justificación |
|---|---|---|---|
| `id` | `BigAutoField` | PK, auto | |
| `cliente` | `ForeignKey(Cliente)` | PROTECT | Ver decisión D-03 |
| `fecha` | `DateTimeField` | auto_now_add | Fecha de creación inmutable |
| `total` | **Propiedad calculada** | NO es campo de BD | Ver decisión D-04 |

#### Entidad 6 — `DetalleVenta`

| Atributo | Tipo Django | Restricción | Justificación |
|---|---|---|---|
| `id` | `BigAutoField` | PK, auto | |
| `venta` | `ForeignKey(Venta)` | CASCADE | Si se borra Venta → borra detalles |
| `producto` | `ForeignKey(Producto)` | PROTECT | Ver decisión D-05 |
| `cantidad` | `PositiveIntegerField` | ≥ 1 | No puede haber 0 unidades |
| `precio_unitario` | `DecimalField(10,2)` | not null | Ver decisión D-06 |

#### Entidad 7 — `Pedido` (e-commerce, implementado en Espiral 5)

| Atributo | Tipo Django | Restricción | Justificación |
|---|---|---|---|
| `id` | `BigAutoField` | PK, auto | |
| `numero_pedido` | `CharField(20)` | unique | Código legible: `PED-2025-0001` |
| `cliente` | `ForeignKey(Cliente)` | PROTECT | Pedido siempre tiene cliente |
| `estado` | `CharField(20)` | choices | pendiente/pagado/enviado/cancelado |
| `fecha_pedido` | `DateTimeField` | auto_now_add | Cuándo se creó |
| `fecha_entrega` | `DateField` | null=True | Cuándo se entregó (opcional) |
| `total_pagado` | `DecimalField(10,2)` | null=True | Registrado al procesar pago |

#### Entidad 8 — `ConfiguracionERP` (singleton del sistema)

| Atributo | Tipo Django | Restricción | Justificación |
|---|---|---|---|
| `id` | `BigAutoField` | PK, auto | |
| `nombre_empresa` | `CharField(200)` | not null | Aparece en facturas y PDF |
| `rfc` | `CharField(13)` | blank=True | RFC del negocio (México) |
| `moneda` | `CharField(3)` | default='MXN' | ISO 4217 |
| `iva_porcentaje` | `DecimalField(5,2)` | default=16.00 | IVA México estándar |
| `logo` | `ImageField` | null=True, blank=True | Logo para facturas PDF |
=======
# Decisiones de Diseño — ERP Django
## Espiral 2 · Modelo Entidad-Relación

---

### D-01: Producto → Categoria usa on_delete=PROTECT

**Decisión:** No permitir borrar una categoría si tiene productos asociados.

**Alternativas consideradas:**
- `CASCADE`: borraría todos los productos de esa categoría (peligroso)
- `SET_NULL`: dejaría productos sin categoría (viola integridad de negocio)

**Consecuencia:** Para borrar una categoría, primero reasignar sus productos.
Esto es correcto: un ERP no debe perder histórico de productos.

---

### D-02: Producto → Proveedor usa on_delete=SET_NULL, null=True

**Decisión:** Un producto puede existir sin proveedor asignado.

**Justificación:** Productos fabricados internamente o de proveedor desconocido.
Al borrar un proveedor, los productos no desaparecen; quedan sin proveedor.

---

### D-03: Venta → Cliente usa on_delete=PROTECT

**Decisión:** No borrar un cliente con historial de ventas.

**Justificación legal:** El historial de ventas es un registro contable.
Borrar el cliente implicaría borrar evidencia fiscal.
Usar `activo=False` para "dar de baja" sin borrar datos.

---

### D-04: Venta.total es propiedad calculada (NO campo de BD)

**Decisión:** `total` se calcula en tiempo de ejecución, no se almacena.

```python
@property
def total(self):
    return sum(d.subtotal for d in self.detalles.all())
>>>>>>> 887a20c10a2701be1ada22a52c82e7142859dab9
