import datetime
from flask import Flask, request, jsonify
from fitparse import FitFile

app = Flask(__name__)

def parse_fit_file(file):
    fitfile = FitFile(file)
    data = []
    
    for record in fitfile.get_messages():
        record_data = {}
        
        for field in record:
            value = field.value
            # Convert datetime.time objects to string
            if isinstance(value, (list, tuple)):  
                # If it's a list, convert all time values inside
                value = [v.isoformat() if isinstance(v, datetime.time) else v for v in value]
            elif isinstance(value, datetime.time):
                value = value.isoformat()
            
            record_data[field.name] = value
        
        data.append(record_data)

    return data


@app.route('/convert', methods=['POST'])
def convert_fit():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        json_data = parse_fit_file(file)
        return jsonify(json_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

