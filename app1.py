from flask import Flask, request, jsonify, send_file, send_from_directory
import pandas as pd
import joblib
from io import BytesIO
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Load the model
model = joblib.load('model_rf271.pkl')

# Serve index.html from frontend folder
@app.route('/')
def index():
    print("Inside index function")
    return send_from_directory('index.html')

# Serve CSS, JS, and other files
@app.route('/<path:path>')
def serve_files(path):
    return send_from_directory('frontend', path)


@app.route('/predict', methods=['POST'])
@cross_origin(origin='http://127.0.0.1:5500')
def predict():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        df = pd.read_csv(file)

        # Ensure proper columns
        required_columns = ['Competitor_Price',
                             'Seasonality_Price', 'Quantity', 'Demand_Index', 'Discount_Percentage']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': 'Missing required columns'}), 400
        
        # Predict
        predictions = model.predict(df[required_columns])
        df['Predicted_Price'] = predictions

        # Convert to CSV
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return send_file(output, download_name='predicted_prices.csv', as_attachment=True)
        # return jsonify(df.to_dict(orient='records'))

    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/performance', methods=['GET'])
def performance():
    try:
        metrics = {'R2 Score': 0.92, 'MAE': 50.32, 'RMSE': 72.56}
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)