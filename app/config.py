import os


class Config:
    # Clave secreta para la seguridad de la aplicación
    SECRET_KEY = os.environ.get('SECRET_KEY', 'nutriCC32')
    
    # URI de la base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///datos.db')
    
    # Desactiva el seguimiento de modificaciones de SQLAlchemy para mejorar el rendimiento
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Carpeta para subir imágenes de perfiles
    UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads', 'img_profiles'))
    
    # Habilita la protección CSRF para formularios
    WTF_CSRF_ENABLED = True

    # Crea la carpeta de cargas si no existe
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
