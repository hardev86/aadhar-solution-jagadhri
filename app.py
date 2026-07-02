import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
DB_PATH = os.path.join(BASE_DIR, 'instance', 'portal.db')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'aadhar-portal-secret-key')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

SERVICES = {
    'aadhaar': ['New Aadhaar guidance', 'Biometric update', 'Mobile/email update', 'Address update', 'DOB/gender correction', 'Document update', 'PVC card help'],
    'pan': ['New PAN apply', 'PAN correction', 'PAN reprint', 'PAN-Aadhaar link help', 'e-PAN download'],
    'passport': ['New passport form', 'Renewal', 'Tatkal guidance', 'Appointment help', 'Police verification guidance'],
    'familyid': ['Family ID new/update', 'Member add/remove', 'Income verification help', 'Correction support'],
    'gazette': ['Name change guidance', 'Gazette notification', 'Affidavit support', 'Newspaper publication help'],
    'retire': ['Retirement form filling', 'Pension document help', 'Life certificate guidance']
}

JOB_CATEGORIES = ['Govt Job', 'Private Job', 'Admit Card', 'Result', 'Answer Key', 'Syllabus']


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    with get_db() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT, name TEXT, phone TEXT, details TEXT, created_at TEXT
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner TEXT, phone TEXT, title TEXT, property_type TEXT,
            location TEXT, price TEXT, details TEXT, photo TEXT, created_at TEXT
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, category TEXT, qualification TEXT, last_date TEXT, link TEXT, details TEXT, created_at TEXT
        )''')
        db.commit()


@app.route('/')
def index():
    with get_db() as db:
        properties = db.execute('SELECT * FROM properties ORDER BY id DESC LIMIT 3').fetchall()
        jobs = db.execute('SELECT * FROM jobs ORDER BY id DESC LIMIT 4').fetchall()
    return render_template('index.html', services=SERVICES, properties=properties, jobs=jobs)


@app.route('/services/<service_name>', methods=['GET', 'POST'])
def services(service_name):
    if service_name not in SERVICES:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        details = request.form.get('details', '').strip()
        with get_db() as db:
            db.execute('INSERT INTO enquiries(service,name,phone,details,created_at) VALUES(?,?,?,?,?)',
                       (service_name, name, phone, details, datetime.now().strftime('%d-%m-%Y %H:%M')))
            db.commit()
        flash('आपका आवेदन सेव हो गया है। हम जल्द संपर्क करेंगे।')
        return redirect(url_for('services', service_name=service_name))
    return render_template('services.html', service_name=service_name, items=SERVICES[service_name])


@app.route('/property', methods=['GET', 'POST'])
def property_page():
    if request.method == 'POST':
        photo_name = ''
        file = request.files.get('photo')
        if file and file.filename and allowed_file(file.filename):
            photo_name = datetime.now().strftime('%Y%m%d%H%M%S_') + secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_name))
        data = {k: request.form.get(k, '').strip() for k in ['owner','phone','title','property_type','location','price','details']}
        with get_db() as db:
            db.execute('''INSERT INTO properties(owner,phone,title,property_type,location,price,details,photo,created_at)
                          VALUES(?,?,?,?,?,?,?,?,?)''',
                       (data['owner'], data['phone'], data['title'], data['property_type'], data['location'], data['price'], data['details'], photo_name, datetime.now().strftime('%d-%m-%Y %H:%M')))
            db.commit()
        flash('Property portal पर add हो गई है।')
        return redirect(url_for('property_page'))
    with get_db() as db:
        properties = db.execute('SELECT * FROM properties ORDER BY id DESC').fetchall()
    return render_template('property.html', properties=properties)


@app.route('/jobs')
def jobs():
    with get_db() as db:
        job_list = db.execute('SELECT * FROM jobs ORDER BY id DESC').fetchall()
    return render_template('jobs.html', jobs=job_list, categories=JOB_CATEGORIES)
@app.route('/govt-schemes')
def govt_schemes():
    return render_template('govt_schemes.html')


@app.route('/tech-services')
def tech_services():
    return render_template('tech_services.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        with get_db() as db:
            db.execute('INSERT INTO enquiries(service,name,phone,details,created_at) VALUES(?,?,?,?,?)',
                       ('contact', request.form.get('name',''), request.form.get('phone',''), request.form.get('message',''), datetime.now().strftime('%d-%m-%Y %H:%M')))
            db.commit()
        flash('Message receive हो गया है।')
        return redirect(url_for('contact'))
    return render_template('contact.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        with get_db() as db:
            db.execute('INSERT INTO jobs(title,category,qualification,last_date,link,details,created_at) VALUES(?,?,?,?,?,?,?)',
                       (request.form.get('title',''), request.form.get('category',''), request.form.get('qualification',''), request.form.get('last_date',''), request.form.get('link',''), request.form.get('details',''), datetime.now().strftime('%d-%m-%Y %H:%M')))
            db.commit()
        flash('Job alert add हो गया।')
        return redirect(url_for('admin'))
    with get_db() as db:
        enquiries = db.execute('SELECT * FROM enquiries ORDER BY id DESC LIMIT 50').fetchall()
        properties = db.execute('SELECT * FROM properties ORDER BY id DESC LIMIT 50').fetchall()
        jobs = db.execute('SELECT * FROM jobs ORDER BY id DESC LIMIT 50').fetchall()
    return render_template('admin.html', enquiries=enquiries, properties=properties, jobs=jobs, categories=JOB_CATEGORIES)


@app.route('/uploads/<filename>')
def uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# Production hosting पर database/tables automatically create हों
init_db()

if __name__ == '__main__':
    app.run(debug=True)
