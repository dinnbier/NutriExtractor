#from flask import Blueprint, render_template
from . import db
from flask import Response, Blueprint, render_template, request, flash, redirect, url_for, send_file, send_from_directory, jsonify, session, current_app
from .models import Producto, Comida, ComidaProducto
import csv
import requests
import re


#Constantes
# Campos específicos que quieres mostrar
campos_deseados = ['Producto', 'Energía', 'Grasas', 'Grasas saturadas', 'Hidratos de carbono', 'Azúcares', 'Fibra alimentaria', 'Proteínas']

# Crear un blueprint para las rutas
main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html', is_index=True)


@main.route('/listar_productos')
def listar_productos():
    print(f"Conectando a la base de datos: {current_app.config['SQLALCHEMY_DATABASE_URI']}")

    productos = Producto.query.all()
    return render_template('listar_productos.html', is_index=False, productos=productos)
    #return render_template('listar_productos.html')



@main.route('/eliminar_producto/<int:id>', methods=['POST', 'GET'])
def eliminar_producto(id):
    producto = Producto.query.get(id)
    if producto:
        db.session.delete(producto)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Producto "{producto.nombre}" eliminado correctamente'})
    else:
        return jsonify({'success': False, 'message': 'Producto no encontrado'})
    
@main.route('/editar_producto/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    # Obtener el producto de la base de datos por ID
    producto = Producto.query.get(id)

    if not producto:
        flash('Producto no encontrado', 'error')
        return redirect(url_for('main.seccion0'))

    if request.method == 'POST':
        # Procesar el formulario de edición
        # Aquí deberías actualizar los campos del producto con los nuevos valores del formulario
        producto.nombre = request.form.get('nombre')
        producto.energia = request.form.get('energia')
        producto.grasas = request.form.get('grasas')
        producto.grasas_saturadas = request.form.get('grasas_saturadas')
        producto.carbohidratos = request.form.get('carbohidratos')
        producto.azucares = request.form.get('azucares')
        producto.fibra_alimentaria = request.form.get('fibra_alimentaria')
        producto.proteinas = request.form.get('proteinas')
        producto.url = request.form.get('url')
        # ... Actualizar otros campos ...
        
        

        db.session.commit()
        flash('Producto actualizado correctamente', 'success')
   

    # Renderizar la plantilla de edición con los datos del producto
    return render_template('editar_producto.html', producto=producto)

@main.route('/descargar_bd_csv')
def descargar_bd_csv():
    productos = Producto.query.all()
    datos_obtenidos = [{'nombre': p.nombre, 'energia': p.energia, 'grasas': p.grasas, 'grasas_saturadas': p.grasas_saturadas,
                        'carbohidratos': p.carbohidratos, 'azucares': p.azucares, 'fibra_alimentaria': p.fibra_alimentaria,
                        'proteinas': p.proteinas, 'url': p.url} for p in productos]

    # Genera el CSV
    csv_filename = generar_csv(datos_obtenidos)

    # Lee el contenido del archivo CSV
    with open(csv_filename, 'r', encoding='utf-8') as csvfile:
        csv_content = csvfile.read()

    # Crea una respuesta con el contenido del archivo CSV
    response = Response(csv_content, content_type='text/csv')
    response.headers["Content-Disposition"] = "attachment; filename=productos.csv"

    return response

def generar_csv(datos_obtenidos):
    # Asegúrate de que todos los diccionarios en datos_obtenidos tengan las mismas claves
    fieldnames = ['nombre', 'energia', 'grasas', 'grasas_saturadas', 'carbohidratos', 'azucares', 'fibra_alimentaria', 'proteinas', 'url']

    csv_filename = 'productos.csv'

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')

        # Escribir la cabecera del CSV
        writer.writeheader()

        # Escribir los datos obtenidos al CSV
        writer.writerows(datos_obtenidos)

    return csv_filename



@main.route('/comparar_datos', methods=['GET', 'POST'])
def comparar_datos():
    if request.method == 'POST':
        # Obtener las URLs del formulario
        urls = request.form.get('urls').split('\r\n')

        # Procesar las URLs y obtener los datos nutricionales
        datos_obtenidos = procesar_urls(urls)

        # Renderizar la plantilla con los datos obtenidos
        return render_template('comparacion.html', campos=campos_deseados, datos_obtenidos=datos_obtenidos, urls=urls)

    # Renderizar la plantilla inicial si no se ha enviado el formulario
    return render_template('index.html', is_index=True)



def procesar_urls(urls):
    datos_obtenidos = []

    for url in urls:
        url = url.strip()

        if url:
            try:
                informacion_nutricional = obtener_informacion_nutricional(url)
                
                # Filtrar valores nulos o indefinidos en los datos obtenidos
                informacion_nutricional = {k: v for k, v in informacion_nutricional.items() if v is not None}
                
                datos_obtenidos.append(informacion_nutricional)
                print(f"----------------Datos obtenidos para la URL {url}: {informacion_nutricional}")
            except ValueError as e:
                main.logger.error(f"Error al procesar la URL {url}: {e}")

    return datos_obtenidos


def obtener_informacion_nutricional(url):
    codigo_barras = obtener_codigo_barras(url)

    if codigo_barras:
        api_url = f"https://es.openfoodfacts.org/api/v2/product/{codigo_barras}/?fields=product_name,nutriments,nutriscore_data"

        try:
            response = requests.get(api_url)
            response.raise_for_status()  # Lanza una excepción si la respuesta es un error HTTP

            data = response.json()

            # Obtener el nombre del producto del campo "product_name"
            nombre_producto = data.get('product', {}).get('product_name', '')

            # Obtener la información nutricional del campo "nutriments"
            nutriments = data.get("product", {}).get("nutriments", {})

            # Obtener la información nutricional del campo "nutriscore_data"
            nutriscore_data = data.get("product", {}).get("nutriscore_data", {})
            
            # Verificar si el producto ya está en la BD
            en_bd = Producto.query.filter_by(url=url).first() is not None

            # Diccionario para almacenar los datos nutricionales
            datos_nutricionales = {
                'nombre': nombre_producto,
                'energia': nutriments.get('energy-kcal', ''),
                'grasas': nutriments.get('fat', ''),
                'grasas_saturadas': nutriments.get('saturated-fat', ''),
                'carbohidratos': nutriments.get('carbohydrates', ''),
                'azucares': nutriments.get('sugars', ''),
                'fibra_alimentaria': nutriments.get('fiber', ''),
                'proteinas': nutriments.get('proteins', ''),
                'url': url,
                'en_bd': en_bd,
            }

            # Completar con la información de nutriscore_data
            datos_nutricionales.update({
                'fibra_alimentaria': nutriscore_data.get('fiber', '0.0'),
                'grasas_saturadas': nutriscore_data.get('saturated_fat', '0.0'),
            })

            return datos_nutricionales
        except requests.RequestException as e:
            main.logger.error(f"Error al obtener la información nutricional: {e}")

    main.logger.error(f"La URL {url} no tiene el formato esperado.")
    # Lanza una excepción para indicar el error al procesar la URL
    raise ValueError(f"La URL {url} no tiene el formato esperado.")


def obtener_codigo_barras(url):
    match = re.search(r'/(\d+)(?:/|$)', url)
    return match.group(1) if match else None


@main.route('/guardar_producto/<path:url>', methods=['POST'])
def guardar_producto(url):
    try:
        print("URL recibida:", url)
  
        
                # Decodificar la URL si es necesario
        from urllib.parse import unquote
        url = unquote(url)
        print(f"URL decodificada: {url}")
        
        # Verificar si el producto ya está en la BD
        if not Producto.query.filter_by(url=url).first():
            # Obtener la información nutricional
            informacion_nutricional = obtener_informacion_nutricional(url)

            if informacion_nutricional:
                # Crear un nuevo objeto Producto con la información nutricional
                nuevo_producto = Producto(
                    nombre=informacion_nutricional['nombre'],
                    energia=informacion_nutricional['energia'],
                    grasas=informacion_nutricional['grasas'],
                    grasas_saturadas=informacion_nutricional['grasas_saturadas'],
                    carbohidratos=informacion_nutricional['carbohidratos'],
                    azucares=informacion_nutricional['azucares'],
                    fibra_alimentaria=informacion_nutricional['fibra_alimentaria'],
                    proteinas=informacion_nutricional['proteinas'],
                    url=informacion_nutricional['url']
                )

                # Agregar el nuevo producto a la BD y confirmar
                db.session.add(nuevo_producto)
                db.session.commit()

                # Devolver una respuesta JSON indicando que se guardó el producto
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Información nutricional no encontrada'}), 400
        else:
            return jsonify({'success': False, 'error': 'Producto ya existe en la BD'}), 400
    except Exception as e:
        print("Error general:", str(e))
        return jsonify({'success': False, 'error': str(e)}), 500
    
    
# Asumiendo que tienes una ruta llamada 'insertar_producto_manual'
@main.route('/insertar_producto_manual', methods=['GET', 'POST'])
def insertar_producto_manual():
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre = request.form.get('nombre')
        energia = request.form.get('energia')
        grasas = request.form.get('grasas')
        grasas_saturadas = request.form.get('grasas_saturadas')
        carbohidratos = request.form.get('carbohidratos')
        azucares = request.form.get('azucares')
        fibra_alimentaria = request.form.get('fibra_alimentaria')
        proteinas = request.form.get('proteinas')
        url = request.form.get('url')

        # Asignar un valor predeterminado al campo URL si no se proporciona
        if not url:
            url = "Sin Url"  # Puedes cambiar esto según tus necesidades

        # Asumiendo que tienes un modelo Producto definido
        nuevo_producto = Producto(
            nombre=nombre,
            energia=energia,
            grasas=grasas,
            grasas_saturadas=grasas_saturadas,
            carbohidratos=carbohidratos,
            azucares=azucares,
            fibra_alimentaria=fibra_alimentaria,
            proteinas=proteinas,
            url=url
        )

        # Agregar el nuevo producto a la BD y confirmar
        db.session.add(nuevo_producto)
        db.session.commit()

        # Obtener la lista de nuevos productos agregados
        nuevos_productos = [{'nombre': nuevo_producto.nombre, 'url': nuevo_producto.url}]

        # Agregar el producto en el mensaje flash
        flash(f"Producto '{nombre}' insertado correctamente. URL: {url}", 'success')
        # Renderizar la plantilla 'productos_agregados.html'
        return render_template('insertar_producto_manual.html') 

    return render_template('insertar_producto_manual.html')  # Asegúrate de tener la plantilla correspondiente


@main.route('/insertar_comida', methods=['GET', 'POST'])
def insertar_comida():
    if request.method == 'POST':
        nombre = request.form['nombre']
        detalles = request.form['detalles']
        url = request.form['url']
        racion_habitual = float(request.form['racion_habitual'])
        
         # Validaciones
        if not nombre:
            flash('El campo "Nombre" es obligatorio.', 'danger')
            return redirect(request.url)


        nueva_comida = Comida(nombre=nombre, detalles=detalles, url=url, racion_habitual=racion_habitual)
        db.session.add(nueva_comida)
        db.session.commit()
        
        # Agregar el producto en el mensaje flash
        flash(f"Comida'{nombre}' creada correctamente", 'success')
        return render_template('insertar_comida.html')

    return render_template('insertar_comida.html')