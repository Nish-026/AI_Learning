from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "NISHTHA"
app.config[
    "MONGO_URI"
] = "mongodb+srv://nishtha:nish@cluster0.ewtdbs6.mongodb.net/"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


@app.route("/")
def hello_world():
    return "Hello"


@app.route("/signup", methods=["POST"])
def signup():
    name = request.json["name"]
    email = request.json["email"]
    password = request.json["password"]

    user_exists = mongo.db.users.find_one({"email": email}) is not None
    if user_exists:
        return jsonify({"error": "Email already exists"}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = {
        "name": name,
        "email": email,
        "password": hashed_password,
        "role": "user",
    }
    mongo.db.users.insert_one(new_user)

    return jsonify({"message": "Registration successful"})


@app.route("/login", methods=["POST"])
def login_user():
    email = request.json["email"]
    password = request.json["password"]

    user = mongo.db.users.find_one({"email": email})
    if user is None:
        return jsonify({"error": "Unauthorized Access"}), 401

    if not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"error": "Unauthorized"}), 401
    user_role = user.get("role") if user and "role" in user else "user"
    access_token = create_access_token(identity=str(user["_id"]))
    return jsonify({"token": access_token,"role":user_role})


@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    return jsonify({"message": "Access granted", "user_id": current_user_id})


@app.route("/menu", methods=["GET"])
def get_menu():
    menu = mongo.db.menu.find()
    menu_list = []
    for dish in menu:
        menu_list.append(
            {
                "dish_id": str(dish["_id"]),
                "dish_name": dish["dish_name"],
                "img": dish["img"],
                "description": dish["description"],
                "price": dish["price"],
                "stock": dish["stock"],
            }
        )

    return jsonify({"menu": menu_list})


@app.route("/add_dish", methods=["POST"])
@jwt_required()
def add_dish():
    if not request.is_json:
        return jsonify({"error": "Invalid JSON"}), 400

    dish_name = request.json.get("dish_name")
    price = request.json.get("price")
    img = request.json.get("img")
    description = request.json.get("description")
    stock = request.json.get("stock")
    new_dish = {
        "dish_name": dish_name,
        "img": img,
        "description": description,
        "price": price,
        "stock": stock,
    }
    mongo.db.menu.insert_one(new_dish)
    return jsonify({"message": "Dish added successfully"})


@app.route("/remove_dish/<dish_id>", methods=["DELETE"])
@jwt_required()
def remove_dish(dish_id):
    result = mongo.db.menu.delete_one({"_id": ObjectId(dish_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Dish not found"}), 404

    return jsonify({"message": "Dish removed"})


@app.route("/update_dish/<dish_id>", methods=["PATCH"])
@jwt_required()
def update_dish(dish_id):
    dish_name = request.json.get("dish_name")
    img = request.json.get("img")
    description = request.json.get("description")
    price = request.json.get("price")
    stock = request.json.get("stock")

    dish = mongo.db.menu.find_one({"_id": ObjectId(dish_id)})
    if not dish:
        return jsonify({"error": "Dish not found"}), 404

    if dish_name is not None:
        dish["dish_name"] = dish_name
    if img is not None:
        dish["img"] = img
    if description is not None:
        dish["description"] = description
    if price is not None:
        dish["price"] = price
    if stock is not None:
        dish["stock"] = stock
    # Save the updated dish
    mongo.db.menu.update_one({"_id": ObjectId(dish_id)}, {"$set": dish})
    return jsonify({"message": "Dish updated"})


@app.route("/order", methods=["POST"])
@jwt_required()
def place_order():
    user_id = get_jwt_identity()
    order_dishes = request.json.get("order_dishes")
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        return jsonify({"error": "User not found"}), 404
    total_price = 0
    order_items = []
    # Check if all dishes exist and have sufficient stock
    for dish in order_dishes:
        dish_id = dish.get("dish_id")
        quantity = dish.get("quantity")
        dish_obj = mongo.db.menu.find_one({"_id": ObjectId(dish_id)})
        if dish_obj is None:
            return jsonify({"error": "Dish not found"}), 404

        if dish_obj["stock"] < quantity:
            return jsonify({"error": "Insufficient stock for a dish"}), 400

        dish_price = dish_obj["price"]
        item_total_price = dish_price * quantity

        order_item = {
            "dish_id": dish_id,
            "quantity": quantity,
            "total_price": item_total_price,
        }
        order_items.append(order_item)
        total_price += item_total_price
    # Create the order
    new_order = {
        "user": user_id,
        "order_items": order_items,
        "total_price": total_price,
        "status": "Pending",
    }
    mongo.db.orders.insert_one(new_order)
    for dish in order_dishes:
        dish_id = dish.get("dish_id")
        quantity = dish.get("quantity")
        mongo.db.menu.update_one(
            {"_id": ObjectId(dish_id)}, {"$inc": {"stock": -quantity}}
        )

    return jsonify({"message": "Order placed successfully"})


@app.route("/update_order/<order_id>", methods=["PATCH"])
def update_order(order_id):
    order = mongo.db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        return jsonify({"error": "Order not found"}), 404
    if "status" in request.json:
        order["status"] = request.json["status"]
    if "total_price" in request.json:
        order["total_price"] = request.json["total_price"]
    if "order_dishes" in request.json:
        order["order_dishes"] = request.json["order_dishes"]
    mongo.db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": order})
    return jsonify({"message": "Order updated successfully"})


@app.route("/order_history", methods=["GET"])
@jwt_required()
def order_history():
    current_user_id = get_jwt_identity()
    orders = mongo.db.orders.find({"user": current_user_id})
    order_history = []
    for order in orders:
        order_items = order.get("order_items", [])
        order_history.append(
            {
                "order_id": str(order["_id"]),
                "total_price": order["total_price"],
                "order_items": order_items,
                "status": order["status"],
            }
        )
    return jsonify({"order_history": order_history})


@app.route("/all_orders", methods=["GET"])
@jwt_required()
def all_orders():
    current_user = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(current_user)})
    if user["role"] != "admin":
        return jsonify({"error": "Access denied"}), 403

    status = request.args.get("status", "all")

    if status == "all":
        orders = list(mongo.db.orders.find())
    else:
        orders = list(mongo.db.orders.find({"status": status}))

    formatted_orders = []
    for order in orders:
        formatted_order = {
            "order_id": str(order["_id"]),
            "user_id": str(order.get("user", "")),  # Use 'user' instead of 'user_id'
            "dishes": [item["dish_id"] for item in order.get("order_items", [])],
            "total_price": order.get("total_price", 0),
            "status": order.get("status", "")
        }
        formatted_orders.append(formatted_order)

    return jsonify({"orders": formatted_orders})



if __name__ == "__main__":
    app.run(debug=True)