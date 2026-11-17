# StockPar – Trabajo Parcial 2

Sistema web para un comercio de repuestos: maneja el catálogo con precios en USD, los convierte a pesos según la cotización del dólar y genera presupuestos que descuentan stock.

Materia: Análisis y Metodologías de Sistemas.

## Integrantes

- Martin Brown
- Facundo Castelluccio
- Emiliano Orsingher
- Zahir Pacheco

## Qué hicimos

- **HU1:** actualizar la cotización del dólar (se guarda el historial).
- **HU2:** administrar el catálogo de repuestos (alta, edición, baja y búsqueda).
- **HU3:** generar presupuestos con el total en pesos y descuento automático de stock.

Desarrollado con Python y Django (patrón MVC), con base de datos SQLite.

## Cómo ejecutarlo

Desde la carpeta `TP2`:

```bash
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Después abrir <http://127.0.0.1:8000/>. Primero cargar la cotización del dólar y después los repuestos.

Para correr los tests: `python manage.py test`
