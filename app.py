from flask import Flask, render_template, request, jsonify, send_file
import os
import fitz  # PyMuPDF
import pandas as pd
import re

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['OUTPUT_FOLDER'] = 'output/'

@app.route('/')
def index():
    return render_template('index.html')

# Pastikan folder uploads dan output ada
for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def extract_info(text):
    try:
        invoice_number = re.search(r'(\d{2}[A-Z]+\d{6})', text).group(1)
    except AttributeError:
        invoice_number = None

    try:
        pattern = r'Bill To\s+([\s\S]+?)(?=\s*Bill To|\s*$)'
        matches = re.findall(pattern, text, re.DOTALL)
        company_pattern = r'\bPT\.\s*[A-Z][A-Za-z\s]*\b(?=\s*(?:Invoice|Please Remit To|Account Name|Ship-To|$))'
        final_result = None
        for match in matches:
            company_matches = re.findall(company_pattern, match, re.IGNORECASE)
            if company_matches:
                final_result = company_matches[-1].strip()
                break
    except AttributeError:
        final_result = None

    try:
        pattern = r'Sub\s+Acct.*?(\d{4})'
        match = re.search(pattern, text, re.DOTALL)
        sub_account = match.group(1) if match else None
    except AttributeError:
        sub_account = None

    try:
        purchase_order = re.search(r'Purchase Order\s*:?\s*(\S+)', text).group(1)
    except AttributeError:
        purchase_order = None

    try:
        item_regex = re.compile(r'(\d+)\n(\d+\.\d+)\n\d+\nYes\n[0-9,.]+\n[0-9,.]+\n(.+?)(?=\n\d+|\n\* \* \* D U P L I C A T E \* \* \*|\Z)', re.DOTALL)
        items = item_regex.findall(text)
    
        # Menggunakan cara lain untuk menyusun string tanpa f-string
        item_list = []
        for item in items:
            description = item[2].strip().replace('\n', ' ')
            item_number = item[0] + ". " + description
            item_list.append(item_number)
    
        # Menggabungkan item_list menjadi satu string
        item_number = "\n".join(item_list) if item_list else None
    except AttributeError:
        item_number = None

    try:
        invoice_date = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text).group(1)
    except AttributeError:
        invoice_date = None

    try:
        total_match = re.findall(r'Total\s*:?\s*([\d,]+)', text)
        total = total_match[-1] if total_match else None
    except AttributeError:
        total = None

    return {
        'Invoice': invoice_number,
        'Bill To': final_result,
        'Sub Acct': sub_account,
        'Purchase Order': purchase_order,
        'Description': item_number,
        'Invoice Date': invoice_date,
        'Total': total
    }

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'pdfFile' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['pdfFile']

    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if file and file.filename.endswith('.pdf'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        data_list = []
        doc = fitz.open(file_path)
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text()
            data = extract_info(text)
            data_list.append(data)

        df = pd.DataFrame(data_list)
        df_combined = df.groupby('Invoice').agg({
            'Bill To': 'first',
            'Sub Acct': 'first',
            'Purchase Order': 'first',
            'Description': lambda x: ' | '.join(filter(None, x)),
            'Invoice Date': 'first',
            'Total': 'first'
        }).reset_index()

        output_combined_path = os.path.join(app.config['OUTPUT_FOLDER'], 'output_invoice.xlsx')
        df_combined.to_excel(output_combined_path, index=False)

        return send_file(output_combined_path, as_attachment=True)

    else:
        return jsonify({'message': 'Invalid file type'}), 400

if __name__ == "__main__":
    app.run(debug=True)
