import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, HTTPException
import openai
import pandas as pd
import httpx
import json  # Agregado para manejar conversiones de datos
from token_manager import get_valid_token

app = FastAPI()
load_dotenv()

# Configuración de la API de MercadoLibre
MERCADOLIBRE_ITEMS_API_URL = "https://api.mercadolibre.com/items"
MERCADOLIBRE_CATEGORIES_API_URL = "https://api.mercadolibre.com/sites/MLA/domain_discovery/search"
MERCADOLIBRE_CATEGORIES_ATTRIBUTES_API_URL = "https://api.mercadolibre.com/categories/"

# Variables modificables
OPENAI_KEY = os.getenv("OPENAI_KEY")
IS_ATTRIBUTES_IN_ROWS = os.getenv("IS_ATTRIBUTES_IN_ROWS") == "True"
BUYING_MODE = os.getenv("BUYING_MODE")
LISTING_TYPE_ID = os.getenv("LISTING_TYPE_ID")

# Función para validar el archivo subido
def validate_file(file: UploadFile):
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="File format not supported. Please upload an .xlsx file.")

# Función para leer el contenido del archivo Excel
def read_excel(file: UploadFile):
    contents = file.file.read()
    df = pd.read_excel(contents, engine='openpyxl')
    if df.empty or df.shape[1] < 2:
        raise HTTPException(status_code=400, detail="Estructura de Excel invalida")
    return df

def extract_products_data(df):
    products_data = []

    # Determinar si los atributos están en filas o columnas
    is_attributes_in_rows = IS_ATTRIBUTES_IN_ROWS

    if is_attributes_in_rows:
        # Caso 1: Atributos en filas, productos en columnas
        for col in df.columns[1:]:
            product_data = {}
            for index, row in df.iterrows():
                key = row[0]  # La clave está en la primera columna.
                value = row[col]  # El valor está en la columna actual.
                if pd.notnull(key) and pd.notnull(value):
                    product_data[key] = value
            products_data.append(product_data)
    else:
        # Caso 2: Atributos en columnas, productos en filas
        for index, row in df.iterrows():
            product_data = {}
            # Itera sobre las columnas desde la segunda en adelante
            for col in df.columns[1:]:
                key = col  # La clave ya es el nombre de la columna
                value = row[col]  # El valor está en la celda actual
                if pd.notnull(key) and pd.notnull(value):
                    product_data[key] = value
            products_data.append(product_data)

    return products_data

# Función para solicitar el formato de datos a OpenAI
def request_openai_formatting(product_data):
    openai.api_key = OPENAI_KEY
    response = openai.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "Eres un experto en estructurar titulos. Recibiras datos de un producto y deberas estructurarlos en el formato que se requiere para el titulo"},
            {"role": "user", "content": f"{product_data}"}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "mercado_libre_product_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "description": "Sigue la estructura: Producto + Marca + modelo del producto + algunas especificaciones que ayuden a identificar el producto.",
                            "type": "string"
                        }
                    }
                }
            }
        }
    )
    return response.choices[0].message.content

# Función para parsear la respuesta de OpenAI
def parse_openai_response(response):
    try:
        formatted_data = json.loads(response)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse formatted data from AISuite.")
    return formatted_data

# Función para consultar las categorías en MercadoLibre
async def query_mercadolibre_categories(title):
    access_token = await get_valid_token()  # Obtener el token válido
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            MERCADOLIBRE_CATEGORIES_API_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            params={"q": title}
        )
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Error al obtener categorías: {response.json()}")
    categories_data = response.json()
    if not categories_data:
        raise HTTPException(status_code=404, detail="No se encontraron categorías para el producto.")
    return categories_data[0]

# Función para consultar los atributos de una categoria en especifico en MercadoLibre
async def query_mercadolibre_attributes(category):    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            MERCADOLIBRE_CATEGORIES_ATTRIBUTES_API_URL + category + '/attributes',
        )
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Error al obtener atributos de esta categoria: {response.json()}")
    attributes_data = response.json()
    if not attributes_data:
        raise HTTPException(status_code=404, detail="No se encontraron categorías para el producto.")
    
    # Filtrar los atributos según las condiciones especificadas
    filtered_attributes = [
        attribute for attribute in attributes_data
        if attribute.get("tags", {}).get("required", False)
        or attribute.get("hierarchy") == "CHILD_PK"
        or attribute.get("tags", {}).get("conditional_required", False)
    ]
    
    return filtered_attributes

def request_openai_completion(product_data, additional_context):
    # Construir el JSON Schema dinámico
    json_schema = {
        "name": "mercado_libre_product_schema",
        "schema": {
            "type": "object",
            "properties": {
                "title": {
                    "description": "Sigue la estructura: Producto + Marca + modelo del producto + algunas especificaciones que ayuden a identificar el producto.",
                    "type": "string"
                },
                "category_id": {
                    "description": "El id de categoría del producto",
                    "type": "string"
                },
                "price": {
                    "description": "El precio del producto",
                    "type": "number"
                },
                "currency_id": {
                    "description": "Este valor siempre debe ser ARS",
                    "type": "string"
                },
                "available_quantity": {
                    "description": "Stock del producto o cantidad disponible",
                    "type": "integer"
                },
                "buying_mode": {
                    "description": "Siempre debe ser: buy_it_now",
                    "type": "string"
                },
                "condition": {
                    "description": "Siempre debe ser 'new'",
                    "type": "string"
                },
                "listing_type_id": {
                    "description": "ID del listing type del producto",
                    "type": "string"
                },
                "sale_terms": {
                    "description": "Solo la garantía del producto con los items que aquí se muestran",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "value_name": {"type": "string"}
                        },
                        "required": ["id", "value_name"]
                    }
                },
                "pictures": {
                    "description": "Imágenes del producto, pueden ser las URLs de las imágenes",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string"}
                        },
                        "required": ["source"]
                    }
                },
                "attributes": {
                    "description": "Atributos o especificaciones requeridas del producto",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "description": "ID del atributo",
                                "type": "string"
                            },
                            "value_name": {
                                "description": "Valor del atributo",
                                "type": "string"
                            }
                        },
                        "required": ["id", "value_name"]
                    }
                }
            },
            "additionalProperties": False
        }
    }

    # Construir los mensajes para la solicitud
    messages = [
        {
            "role": "system",
            "content": "Eres un experto en estructurar datos. Recibirás datos de productos y deberás estructurarlos en el formato que la API de MercadoLibre espera."
        },
        {
            "role": "user",
            "content": (
                f"Datos iniciales: {product_data}. "
                f"Los siguientes atributos son obligatorios y deben ser completados: {additional_context['attributes']}. "
                f"Devuelve un objeto JSON con el formato requerido por la API de MercadoLibre."
            )
        }
    ]

    # Hacer la solicitud a OpenAI
    response = openai.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": json_schema
        }
    )

    # Retornar la respuesta de OpenAI como objeto JSON
    return json.loads(response.choices[0].message.content)

def modify_json_field(product_json, field_to_modify, new_value):
    """
    Modifica un campo en el JSON del producto.

    Args:
        product_json (dict): JSON del producto retornado por OpenAI.
        field_to_modify (str): Nombre del campo a modificar.
        new_value: Nuevo valor para el campo.

    Returns:
        dict: JSON modificado.
    """
    if field_to_modify in product_json:
        product_json[field_to_modify] = new_value
    else:
        print(f"Campo '{field_to_modify}' no encontrado en el JSON.")
    return product_json

@app.post("/process_excel_and_upload/")
async def process_excel_and_upload(file: UploadFile):
    validate_file(file)
    df = read_excel(file)
    
    # Extraemos datos de todos los productos
    products_data = extract_products_data(df)  # Usa la nueva función para extraer todos los productos
    
    results = []  # Lista para guardar las respuestas de cada producto
    
    for product_data in products_data:
        formatted_response = request_openai_formatting(product_data)
        formatted_data = parse_openai_response(formatted_response)
        title = formatted_data.get("title")

        # Consultamos la categoría en MercadoLibre
        primary_category = await query_mercadolibre_categories(title)
        category = primary_category.get("category_id")
        
        # Obtenemos los atributos de la categoría
        attributes = await query_mercadolibre_attributes(category)

        additional_context = {
            "category_id": category,
            "attributes": attributes
        }

        # Completamos los datos con OpenAI
        completed_data = request_openai_completion(product_data, additional_context)

        # Reemplazo de variables necesarias para MercadoLibre
        completed_data = modify_json_field(completed_data, "category_id", category)
        completed_data = modify_json_field(completed_data, "title", "Item de test - No Ofertar")
        #completed_data = modify_json_field(completed_data, "title", title)
        completed_data = modify_json_field(completed_data, "currency_id", "ARS")
        completed_data = modify_json_field(completed_data, "buying_mode", BUYING_MODE)
        completed_data = modify_json_field(completed_data, "condition", "new")
        completed_data = modify_json_field(completed_data, "listing_type_id", LISTING_TYPE_ID)

        # Obtenemos el token de acceso válido
        access_token = await get_valid_token()

        # Hacemos el POST a la API de MercadoLibre para cada producto
        async with httpx.AsyncClient() as client:
            final_response = await client.post(
                MERCADOLIBRE_ITEMS_API_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                json=completed_data
            )
        if final_response.status_code == 201:
            results.append({"message": "Producto registrado con éxito", "response": final_response.json()})
        else:
            results.append({"message": "Error al registrar el producto", "error": final_response.json()})
    
    # Devolvemos la lista de resultados
    return results
