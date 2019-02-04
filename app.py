from flask import Flask, render_template, request, send_file
from werkzeug import secure_filename
from geopy.geocoders import Bing
import pandas as pd
import os
import datetime
import logging

app = Flask(__name__)

class Geo():

    BING_KEY = os.environ['BING_KEY']

    def __init__(self, filename):
        self.filename = filename
        self.df = None

    def read_file(self):
        self.df = pd.read_csv(self.filename)
        #print(df.loc[:, 'Address'].to_string(index=False))
        return self.df

    def file_has_address(self):
        #Check if an 'Address' column exists
        return 'Address' in self.df.columns

    def write_csv(self):
        # if file exists, remove
        if os.path.isfile(self.filename):
            os.remove(self.filename)
        self.df.to_csv(self.filename, index=False)

    def get_geo_data(self):
        bing = Bing(self.BING_KEY, timeout=10)
        self.df['LongLat'] = self.df['Address'].apply(bing.geocode)
        self.df['LongLat'] = self.df['LongLat'].apply(lambda x: (x.longitude, x.latitude) if x != None else None)
        return self.df



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data", methods=['POST'])
def data():
    global filename
    if request.method == 'POST':
        file = request.files["form_file"]
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f ")
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", secure_filename(timestamp+file.filename))
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        file.save(filename)
        try:
            print(filename)
            geo = Geo(filename)
            geo.read_file()
            if geo.file_has_address():
                geo_data = geo.get_geo_data()
                geo.write_csv()
                return render_template("index.html", btn="download.html", data=geo_data.to_html(justify='center'))
            else:
                return render_template("index.html", err="The file was missing an 'Address' column. Please check and try again.")
        except:
            return render_template("index.html", err="There was a problem with your file. Please check and try again.")

@app.route("/download")
def download():
    return send_file(filename, attachment_filename="data.csv", as_attachment=True)

if __name__ == '__main__':
    app.debug = True
    app.run()
