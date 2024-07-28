from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
port = 5000
app.config['SQLALCHEMY_DATABASE_URI']='postgresql+psycopg2://fer2:fer2@localhost:5432/pokemon'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

CORS(app, resources={
    r"/pokemons/*": {"origins": "http://localhost:8000"},
    r"/tipos/*": {"origins": "http://localhost:8000"},
    r"/editar/*": {"origins": "http://localhost:8000"},
    r"/movimientos/*": {"origins": "http://localhost:8000"}
})


db = SQLAlchemy(app)

# --------------------------------------// Modelos //----------------------------------------------- #
class Pokemon(db.Model):
    __tablename__ = 'pokemon'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False, unique=True)
    tipo_id1 = db.Column(db.Integer, db.ForeignKey('tipos.id'))
    tipo_id2 = db.Column(db.Integer, db.ForeignKey('tipos.id'), nullable=True) # Si no hay nada, no tiene

    

class Tipo(db.Model):
    __tablename__ = 'tipos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    debilidades = db.Column(db.String(255))
    fortalezas = db.Column(db.String(255))
    resistencias = db.Column(db.String(255), nullable=True)
    inmunidades = db.Column(db.String(255), nullable=True) # Si no hay nada, no tiene


class Movimiento(db.Model):
    __tablename__ = 'movimiento'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    tipo = db.Column(db.Integer, db.ForeignKey('tipos.id'))
    poder = db.Column(db.Integer, nullable=False)

# --------------------------------------------------------------------------------------------------- #

@app.route("/")
def home():
    return jsonify("Bienvenidos!")

@app.route("/pokemons", methods=["OPTIONS"])
def manegar_metodo_options():
    response = app.make_default_options_response()  # Asi permite URLs con 'origen desconocido' hacer el metodo POST (en este caso seria el frontend ya q este tiene localhost:8000 y en backend tiene localhost:5000)
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# Ver info de todos los Pokemones disponibles
@app.route("/pokemons/", methods=["GET"])
def data_plural():
    try: 
        pokemons = Pokemon.query.order_by(Pokemon.id).all() # Ya entra por default el "asc()"
        pokemons_info=[]
        for poke in pokemons:
            poke_info = {
               'id' : poke.id,
               'nombre' : poke.nombre,
               'tipo' : poke.tipo_id1,
               'tipo2' : poke.tipo_id2, 
            } 
            pokemons_info.append(poke_info)
        return jsonify(pokemons_info)
    except:
        return jsonify('Error: No hay Pokemones')


# Para crear tu propio Pokemon 
@app.route("/pokemons/", methods=["POST"])
def crear_pokemon():
       data = request.get_json()
       if not data:
           return jsonify('Error : No se proporcionaron datos')

       nombre_nuevo = data.get('nombre')
       tipo_id1 = data.get('tipo_id1')
       tipo_id2 = data.get('tipo_id2')
    
       # Verifica si el nombre y el tipo1 existen (los cuales son obligatorios)
       if not nombre_nuevo or not tipo_id1:
           return jsonify('Error : Nombre o tipo no encontrado')

       # Verifica si ya existe un Pokemon con ese nombre
       pokemon_existente = Pokemon.query.filter_by(nombre=nombre_nuevo).first()
       if pokemon_existente:
           return jsonify('Error : Ya existe un Pokemon con ese nombre')

       tipo1 = Tipo.query.get(tipo_id1)
       if not tipo1:
           return jsonify('Error : Tipo no encontrado')

       if tipo_id2:
           tipo2 = Tipo.query.get(tipo_id2)
           if not tipo2:
               return jsonify('Error : Tipo 2 no encontrado')
       else:
           tipo2 = None
    
       if tipo_id1 == tipo_id2:
          tipo_id2 = None

       # Obtiene el ID del ultimo Pokemon de la tabla (agregue tambien en nuevo_pokemon el (id=nuevo_id))
       ultimo_pokemon = Pokemon.query.order_by(Pokemon.id.desc()).first()  #Ordena en forma descendente y devuelve el ID con mayor valor
       if ultimo_pokemon is None:
           nuevo_id = 1
       else:
           nuevo_id = ultimo_pokemon.id + 1

       nuevo_pokemon = Pokemon(id=nuevo_id, nombre=nombre_nuevo, tipo_id1=tipo_id1, tipo_id2=tipo_id2)
       db.session.add(nuevo_pokemon)
       db.session.commit()
    
       return jsonify({'success': True, 'Mensaje': 'Pokemon creado con exito', 'Pokemon agregado': {'id': nuevo_pokemon.id, 'nombre' : nuevo_pokemon.nombre, 'tipo_id1' : nuevo_pokemon.tipo_id1, 'tipo_id2' : nuevo_pokemon.tipo_id2}})

    
# Ver info de algun Pokemon en particular
@app.route("/pokemons/<id_pokemon>", methods=["GET"])
def data_singular(id_pokemon):
    try: 
       pokemon = Pokemon.query.get(id_pokemon)
       if pokemon.tipo_id1 == pokemon.tipo_id2: 
           pokemon.tipo_id2 = None
       pokemon_info = {
           'id' : pokemon.id,
           'nombre' : pokemon.nombre,
           'tipo' : pokemon.tipo_id1, 
           'tipo2' : pokemon.tipo_id2,
       }
       return jsonify(pokemon_info)
    except:
        return jsonify('Error: Pokemon no existe.')
    
# Borra un Pokemon en particular
@app.route("/pokemons/<id_pokemon>", methods=["DELETE"])
def eliminar_pokemon(id_pokemon):
    pokemon = Pokemon.query.get(id_pokemon)
    if pokemon is None:
        return jsonify('Error : Pokemon no encontrado')
    db.session.delete(pokemon)
    db.session.commit()
    return jsonify({'Mensaje': 'Pokemon eliminado con exito'})


# Edita un Pokemon en particular 
@app.route("/pokemons/", methods=["PUT"])
def editar_pokemon():
    pokemon_data = request.json
    id_pokemon = pokemon_data.get('id')
    nombre = pokemon_data.get('nombre')
    tipo1 = pokemon_data.get('tipo_id1')
    tipo2 = pokemon_data.get('tipo_id2')

    # Verifica si el id del Pokemon existe
    if id_pokemon is None:
        return jsonify('Error : Debe proporcionar el id correcto del Pokemon')

    # Obtiene el Pokemon q se quiere editar
    pokemon = Pokemon.query.get(id_pokemon)
    if pokemon is None:
        return jsonify('Error : Pokemon no encontrado')
    
    # Verifica si el nombre nuevo coindice con el nombre antiguo
    if nombre == pokemon.nombre:
        nombre = pokemon.nombre   
    else: 
        pokemon.nombre = nombre   

    # Actualizar los datos del Pokémon
    pokemon.tipo_id1 = tipo1
    if tipo2 == tipo1:
        pokemon.tipo_id2 = None
    else:
        pokemon.tipo_id2 = tipo2 

    db.session.commit()

    return jsonify({'success': True, 'Message': 'Pokemon actualizado con exito'})

# Ver info de todos los Tipos disponibles
@app.route("/tipos/", methods=["GET"])
def data_plural_tipo():
    try: 
        tipos = Tipo.query.all()
        tipos_info= []
        for tipo in tipos:
            tip_info = {
                'id' : tipo.id,
                'nombre' : tipo.nombre,
                'debilidades' : tipo.debilidades,
                'fortalezas' : tipo.fortalezas,
                'resistencias' : tipo.resistencias,
                'inmunidades' : tipo.inmunidades
            }
            tipos_info.append(tip_info)
        return jsonify(tipos_info)
    except:
        return jsonify('Error: No hay Tipos')

# Ver info de algun Tipo en particular
@app.route("/tipos/<id_tipo>", methods=["GET"])
def data_singular_tipo(id_tipo):
    try: 
       tipo = Tipo.query.get(id_tipo)
       tipo_info = {
           'id' : tipo.id,
           'nombre' : tipo.nombre,
           'debilidades' : tipo.debilidades,
           'fortalezas' : tipo.fortalezas,
           'resistencias' : tipo.resistencias,
           'inmunidades' : tipo.inmunidades
       }
       return tipo_info
    except:
        return jsonify('Error: el Tipo no existe.')


# Ver info de todos los Movimientos disponibles
@app.route("/movimientos/", methods=["GET"])
def data_plural_movimientos():
    try: 
        movimientos = Movimiento.query.all()
        movimientos_info=[]
        for movi in movimientos:
            movi_info = {
               'id' : movi.id,
               'nombre' : movi.nombre,
               'tipo' : movi.tipo,
               'poder' : movi.poder, 
            } 
            movimientos_info.append(movi_info)
        return jsonify(movimientos_info)
    except:
        return jsonify('Error: No hay Movimientos')
    

# Ver info de algun Movimiento de algun Tipo en particular
@app.route("/tipos/<id_tipo>/movimientos", methods=["GET"])
def data_singular_movimiento(id_tipo):
    try:     
         movimientos = Movimiento.query.where(Movimiento.tipo == id_tipo).all()
         movimientos_info= []
         for movimiento in movimientos:
             movi_info = {
                'id' : movimiento.id,
                'nombre' : movimiento.nombre, 
                'tipo' : movimiento.tipo,
                'poder' : movimiento.poder 
             }
             movimientos_info.append(movi_info)
         return jsonify(movimientos_info)
    except:
         return jsonify('Error: No hay Movimientos')
    
# Crea un Movimiento de algun Tipo en particular
@app.route("/tipos/<id_tipo>/movimientos", methods=["POST"])
def crear_movimiento(id_tipo):
    try: 
        data = request.json
        poder_nuevo = data.get('poder')
        nombre_nuevo = data.get('nombre')
        # Verifica si el nombre ya existe
        if Movimiento.query.filter_by(nombre=nombre_nuevo).first() is None: 
            pass
        else:
            return jsonify(f"Error : El Movimiento'{nombre_nuevo}' ya existe. Por favor, elige otro nombre.")
        
        # Verifica si el tipo ya existo
        if Tipo.query.filter_by(id=id_tipo).first() is None: 
            return jsonify('Error : El tipo elegido no existe. Por favor, elige un tipo que exista.')
        else:
            pass
        
        # Verifica si no le falta ningun campo
        if not nombre_nuevo or not id_tipo or not poder_nuevo:
            return jsonify('Error : Nombre o tipo o poder no encontrado. Por favor, ingrese valores en cada categoria para crearlo.')
        
        # Procede a poner automaticamente el ultimo ID + 1 al nuevo Movimiento
        ultimo_movimiento = Movimiento.query.order_by(Movimiento.id.desc()).first()  
        if ultimo_movimiento is None:
           nuevo_id = 1
        else:
           nuevo_id = ultimo_movimiento.id + 1
        
        nuevo_movimiento = Movimiento(id=nuevo_id, nombre=nombre_nuevo, tipo=id_tipo, poder=poder_nuevo)
        db.session.add(nuevo_movimiento)
        db.session.commit() 
        return jsonify({'success': True, 'Movimiento agregado' : {'id': nuevo_movimiento.id, 'nombre' : nuevo_movimiento.nombre, 'tipo': nuevo_movimiento.tipo, 'poder' : nuevo_movimiento.poder}})
    except Exception:
        return jsonify('Error: No se pudo crear el Movimiento. Por favor, al asignar un tipo al Movimiento, utilize el numero ID del tipo deseado.')

# Muestra un Movimiento en particular de algun Tipo en particular
@app.route("/tipos/<id_tipo>/movimientos/<id_movimiento>", methods=["GET"])
def conseguir_movimiento(id_tipo, id_movimiento):
    verificar_tipo = Tipo.query.get(id_tipo)
    if verificar_tipo is None:
        return jsonify('Error : Tipo no encontrado')

    verificar_movimiento = Movimiento.query.filter_by(tipo=id_tipo, id=id_movimiento).first()
    if verificar_movimiento is None:
        return jsonify('Error : Movimiento no encontrado o no asociado con el Tipo correspondiente')

    movimiento_data = {
        'id': verificar_movimiento.id,
        'nombre': verificar_movimiento.nombre,
        'poder': verificar_movimiento.poder
    }

    return jsonify(movimiento_data)

# Elimina un Movimiento en particular de algun Tipo en particular
@app.route("/tipos/<id_tipo>/movimientos/<id_movimiento>", methods=["DELETE"])
def remover_movimiento_por_id(id_tipo, id_movimiento):
    verificar_tipo = Tipo.query.get(id_tipo)
    if verificar_tipo is None:
        return jsonify('Error : Tipo no encontrado')
    verificar_movimiento = Movimiento.query.filter_by(tipo=id_tipo, id=id_movimiento).first()
    if verificar_movimiento is None:
        return jsonify('Error : Movimiento no encontrado o no asociado con el Tipo correspondiente')
    
    db.session.delete(verificar_movimiento)
    db.session.commit()
    return jsonify('Movimiento borrado!')

# Elimina un Movimiento en particular de algun Tipo en particular (No implementado para el usuario, pero se puede hacer en la terminal)
@app.route("/tipos/<id_tipo>/movimientos/<id_movimiento>", methods=["PUT"])
def editar_movimiento_por_id(id_tipo, id_movimiento):
    verificar_tipo = Tipo.query.get(id_tipo)
    if verificar_tipo == None:
        return jsonify('Error : Tipo no encontrado')
    verificar_movimiento = Movimiento.query.filter_by(tipo=id_tipo, id=id_movimiento).first()
    if verificar_movimiento == None:
        return jsonify('Error : Movimiento no encontrado o no asociado con el Tipo correspondiente')
    
    data = request.json
    if 'nombre' in data:
       verificar_movimiento.nombre = data.get('nombre')
    if 'poder' in data:
       verificar_movimiento.poder = data.get('poder')
    db.session.commit()
    return jsonify('Movimiento editado con exito!' )

# Crea las tablas correspondientes si no existen!
if __name__ == '__main__':
    print('Starting server...')
    db.init_app(app)
    with app.app_context():
         db.create_all()
    app.run(host='0.0.0.0', debug=True, port=port)
    print('Started...')
    