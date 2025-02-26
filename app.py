from flask import Flask, request, jsonify
import requests
from fitparse import FitFile
import datetime
import os

app = Flask(__name__)

def parse_fit_file(file_path):
    fitfile = FitFile(file_path)
    data = []
    
    for record in fitfile.get_messages():
        record_data = {}
        for field in record:
            value = field.value
            if isinstance(value, datetime.time):
                value = value.isoformat()
            record_data[field.name] = value
        data.append(record_data)

    return data

@app.route('/convert', methods=['POST'])
def convert_fit():
    data = request.get_json()

    if "file_url" not in data:
        return jsonify({"error": "No file URL provided"}), 400

    file_url = data["file_url"]

    try:
        # Download the .fit file
        response = requests.get(file_url)
        if response.status_code != 200:
            return jsonify({"error": "Failed to download file"}), 400

        temp_file = "temp.fit"
        with open(temp_file, "wb") as f:
            f.write(response.content)

        # Process the file
        json_data = parse_fit_file(temp_file)

        # Remove temp file
        os.remove(temp_file)

        return jsonify(json_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

