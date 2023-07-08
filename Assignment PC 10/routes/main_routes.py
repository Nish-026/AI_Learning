from flask import Blueprint

from controllers.main_controllers import (
    display_menu, take_order, add_items, update_items, delete_items, all_orders, review_orders ,user_registration , user_login
)


zomato_router = Blueprint('zomato', __name__)

zomato_router.route('/register', methods=['POST'])(user_registration)

zomato_router.route('/login', methods=['POST'])(user_login)


zomato_router.route('/menu', methods=['GET'])(display_menu)


zomato_router.route('/orders', methods=['GET'])(all_orders)


zomato_router.route('/review-orders', methods=['GET'])(review_orders)


zomato_router.route('/take-order', methods=['POST'])(take_order)


zomato_router.route('/add-items', methods=['POST'])(add_items)


zomato_router.route('/update-items/<dish_id>', methods=['PATCH'])(update_items)


zomato_router.route('/delete-items/<dish_id>', methods=['DELETE'])(delete_items)
