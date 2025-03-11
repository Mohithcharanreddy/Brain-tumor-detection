from flask import (Flask, render_template, request, redirect, url_for, session,
                   send_file, jsonify)
from flask_session import Session
import os
import numpy as np
import json
try:
    from PIL import Image
except ImportError as e:
    raise ImportError("PIL (Pillow) module not found. Please install Pillow with 'pip install Pillow==9.5.0'") from e
import tensorflow as tf
import cv2
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['HOSPITAL_IMAGE_FOLDER'] = 'static/hospitals/'
Session(app)

MODEL_URL = "https://drive.google.com/uc?export=download&id=1-QaHl1xmWJu_ELAw-75Q8H1gvtFcW_7I"
MODEL_PATH = 'tumor_detection_model.h5'
IMG_SIZE = (128, 128)

# Load the trained models
try:
    print(f"TensorFlow version: {tf.__version__}")
    detection_model = tf.keras.models.load_model(MODEL_PATH)
    print(f"Detection model loaded successfully. Input shape: {detection_model.input_shape}")
    print(f"Model summary:\n{detection_model.summary()}")
except AttributeError as e:
    print(f"AttributeError: TensorFlow 'keras' attribute missing. Ensure TensorFlow 2.12.0 is installed correctly. Error: {e}")
    detection_model = None
except Exception as e:
    print(f"Failed to load detection model: {e}")
    detection_model = None

if detection_model is not None:
    expected_input_shape = detection_model.input_shape
    print(f"Expected input shape of detection_model: {expected_input_shape}")
else:
    expected_input_shape = (None, 128, 128, 3)

# Load hospital data
try:
    with open('static/hospitals.json', 'r') as f:
        hospitals_data = json.load(f)
    print("Hospital data loaded successfully. Sample:", list(hospitals_data.items())[:1])
except Exception as e:
    print(f"Error loading hospitals.json: {e}")
    hospitals_data = {}

# Static dataset of states and cities in India
STATES_CITIES = {
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur"],
    "Delhi": ["New Delhi"],
    "Karnataka": ["Bengaluru", "Mysuru"]
}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['HOSPITAL_IMAGE_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username and password:
            session['username'] = username
            return redirect(url_for('upload'))
        else:
            return render_template('login.html', error="Please enter both username and password")
    return render_template('login.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'files[]' not in request.files:
            return render_template('upload.html', error="No files uploaded")
        
        if detection_model is None:
            return render_template('upload.html', error="Detection model failed to load. Please check the model file or TensorFlow installation.")

        files = request.files.getlist('files[]')
        processed_images = []
        total_files = len(files)
        processed_count = 0

        for file in files:
            if file.filename == '':
                continue
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Process image for prediction
            img = Image.open(filepath).convert('RGB')
            img = img.resize(IMG_SIZE, Image.Resampling.LANCZOS)

            img_array = np.array(img) / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            # Predict tumor presence
            try:
                prediction = detection_model.predict(img_array)[0][0]
                has_tumor = prediction > 0.5
                confidence = prediction if has_tumor else 1 - prediction
                print(f"Prediction for {filename}: {prediction}, Has Tumor: {has_tumor}, Confidence: {confidence}")
            except Exception as e:
                return render_template('upload.html', error=f"Prediction error for {filename}: {str(e)}")

            # Convert image for OpenCV processing
            img_cv = cv2.cvtColor(np.uint8(img_array[0] * 255), cv2.COLOR_RGB2BGR)
            
            if has_tumor:
                # Generate a heatmap centered on the image
                height, width = img_cv.shape[:2]
                center_x, center_y = width // 2, height // 2

                # Create a blank heatmap (grayscale)
                heatmap = np.zeros((height, width), dtype=np.float32)

                # Simulate tumor region with Gaussian distribution
                sigma = 30  # Controls the spread of the heatmap
                for y in range(height):
                    for x in range(width):
                        heatmap[y, x] = np.exp(-((x - center_x) ** 2 + (y - center_y) ** 2) / (2 * sigma ** 2))

                # Normalize heatmap to [0, 255]
                heatmap = np.uint8(255 * heatmap / np.max(heatmap))

                # Apply colormap (e.g., JET) to heatmap
                heatmap_colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

                # Overlay heatmap on original image
                alpha = 0.5  # Transparency factor
                img_cv = cv2.addWeighted(img_cv, 1 - alpha, heatmap_colored, alpha, 0.0)
                print(f"Heatmap applied to {filename}")
            else:
                print(f"No tumor detected for {filename}, skipping heatmap")

            # Save processed image
            processed_filename = f"processed_{filename}"
            processed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
            cv2.imwrite(processed_filepath, img_cv)
            processed_images.append({
                'original': filename,
                'processed': processed_filename,
                'result': 'Tumor Detected' if has_tumor else 'No Tumor',
                'confidence': f"{confidence:.2f}"
            })
            processed_count += 1
            print(f"Processed {processed_count}/{total_files} images")

        session['images'] = processed_images
        return render_template('upload.html', images=processed_images, total_processed=processed_count, total_files=total_files)
    
    return render_template('upload.html')
@app.route('/instructions')
def instructions():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('instructions.html')

@app.route('/hospitals', methods=['GET', 'POST'])
def hospitals():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    print(f"Received request: {request.method}, Form data: {request.form}")
    
    selected_state = session.get('selected_state')
    selected_city = session.get('selected_city')
    cities = STATES_CITIES.get(selected_state, []) if selected_state else []
    hospitals = []

    if request.method == 'POST':
        selected_state = request.form.get('state')
        selected_city = request.form.get('city')
        
        print(f"POST request: State={selected_state}, City={selected_city}")
        
        if selected_state:
            session['selected_state'] = selected_state
            cities = STATES_CITIES.get(selected_state, [])
        
        if selected_state and selected_city:
            session['selected_city'] = selected_city
            hospitals = hospitals_data.get(selected_state, {}).get(selected_city, [])
            print(f"Hospitals data retrieved: {hospitals}")
        else:
            session.pop('selected_city', None)
            hospitals = []

    print(f"Rendering template with state: {selected_state}, city: {selected_city}, cities: {cities}, hospitals: {hospitals}")
    return render_template('hospitals.html', states=STATES_CITIES.keys(), cities=cities, hospitals=hospitals, selected_state=selected_state, selected_city=selected_city, states_cities=STATES_CITIES)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/download_report')
def download_report():
    if 'username' not in session or 'images' not in session:
        return redirect(url_for('login'))
    
    images = session.get('images', [])
    if not images:
        return redirect(url_for('upload'))

    report_path = os.path.join(app.config['UPLOAD_FOLDER'], 'report.pdf')
    pdf = SimpleDocTemplate(report_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    try:
        title = Paragraph("Brain Tumor Detection Report", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))

        report_date = Paragraph(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
        story.append(report_date)
        story.append(Spacer(1, 12))

        table_data = [['Image', 'Result', 'Confidence']]
        for img in images:
            table_data.append([img['original'], img['result'], img['confidence']])
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

        for img in images:
            story.append(Paragraph(f"Image: {img['original']}", styles['Heading2']))
            story.append(Paragraph(f"Result: {img['result']} (Confidence: {img['confidence']})", styles['Normal']))
            
            original_path = os.path.join(app.config['UPLOAD_FOLDER'], img['original'])
            if os.path.exists(original_path):
                img_obj = ReportLabImage(original_path, width=2.5*inch, height=2.5*inch)
                story.append(img_obj)
            
            processed_path = os.path.join(app.config['UPLOAD_FOLDER'], img['processed'])
            if os.path.exists(processed_path):
                img_obj = ReportLabImage(processed_path, width=2.5*inch, height=2.5*inch)
                story.append(img_obj)
            
            story.append(Spacer(1, 12))

        pdf.build(story)
        session.pop('images', None)
        return send_file(report_path, as_attachment=True, download_name='brain_tumor_report.pdf', mimetype='application/pdf')
    except Exception as e:
        print(f"Error generating report: {e}")
        return render_template('upload.html', error=f"Failed to generate report: {str(e)}")

if __name__ == '__main__':
    import datetime
    app.run(debug=True)
