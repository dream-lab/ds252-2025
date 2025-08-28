from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/hello', methods=['POST'])
def hello():
    data = request.get_json()
    name = data.get("name", "World")
    return jsonify(message=f"Hello, {name}!")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
