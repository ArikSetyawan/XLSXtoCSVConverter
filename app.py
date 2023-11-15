from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from peewee import *
from werkzeug.utils import secure_filename
import os, uuid, datetime
import pandas as pd

db = 'exceltocsv.db'
database = SqliteDatabase(db)

class BaseModel(Model):
	class Meta:
		database=database

class Transaction(BaseModel):
    id = AutoField()
    visitor_ip = CharField()
    transaction_date = DateTimeField()
    filename_original = CharField()
    filename_converted = CharField()

def create_tables():
    with database:
        database.create_tables([Transaction])


ALLOWED_EXTENSIONS = {'xlsx'}
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
app.config['XLSXPATH'] = 'static/xlsx_file'
app.config['CSVPATH'] = 'static/csv_file'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def getVisitorIP():
    #  Get X-Real-IP from request.headers. if is none, then return 127.0.0.1
    return request.headers.get('X-Real-IP', '127.0.0.1').split(',')[0]

@app.route('/')
def index():
    histories = Transaction.select().where(Transaction.visitor_ip == getVisitorIP()).order_by(Transaction.transaction_date.desc()).limit(10)
    return render_template("index.html", transaction_data=histories)

@app.route('/convert', methods=['POST'])
def convertFile():
    # get visitor IP
    visitorIP = getVisitorIP()

    # check if the post request has the file part
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        hashName = uuid.uuid4().hex
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['XLSXPATH'], f"{hashName}.xlsx"))

        # Read XLSX file
        read_file = pd.read_excel(file)
        # convert XLSX file to csv and save it.
        read_file.to_csv (os.path.join(app.config['CSVPATH'], f"{hashName}.csv"),index = None,header=True)

        # insert to Transaction Table
        Transaction.create(
            visitor_ip = visitorIP,
            transaction_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            filename_original = filename,
            filename_converted = hashName
        )

        return redirect(url_for('index'))
    
@app.route('/download-excel/<filename>')
def downloadExcel(filename):
    filename = f"{filename}.xlsx"
    return send_from_directory(app.config['XLSXPATH'], filename)

@app.route('/download-csv/<filename>')
def downloadCsv(filename):
    filename = f"{filename}.csv"
    return send_from_directory(app.config['CSVPATH'], filename)


if __name__ == '__main__':
    create_tables()
    app.run(host="0.0.0.0")