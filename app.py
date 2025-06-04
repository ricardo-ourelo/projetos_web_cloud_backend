from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient, ASCENDING, DESCENDING
from bson import json_util
import json
import jwt
from datetime import datetime, timedelta
from functools import wraps
import bcrypt
from bson.objectid import ObjectId

app = Flask(__name__)
CORS(app)

# App Secret Key para gerar TOKEN
app.config['SECRET_KEY'] = '5eb7a0e6cfab72c11927150b95c60966b59eccc3c13b0c4ea77ff10818e76b55'

########
# MongoDB Connection
client = MongoClient(
    "mongodb+srv://orcooo2:b5aUT388wexTBPU@projeto-web-cloud.7aqx0td.mongodb.net/", 
    tls=True, 
    tlsAllowInvalidCertificates=True
)
# Database and collections
db = client["Projetos_Web_Cloud"]
users_col = db["Users"]
products_col = db["Loja_BDRP"]

########
# parse_json para garantir que os dados estejam em formato JSON
def parse_json(data):
    return json.loads(json_util.dumps(data))

########
def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'Expired': True}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        return func(*args, **kwargs)
    return decorated

########
# POST /user/register
# Registo de utilizador com hash de password
def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

@app.route('/user/register', methods=['POST'])
def register():
    dados = request.json
    username = dados.get('username')
    password = dados.get('password')
    role = dados.get('role', 'user')  # Default role is 'user'

    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400

    # Check if the username already exists
    if users_col.find_one({'username': username}):
        return jsonify({'message': 'Username already exists'}), 409

    # Set 'confirmed' based on the role
    confirmed = True if role == 'admin' else False

    # Hash the password
    pw_hash = hash_password(password)

    # Insert the user into the database
    users_col.insert_one({
        'username': username,
        'password': pw_hash,
        'role': role,
        'confirmed': confirmed
    })

    return jsonify({'message': 'User registered successfully'}), 201


########
# POST /user/login
# Criar Token após validar credenciais
@app.route('/user/login', methods=['POST'])
def login():
    dados = request.json
    username = dados.get('username')
    password = dados.get('password')
    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400
    user = users_col.find_one({'username': username})
    if not user:
        return jsonify({'message': 'User not found'}), 404
    # compara password
    if not bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    # gera token
    token = jwt.encode({
        'username': username,
        'role': user.get('role', 'user'),
        'exp': datetime.utcnow() + timedelta(minutes=90)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    return jsonify({'token': token}), 200

########
# Endpoint GET /protected/route
@app.route("/protected/route", methods=["GET"])
@token_required
def get_example():
    return jsonify({"message": "Test"}), 200

# Endpoint GET /products
@app.route('/products', methods=['GET'], strict_slashes=False)
def get_products():
    page = request.args.get('page')
    per_page = request.args.get('per_page')
    if page and per_page:
        try:
            page = int(page)
            per_page = int(per_page)
        except ValueError:
            return jsonify({'message': 'Invalid pagination parameters'}), 400
        cursor = products_col.find().sort([("id", ASCENDING)]) \
                        .skip((page - 1) * per_page) \
                        .limit(per_page)
        products = list(cursor)
    else:
        products = list(products_col.find({}, {"_id": 0}))
    return jsonify(parse_json(products)), 200

# Endpoint POST /products (protegido)
@app.route('/products', methods=['POST'])
@token_required
def add_products():
    data = request.json
    if isinstance(data, list):
        result = products_col.insert_many(data)
        ids = result.inserted_ids
    else:
        result = products_col.insert_one(data)
        ids = [result.inserted_id]
    return jsonify({
        'message': 'Products added successfully!',
        'ids': parse_json(ids)
    }), 201

# Endpoint GET /products by id 
@app.route('/products/<string:id>', methods=['GET'])
def get_product_by_id(id):
    try:
        product = products_col.find_one({'_id': ObjectId(id)})
        if not product:
            return jsonify({'message': 'Product not found'}), 404
        return jsonify(parse_json(product)), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400

# Endpoint DELETE /products by id    
@app.route('/products/<string:id>', methods=['DELETE'])
@token_required
def delete_product(id):
    try:
        result = products_col.delete_one({'_id': ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({'message': 'Product not found'}), 404
        return jsonify({'message': 'Product deleted successfully'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400

# Endpoint UPDATE /products by id 
@app.route('/products/<string:id>', methods=['PUT'])
@token_required
def update_product(id):
    data = request.json
    try:
        result = products_col.update_one({'_id': ObjectId(id)}, {'$set': data})
        if result.matched_count == 0:
            return jsonify({'message': 'Product not found'}), 404
        return jsonify({'message': 'Product updated successfully'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400

# Endpoint GET /products TOP PRODUCTS
@app.route('/products/featured', methods=['GET'])
def get_top_products():
    try:
        top_products = list(products_col.find({}, {"_id": 0})
                            .sort("popularity", DESCENDING)
                            .limit(10))
        return jsonify(parse_json(top_products)), 200
    except Exception as e:
        return jsonify({'message': 'Error fetching top products', 'error': str(e)}), 500

# Endpoint GET /products por categoria  
@app.route('/products/categories/<string:categoria>', methods=['GET'])
def get_products_by_category(categoria):
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)

    try:
        cursor = products_col.find(
            {'category': categoria}
        ).sort('id', ASCENDING).skip((page - 1) * per_page).limit(per_page)

        products = list(cursor)
        return jsonify(parse_json(products)), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 400
    
# Endpoint GET /products por preço
@app.route('/products/price', methods=['GET'])
def get_products_by_price():
    try:
        min_price = float(request.args.get('min', 0))
        max_price = float(request.args.get('max', float('inf')))
        sort_order = request.args.get('sort', 'asc').lower()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        sort = ASCENDING if sort_order == 'asc' else DESCENDING

        query = {
            'price': {
                '$gte': min_price,
                '$lte': max_price
            }
        }

        cursor = products_col.find(query).sort('price', sort) \
            .skip((page - 1) * per_page).limit(per_page)

        products = list(cursor)
        return jsonify(parse_json(products)), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 400
    
# Endpoint POST\ guardar produtos no carrinho          
cart_col = db["Carts"]


@app.route('/products/cart', methods=['POST'])
@token_required
def save_cart():
    data = request.json
    token = request.args.get('token')

    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        username = payload['username']

        if not data or 'products' not in data:
            return jsonify({'message': 'Missing cart data'}), 400

        cart_data = {
            'products': data['products'],
            'updated_at': datetime.utcnow()
        }

        # Atualiza se já existir, ou cria um novo
        result = cart_col.update_one(
            {'username': username},
            {'$set': cart_data, '$setOnInsert': {'created_at': datetime.utcnow()}},
            upsert=True
        )

        return jsonify({'message': 'Cart saved successfully'}), 200

    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401


@app.route('/products/cart', methods=['GET'])
@token_required
def get_cart():
    token = request.args.get('token')

    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        username = payload['username']

        cart = cart_col.find_one({'username': username})
        if not cart or 'products' not in cart:
            return jsonify({'message': 'Carrinho vazio', 'products': []}), 200

        products_with_details = []
        for item in cart['products']:
            product_id = item.get('product_id')
            product = products_col.find_one({'_id': ObjectId(product_id)})
            if product:
                product['_id'] = str(product['_id'])  # Converte para string
                products_with_details.append({
                    **product,
                    'quantity': item.get('quantity', 1),
                    'selectedSize': item.get('selectedSize', None)
                })

        return jsonify({'products': products_with_details}), 200

    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401

# Admin required 
# Admin required 
def admin_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            if data.get('role') != 'admin':
                return jsonify({'message': 'Admin privileges required'}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'Expired': True}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        return func(*args, **kwargs)
    return decorated


# Endpoint POST\ confirmação do user  
@app.route('/user/confirmation', methods=['POST'])
@admin_required
def confirm_user():
    data = request.json
    username = data.get('username')

    if not username:
        return jsonify({'message': 'Username is required'}), 400

    result = users_col.update_one(
        {'username': username},
        {'$set': {'confirmed': True}}
    )

    if result.matched_count == 0:
        return jsonify({'message': 'User not found'}), 404

    return jsonify({'message': f'User {username} confirmed successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)