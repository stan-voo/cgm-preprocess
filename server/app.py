from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
import pandas as pd
import os
import datetime as dt
import re

app = Flask(__name__)
CORS(app)

import pandas as pd
import datetime as dt
import re

def join_notes(series):
    """Function to join notes, handling NaN values."""
    return ' '.join(series.dropna())

def find_nearest_glucose(timestamp, df):
    """Function to find the nearest glucose reading for notes within a ±2.5-minute window."""
    time_diff = df['Device Timestamp'] - timestamp
    mask = abs(time_diff) <= dt.timedelta(minutes=2.5)
    if mask.any():
        return df.loc[mask, 'Glucose Combined'].iloc[0]
    return None

def process_glucose_data(input_path, output_path):
    # Load CSV into DataFrame
    df = pd.read_csv(input_path, skiprows=1)

    # Convert 'Device Timestamp' to datetime format
    df['Device Timestamp'] = pd.to_datetime(df['Device Timestamp'], dayfirst=True)

    # Group by the 'Device Timestamp' column and aggregate
    grouped = df.groupby('Device Timestamp').agg({
        'Historic Glucose mg/dL': 'first',
        'Scan Glucose mg/dL': 'first',
        'Notes': join_notes
    }).reset_index()

    # Create 'Glucose Combined' column
    grouped['Glucose Combined'] = grouped[['Historic Glucose mg/dL', 'Scan Glucose mg/dL']].max(axis=1)

    # Match notes to glucose readings and find nearest glucose for notes without exact match
    notes_without_glucose = grouped['Notes'].notna() & grouped['Glucose Combined'].isna()
    grouped.loc[notes_without_glucose, 'Glucose Combined'] = grouped.loc[notes_without_glucose, 'Device Timestamp'].apply(lambda x: find_nearest_glucose(x, grouped))

    # Merge the grouped data with the original DataFrame to retain all columns
    merged_df = pd.merge(df, grouped[['Device Timestamp', 'Glucose Combined']], on='Device Timestamp', how='right')

    # Aggregate the data to remove duplicates and retain all original columns
    aggregated_full_df = merged_df.groupby('Device Timestamp').first().reset_index()

    # Identify rows where the 'Notes' column contains only spaces (and no other columns have relevant data)
    blank_note_mask = aggregated_full_df['Notes'].str.contains(r'^\s+$', regex=True, na=False)
    columns_to_check = aggregated_full_df.columns.difference(['Device Timestamp', 'Notes'])
    other_data_present = aggregated_full_df[columns_to_check].notna().any(axis=1)
    removal_mask = blank_note_mask & ~other_data_present
    cleaned_df = aggregated_full_df[~removal_mask]

      # Remove rows where 'Glucose Combined' is NaN
    cleaned_df = aggregated_full_df[aggregated_full_df['Glucose Combined'].notna()]


    # Export the final processed data
    cleaned_df.to_csv(output_path, index=False)

# Usage
# process_glucose_data('cgm-data/input.csv', 'cgm-data/output.csv')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"})

    if file:
        filename = "input.csv"
        filepath = os.path.join(os.getcwd(), filename)
        file.save(filepath)
        
        # Call your processing function
        output_filepath = os.path.join(os.getcwd(), "output.csv")
        process_glucose_data(filepath, output_filepath)
        
        return jsonify({"success": True, "message": "File processed successfully"})

@app.route('/download', methods=['GET'])
def download_file():
    return send_from_directory(os.getcwd(), "output.csv", as_attachment=True, mimetype='text/csv')

if __name__ == '__main__':
    app.run(debug=True, port=5000)