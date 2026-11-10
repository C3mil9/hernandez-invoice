"""Column headings and status labels for English and Spanish CSV exports."""

HEADINGS = {
    'en': {
        'clients': ['Name', 'Store', 'Email', 'Phone', 'Address', 'Notes', 'Archived'],
        'products': ['Product', 'SKU', 'Price', 'Description', 'Archived'],
        'sales': ['Invoice', 'Invoice date', 'Due date', 'Client', 'Store', 'Status', 'Subtotal', 'Tax', 'Shipping', 'Total'],
        'invoice-items': ['Invoice', 'Invoice date', 'Client', 'Status', 'Item', 'SKU', 'Quantity', 'Unit price', 'Line total'],
    },
    'es': {
        'clients': ['Nombre', 'Tienda', 'Correo electrónico', 'Teléfono', 'Dirección', 'Notas', 'Archivado'],
        'products': ['Producto', 'SKU', 'Precio', 'Descripción', 'Archivado'],
        'sales': ['Factura', 'Fecha de factura', 'Fecha de vencimiento', 'Cliente', 'Tienda', 'Estado', 'Subtotal', 'Impuesto', 'Envío', 'Total'],
        'invoice-items': ['Factura', 'Fecha de factura', 'Cliente', 'Estado', 'Artículo', 'SKU', 'Cantidad', 'Precio unitario', 'Importe'],
    },
}

STATUSES = {
    'en': {'Paid': 'Paid', 'Unpaid': 'Unpaid', 'Void': 'Void'},
    'es': {'Paid': 'Pagada', 'Unpaid': 'Pendiente', 'Void': 'Anulada'},
}


def archived_text(archived, language):
    return ('Sí' if archived else 'No') if language == 'es' else ('Yes' if archived else 'No')
