import urllib.parse 
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import CONNECTION_STRING


app = Flask(__name__)

# Configure Database URI: 
params = urllib.parse.quote_plus(CONNECTION_STRING)
app.config['SECRET_KEY'] = 'ebe6aecfada7f4cb575b702f62f26adb'
app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={params}"

# extensions
db = SQLAlchemy(app)

# local.settings.json
{
  "IsEncrypted": False,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "",
    "AzureSQLConnectionString": CONNECTION_STRING
  }
}