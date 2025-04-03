import json
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/SaveFile', methods=['POST'])
def upload_file():
    file = request.files['file']
    print(f"{request.form['equipment']}")
    filename = file.filename
    filepath = request.form['equipment']
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    file.save(os.path.join(filepath, filename))
    return jsonify({'message': 'File successfully uploaded', 'filename': filename}), 201

if __name__ == '__main__':
    app.run(debug=True)