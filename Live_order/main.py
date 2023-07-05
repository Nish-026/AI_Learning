from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('A client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('A client disconnected')

# Example event handler for order status updates
@socketio.on('order_status_update')
def handle_order_status_update(data):
    order_id = data['order_id']
    new_status = data['new_status']
    emit('order_status_update', {'order_id': order_id, 'new_status': new_status}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app)
