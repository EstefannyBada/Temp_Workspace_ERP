
# Decisiones de Diseño — ERP Django
## Espiral 2 · Modelo Entidad-Relación

---

### D-01: Producto → Categoría usa `on_delete=PROTECT`

**Decisión:** No permitir borrar una categoría si tiene productos asociados.

**Alternativas consideradas:**
- `CASCADE`: borraría todos los productos de esa categoría.
- `SET_NULL`: dejaría productos sin categoría asignada.

**Consecuencia:** Para borrar una categoría, primero se deben reasignar sus productos.

**Justificación:** Se protege la integridad de los datos del ERP.

---

### D-02: Producto → Proveedor usa `on_delete=SET_NULL, null=True`

**Decisión:** Permitir que un producto exista sin un proveedor asignado.

**Justificación:** Puede haber productos fabricados internamente o con proveedor desconocido.

**Consecuencia:** Al eliminar un proveedor, los productos permanecen registrados sin proveedor asociado.

---

### D-03: Venta → Cliente usa `on_delete=PROTECT`

**Decisión:** No permitir eliminar un cliente que tenga ventas registradas.

**Justificación:** Se debe conservar el historial comercial y contable de las operaciones.

**Consecuencia:** Se recomienda desactivar al cliente mediante un campo como `activo=False` en lugar de eliminarlo.

---

### D-04: `Venta.total` es una propiedad calculada

**Decisión:** Calcular el total de una venta a partir de sus detalles.

**Implementación de referencia:**

```python
@property
def total(self):
    return sum(detalle.subtotal for detalle in self.detalles.all())
```

**Justificación:** Evita duplicar información y permite obtener el total a partir de los detalles registrados.

**Consecuencia:** El resultado depende de los detalles asociados a la venta.

---

### D-05: Uso de claves foráneas para relacionar entidades

**Decisión:** Utilizar `ForeignKey` para establecer relaciones entre las entidades del ERP.

**Justificación:** Permite relacionar productos con categorías y proveedores, así como ventas con clientes y detalles de venta.

**Alternativa considerada:** Guardar los nombres de las entidades como texto, lo que puede provocar duplicidad e inconsistencias.

**Consecuencia:** Se facilita el mantenimiento de las relaciones y la integridad referencial de los datos.
