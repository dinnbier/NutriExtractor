from flask import Flask
from flask_sqlalchemy import SQLAlchemy



# Crear una instancia de la base de datos
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    #en esta línea importamos la clase config. De esta forma le indicamos que está dentro de la carpeta
    #app con nombre config (por tanto busca un archivo "config.py")
    app.config.from_object('app.config.Config')    



    # Inicializar la base de datos
    db.init_app(app)

    # Importar las rutas
    from .routes import main
    app.register_blueprint(main)

    return app
