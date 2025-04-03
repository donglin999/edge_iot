from flask import Flask, request, jsonify, send_file, send_from_directory

app = Flask(__name__)

@app.route('/OrderLabel', methods=['POST'])
def order_label():
    # 从请求中获取JSON数据
    data = request.get_json()

    print(f"收到请求：{data}")

    return jsonify({'message': 'successfully uploaded'}), 201

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)