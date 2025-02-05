from . import db
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3  


        

class Producto(db.Model):
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    energia = db.Column(db.Float, nullable=False)
    grasas = db.Column(db.Float, nullable=False)
    grasas_saturadas = db.Column(db.Float, nullable=False)
    carbohidratos = db.Column(db.Float, nullable=False)
    azucares = db.Column(db.Float, nullable=False)
    fibra_alimentaria = db.Column(db.Float, nullable=False)
    proteinas = db.Column(db.Float, nullable=False)
    url = db.Column(db.String(200), nullable=True)


class Comida(db.Model):
    __tablename__ = 'comida'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    detalles = db.Column(db.Text)
    url = db.Column(db.String(200))
    racion_habitual = db.Column(db.Float, default=100.0)
    comida_productos = db.relationship('ComidaProducto', backref='comida', cascade='all, delete-orphan')
    
    def calcular_calorias(self):
        calorias_totales = 0
        for comida_producto in self.comida_productos:
            producto = comida_producto.producto
            calorias_por_gramo = producto.energia
            cantidad_gramos = comida_producto.gramos
            calorias_totales += (calorias_por_gramo * cantidad_gramos) / 100
        return calorias_totales


class ComidaProducto(db.Model):
    __tablename__ = 'comida_producto'
    id = db.Column(db.Integer, primary_key=True)
    comida_id = db.Column(db.Integer, db.ForeignKey('comida.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    gramos = db.Column(db.Float, nullable=False)
    producto = db.relationship('Producto', backref=db.backref('comida_productos', lazy=True))



