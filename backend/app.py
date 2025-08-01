from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import os
import json
import logging
from datetime import datetime
import tempfile
from werkzeug.utils import secure_filename
from fuzzywuzzy import process
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils
import io
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global variables
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'json'}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory storage (in production, use database)
mapping_data = {}
sales_data = {}
processed_data = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_file(file_path):
    """Load file based on extension"""
    if file_path.endswith('.json'):
        with open(file_path, 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    elif file_path.endswith('.csv'):
        return pd.read_csv(file_path).fillna('')
    else:
        return pd.read_excel(file_path).fillna('')

def map_sku(sku, sku_to_msku):
    """Map SKU to MSKU with fuzzy matching"""
    if pd.isna(sku):
        return "Unmapped"
    
    sku_str = str(sku).strip().upper()
    
    # Direct mapping
    if sku_str in sku_to_msku:
        return sku_to_msku[sku_str]
    
    # Fuzzy matching
    if len(sku_to_msku) > 0:
        best_match = process.extractOne(sku_str, sku_to_msku.keys())
        if best_match and best_match[1] >= 80:
            return sku_to_msku[best_match[0]]
    
    return "Unmapped"

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/upload/mapping', methods=['POST'])
def upload_mapping():
    """Upload SKU mapping file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Load and validate data
        df = load_file(file_path)
        
        # Validate required columns
        required_cols = ['SKU', 'MSKU']
        if not all(col in df.columns for col in required_cols):
            return jsonify({'error': f'Missing required columns: {required_cols}'}), 400
        
        # Store mapping data
        mapping_data['df'] = df
        mapping_data['sku_to_msku'] = dict(zip(df['SKU'], df['MSKU']))
        mapping_data['file_path'] = file_path
        
        logger.info(f"Mapping file uploaded: {filename}, {len(df)} mappings")
        
        return jsonify({
            'message': 'Mapping file uploaded successfully',
            'records': len(df),
            'columns': list(df.columns)
        })
        
    except Exception as e:
        logger.error(f"Error uploading mapping file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload/sales', methods=['POST'])
def upload_sales():
    """Upload sales data file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Load data
        df = load_file(file_path)
        
        # Store sales data
        sales_data['df'] = df
        sales_data['file_path'] = file_path
        
        logger.info(f"Sales file uploaded: {filename}, {len(df)} records")
        
        return jsonify({
            'message': 'Sales file uploaded successfully',
            'records': len(df),
            'columns': list(df.columns)
        })
        
    except Exception as e:
        logger.error(f"Error uploading sales file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/process', methods=['POST'])
def process_mapping():
    """Process SKU mapping on sales data"""
    try:
        if not mapping_data or not sales_data:
            return jsonify({'error': 'Please upload both mapping and sales files first'}), 400
        
        df = sales_data['df'].copy()
        sku_to_msku = mapping_data['sku_to_msku']
        
        # Find SKU column
        sku_column = None
        for col in df.columns:
            if 'sku' in col.lower():
                sku_column = col
                break
        
        if sku_column is None:
            return jsonify({'error': 'No SKU column found in sales data'}), 400
        
        # Apply mapping
        df['MSKU'] = df[sku_column].apply(lambda x: map_sku(x, sku_to_msku))
        
        # Calculate statistics
        total_records = len(df)
        mapped_records = len(df[df['MSKU'] != 'Unmapped'])
        unmapped_skus = df[df['MSKU'] == 'Unmapped'][sku_column].unique().tolist()
        
        # Store processed data
        processed_data['df'] = df
        processed_data['stats'] = {
            'total_records': total_records,
            'mapped_records': mapped_records,
            'mapping_rate': mapped_records / total_records * 100,
            'unmapped_skus': unmapped_skus,
            'unmapped_count': len(unmapped_skus)
        }
        
        logger.info(f"Mapping processed: {mapped_records}/{total_records} records mapped")
        
        return jsonify({
            'message': 'Mapping processed successfully',
            'stats': processed_data['stats'],
            'preview': df.head(10).to_dict('records')
        })
        
    except Exception as e:
        logger.error(f"Error processing mapping: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export_results():
    """Export processed results"""
    try:
        if not processed_data:
            return jsonify({'error': 'No processed data to export'}), 400
        
        data = request.get_json()
        format_type = data.get('format', 'csv')
        
        df = processed_data['df']
        
        if format_type == 'csv':
            # Create CSV in memory
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'processed_sales_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
        
        elif format_type == 'excel':
            # Create Excel in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Processed Data')
            output.seek(0)
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'processed_sales_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
        
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        logger.error(f"Error exporting results: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get analytics and charts"""
    try:
        if not processed_data:
            return jsonify({'error': 'No processed data available'}), 400
        
        df = processed_data['df']
        
        # Basic analytics
        analytics = {
            'total_orders': len(df),
            'unique_products': df['MSKU'].nunique(),
            'mapping_rate': processed_data['stats']['mapping_rate'],
            'top_products': df['MSKU'].value_counts().head(10).to_dict(),
            'unmapped_count': processed_data['stats']['unmapped_count']
        }
        
        # Generate charts
        charts = {}
        
        # Top products chart
        top_products = df['MSKU'].value_counts().head(10)
        fig = px.bar(
            x=top_products.values,
            y=top_products.index,
            orientation='h',
            title='Top 10 Products by Orders',
            labels={'x': 'Number of Orders', 'y': 'MSKU'}
        )
        charts['top_products'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        # Mapping status pie chart
        mapping_status = df['MSKU'].apply(lambda x: 'Mapped' if x != 'Unmapped' else 'Unmapped').value_counts()
        fig = px.pie(
            values=mapping_status.values,
            names=mapping_status.index,
            title='Mapping Status Distribution'
        )
        charts['mapping_status'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        return jsonify({
            'analytics': analytics,
            'charts': charts
        })
        
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/preview', methods=['GET'])
def get_data_preview():
    """Get preview of current data"""
    try:
        data_type = request.args.get('type', 'sales')
        
        if data_type == 'mapping' and mapping_data:
            df = mapping_data['df']
        elif data_type == 'sales' and sales_data:
            df = sales_data['df']
        elif data_type == 'processed' and processed_data:
            df = processed_data['df']
        else:
            return jsonify({'error': 'No data available'}), 400
        
        return jsonify({
            'columns': list(df.columns),
            'preview': df.head(20).to_dict('records'),
            'total_rows': len(df)
        })
        
    except Exception as e:
        logger.error(f"Error getting data preview: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 