import os
import base64
import re
from flask import render_template, redirect, url_for, flash, request, current_app, session
from app import app, db
from app.forms import SignUpForm, SignInForm
from app.models import User , TollChalan
from flask_login import login_user, logout_user, current_user, login_required
from dotenv import load_dotenv
import requests
from PIL import Image
import pytesseract
from io import BytesIO


# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Define directories for uploads and license plates
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
LICENSE_PLATES_FOLDER = os.path.join(app.root_path, 'static', 'licensePlates')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)          # Ensure 'uploads' folder exists
os.makedirs(LICENSE_PLATES_FOLDER, exist_ok=True)   # Ensure 'licensePlates' folder exists


# Load environment variables
load_dotenv()

# Get API key and model details from the environment variables
ROBOFLOW_API_KEY = os.getenv('ROBOFLOW_API_KEY')
ROBOFLOW_MODEL = os.getenv('ROBOFLOW_MODEL')

# Home route - License Plate Recognition Homepage
@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def home():
    table_data = []
    if request.method == 'POST':
        # Handle image upload
        if 'file' not in request.files:
            flash('No file part in the request', 'danger')
            return redirect(url_for('home'))

        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(url_for('home'))

        # Save uploaded image in 'uploads'
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        print(f"File saved to {file_path}")

        # Run inference on the uploaded image
        result = run_inference(file_path)
        print(f"Inference result: {result}")

        # Process predictions to preview cropped license plates without saving
        predictions = result.get('predictions', [])
        for pred in predictions:
            if pred['confidence'] > 0.5:
                # Crop the license plate and extract text
                cropped_image_path = crop_license_plate(file_path, pred)
                license_plate_text = ocr_license_plate(cropped_image_path)

                # Encode cropped image to base64 for preview
                with open(cropped_image_path, "rb") as img_file:
                    encoded_image = base64.b64encode(img_file.read()).decode('utf-8')

                # Append data for displaying in detection table
                table_data.append({
                    'license_plate_text': license_plate_text,
                    'license_plate_image': encoded_image,  # Base64 encoded for display
                    'confidence': pred.get('confidence', 'N/A'),
                    'bounding_box': {
                        'x': pred.get('x', 'N/A'),
                        'y': pred.get('y', 'N/A'),
                        'width': pred.get('width', 'N/A'),
                        'height': pred.get('height', 'N/A')
                    },
                    'cropped_image_path': cropped_image_path  # Temporary cropped image path
                })

        return render_template('home.html', table_data=table_data, chalan_data=session.get('chalan_data', []))

    # Render initial page on GET request
    return render_template('home.html', table_data=None, chalan_data=session.get('chalan_data', []))


@app.route('/confirm_match', methods=['POST'])
def confirm_match():
    # Retrieve the submitted data
    license_plate_text = request.form.get('license_plate_text')
    confidence = request.form.get('confidence')
    x_coordinate = request.form.get('x_coordinate')
    y_coordinate = request.form.get('y_coordinate')
    width = request.form.get('width')
    height = request.form.get('height')

    # Create a new TollChalan record with the submitted or edited data
    new_chalan = TollChalan(
        license_plate_text=license_plate_text,
        confidence=confidence,
        x_coordinate=x_coordinate,
        y_coordinate=y_coordinate,
        width=width,
        height=height,
        amount=300  # default amount
    )
    
    # Add and commit the new record to the database
    db.session.add(new_chalan)
    db.session.commit()

    # Retrieve the last inserted record
    last_chalan = TollChalan.query.order_by(TollChalan.id.desc()).first()

    # Store the latest record in the session
    session['chalan_data'] = [{'license_plate_text': last_chalan.license_plate_text, 'amount': last_chalan.amount}]
    
    flash("Chalan record added successfully with updated license plate text.", "success")
    return redirect(url_for('home'))



def run_inference(image_path):
    """Send image to Roboflow for license plate detection and return JSON response."""
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    response = requests.post(
        f"https://detect.roboflow.com/{ROBOFLOW_MODEL}?api_key={ROBOFLOW_API_KEY}",
        files={"file": image_data},
        data={"name": "license-plate-detection"}
    )

    return response.json() if response.status_code == 200 else {}


def crop_license_plate(image_path, bbox):
    """Crop the license plate area from the image using bounding box coordinates."""
    image = Image.open(image_path)
    left = bbox['x'] - bbox['width'] / 2
    top = bbox['y'] - bbox['height'] / 2
    right = bbox['x'] + bbox['width'] / 2
    bottom = bbox['y'] + bbox['height'] / 2
    cropped_image = image.crop((left, top, right, bottom))

    # Save the cropped image to the correct location and return its path
    temp_cropped_image_path = os.path.join(UPLOAD_FOLDER, "temp_cropped_plate.jpg")
    cropped_image.save(temp_cropped_image_path)
    return temp_cropped_image_path  # Return the path, not the Image object



def ocr_license_plate(cropped_image_path):
    """Extract text from the cropped license plate image using OCR."""
    cropped_image = Image.open(cropped_image_path)  # Open the image from path
    text = pytesseract.image_to_string(cropped_image, config='--psm 8')
    return text.strip()


# About route - Team display page
@app.route('/about')
def about():
    return render_template('about.html')  # Ensure you have 'aboutus.html' template


# Contact route - Handles contact form submission
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Handle the form data submission
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        if not name or not email or not message:
            flash('All fields are required', 'danger')
            return redirect(url_for('contact'))

        # You can add form processing logic here (e.g., send email, save to DB)
        flash(f'Thank you for your message, {name}. We will get back to you shortly.', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')


# Sign-Up route - User registration
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        # Add new user to the database
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home'))
    return render_template('signup.html', form=form)


# Sign-In route - User login
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = SignInForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            flash('Welcome back!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('signin.html', form=form)


# Login route - Handles user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = SignInForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)


# Logout route - Logs the user out
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
