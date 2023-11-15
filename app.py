from flask import Flask, render_template, request, redirect, url_for
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
    transaction_date = DateTimeField()
    filename_original = CharField()
    filename_converted = CharField()

def create_tables():
    with database:
        database.create_tables([Transaction])


ALLOWED_EXTENSIONS = {'xlsx'}
app = Flask(__name__)
app.config['XLSXPATH'] = 'static/xlsx_file'
app.config['CSVPATH'] = 'static/csv_file'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    histories = Transaction.select().order_by(Transaction.transaction_date.desc())
    return render_template("index.html", transaction_data=histories)

@app.route('/convert', methods=['POST'])
def convertFile():
    # check if the post request has the file part
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        hashName = f"{uuid.uuid4().hex}.csv"
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['XLSXPATH'], hashName))

        # Read XLSX file
        read_file = pd.read_excel(file)
        # convert XLSX file to csv and save it.
        read_file.to_csv (os.path.join(app.config['CSVPATH'], hashName),index = None,header=True)

        # insert to Transaction Table
        Transaction.create(
            transaction_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            filename_original = filename,
            filename_converted = hashName
        )

        return redirect(url_for('index'))

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)