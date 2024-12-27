# README

## Proyecto: Carga Masiva de Productos para MercadoLibre

Este proyecto permite realizar una carga masiva de productos a MercadoLibre a partir de un archivo Excel. La aplicación procesa los datos del archivo, estructura la información según los requisitos de la API de MercadoLibre y realiza la publicación de los productos.

---

## Tecnologías Utilizadas

- **FastAPI**: Framework para la construcción de la API.
- **OpenAI API**: Para formatear datos de productos y generar información compatible con MercadoLibre.
- **Pandas**: Para procesar y analizar datos del archivo Excel.
- **httpx**: Para realizar solicitudes HTTP asíncronas a la API de MercadoLibre.
- **openpyxl**: Para leer archivos Excel.
- **JSON**: Para manejar conversiones de datos.
- **python-dotenv**: Para manejar variables de entorno de manera segura.

---

## Configuración

1. **Requisitos Previos:**
   - Python 3.8 o superior.
   - Archivo Excel (.xlsx) con los datos de los productos.
   - Clave API de OpenAI.
   - Credenciales válidas para acceder a la API de MercadoLibre.

2. **Variables Modificables:**
   - `OPENAI_KEY`: Clave de API de OpenAI.
   - `IS_ATTRIBUTES_IN_ROWS`: Define si los atributos están en filas o columnas en el archivo Excel.
   - `BUYING_MODE`: Modo de compra (por defecto: `buy_it_now`).
   - `LISTING_TYPE_ID`: Tipo de listado (por defecto: `gold_special`).
   - `CLIENT_SECRET`: Client Secret configurado desde MercadoLibre Developers.
   - `CLIENT_ID`: Client ID configurado desde MercadoLibre Developers.

---

## Uso

### Endpoints Principales

#### `/process_excel_and_upload/` (POST)
- **Descripción**: Procesa un archivo Excel, genera datos compatibles con la API de MercadoLibre y publica los productos.
- **Parámetros de Entrada**:
  - `file`: Archivo Excel (.xlsx) con los datos de los productos.
- **Respuesta**:
  - Detalles de las publicaciones realizadas o errores ocurridos durante el proceso.

### Funcionalidades

1. **Validación del Archivo**:
   - Verifica que el archivo subido sea un Excel con una estructura válida.

2. **Procesamiento del Archivo Excel**:
   - Lee los datos del archivo usando `pandas` y `openpyxl`.
   - Extrae los datos de los productos dependiendo de la disposición de los atributos (filas o columnas).

3. **Formateo de Datos con OpenAI**:
   - Genera títulos y otros datos estructurados requeridos por la API de MercadoLibre usando OpenAI.

4. **Consulta de Categorías y Atributos**:
   - Obtiene la categoría principal para cada producto y los atributos necesarios de la API de MercadoLibre.

5. **Publicación en MercadoLibre**:
   - Construye el JSON final con los datos formateados.
   - Realiza un POST a la API de MercadoLibre para publicar cada producto.

---

## Estructura del Proyecto

```
project_root/
├── app.py               # Archivo principal con la API
├── token_manager.py     # Gestión de tokens de autenticación
├── requirements.txt     # Dependencias del proyecto
├── README.md            # Documentación del proyecto
```

---

## Ejemplo de Archivo Excel

El archivo Excel debe tener la siguiente estructura:

### Caso: Atributos en Columnas
```
Nombre          | Marca      | Modelo   | Precio | Stock | Imagen1          | Imagen2
Producto 1      | Marca A    | Modelo A | 1000   | 10    | url_imagen1      | url_imagen2
Producto 2      | Marca B    | Modelo B | 2000   | 5     | url_imagen3      | url_imagen4
```

### Caso: Atributos en Filas
```
Atributo      | Producto 1   | Producto 2
Nombre        | Producto A   | Producto B
Marca         | Marca A      | Marca B
Modelo        | Modelo A     | Modelo B
Precio        | 1000         | 2000
Stock         | 10           | 5
Imagen1       | url_imagen1  | url_imagen3
Imagen2       | url_imagen2  | url_imagen4
```

---

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd <NOMBRE_DEL_REPOSITORIO>
   ```

2. Crear un entorno virtual y activarlo:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Ejecutar la aplicación:
   ```bash
   uvicorn app:app --reload
   ```

---

## Consideraciones

- **Límites de OpenAI**: La generación de datos puede estar limitada por las políticas de uso de OpenAI.
- **Errores de la API de MercadoLibre**: Verifique las credenciales y los permisos necesarios para evitar errores.
- **Formato del Excel**: Asegúrese de que el archivo tenga la estructura correcta para evitar errores durante el procesamiento.

---

## Contribución

Si desea contribuir a este proyecto, envíe un pull request o reporte problemas en la sección de issues del repositorio.

---

## Licencia

Este proyecto está licenciado bajo la Licencia MIT.

