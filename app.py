from flask import Flask, request, render_template, send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# Ensure upload and processed folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Dynamic Shipping Price and Profit dictionary
SHIPPING_PRICES = {
    'THPE': 5.95,
    'DICE': 0,
    'TPSS': 7.95,
    'NABR': 10,
    'FRNE': 8.95,
    'SEWR': 9
}

PROFITS = {
    'THPE': 2,
    'DICE': 2,
    'TPSS': 2,
    'NABR': 2,
    'FRNE': 2,
    'SEWR': 2
}

def get_shipping_price_and_profit(vendor_prefix):
    """Get the shipping price and profit based on the vendor prefix."""
    shipping_price = SHIPPING_PRICES.get(vendor_prefix, 0)
    profit = PROFITS.get(vendor_prefix, 2)  # Default profit if not found
    # print("shipping - ",shipping_price)
    # print("profit -", profit)
    return shipping_price, profit

def process_file(file_path):
    """Process the uploaded file and return the path of the processed file."""
    # Load the file into a DataFrame
    df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)

    # Debug: Print actual column names to identify discrepancies
    print("Actual columns in the uploaded file:", df.columns.tolist())

    # Standardize column names by stripping spaces and converting to lowercase
    df.columns = df.columns.str.strip().str.lower()

    # Check if required columns are present
    required_columns = ['vendor prefix', 'vendor sku', 'vendor price', 'vendor qty']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns in the file: {missing_columns}")

    # Calculate selling price and quantity based on vendor prefix
    df['selling price'] = df.apply(
        lambda row: round((row['vendor price'] + get_shipping_price_and_profit(row['vendor prefix'])[0] + get_shipping_price_and_profit(row['vendor prefix'])[1]) / 0.85, 2),
        axis=1
    )

    df['quantity'] = df.apply(
        lambda row: 2 if row['vendor price'] > 5 and row['vendor qty'] > 5 else 0,
        axis=1
    )

    # Save the processed file
    output_filename = os.path.join(app.config['PROCESSED_FOLDER'], 'processed_file.xlsx')
    df.to_excel(output_filename, index=False)
    return output_filename


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    try:
        # Process the uploaded file
        processed_file_path = process_file(file_path)
        return send_file(processed_file_path, as_attachment=True)
    except ValueError as e:
        return str(e), 400
    except Exception as e:
        print("An error occurred:", e)
        return "An unexpected error occurred.", 500

if __name__ == '__main__':
    app.run(debug=True)
