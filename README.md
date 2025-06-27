# Plate Analyzer

Plate Analyzer es una aplicación de escritorio en Python que facilita el análisis interactivo de datos de microplacas (96-well). Permite cargar archivos Excel con datos crudos, definir secciones de interés, enmascarar pocillos, marcar controles negativos y generar análisis estadísticos y visualizaciones.

## Características

- Interfaz gráfica moderna construida con [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter).
- Carga de archivos `.xlsx` y parseo automático de las combinaciones **placa-ensayo**.
- Herramientas para:
  - Seleccionar / excluir pocillos con clic izquierdo.
  - Marcar controles negativos con clic derecho.
  - Definir secciones rectangulares personalizadas y asignarles nombres / niveles de gris.
  - Copiar máscaras y valores de grises entre placas y ensayos.
- Análisis estadístico por sección y generación opcional de gráficas de barras o tablas HTML.
- Persistencia de configuración (secciones, máscaras, archivos recientes, etc.) entre sesiones.

## Estructura del proyecto

```
Plate-Analyzer/
├─ data/                # Archivos de ejemplo y salidas (no versionados)
├─ src/                 # Código fuente principal
│  ├─ analysis.py       # Lógica de análisis y generación de gráficos
│  ├─ config.py         # Persistencia de configuración de usuario
│  ├─ core/             # Módulos principales (análisis, visualización, etc.)
│  ├─ models.py         # Estructuras de datos
│  ├─ modules/          # Módulos auxiliares o en desarrollo
│  ├─ parser.py         # Funciones para parsear archivos de datos
│  ├─ plate_analyzer.py # Script principal de la aplicación
│  ├─ ui/               # Interfaz gráfica de usuario
│  ├─ utils/            # Utilidades generales
│  └─ visualization.py  # Funciones de visualización de datos
└─ requirements.txt     # Dependencias de Python
```

## Requisitos

- Python >= 3.9
- Las dependencias listadas en `requirements.txt` (instalables con *pip*):

```bash
pip install -r requirements.txt
```

## Ejecución rápida

Antes de ejecutar la aplicación, asegúrate de haber instalado todas las dependencias:

```bash
pip install -r requirements.txt
```

Luego, puedes iniciar la aplicación con:

```bash
python -m src.main
```
