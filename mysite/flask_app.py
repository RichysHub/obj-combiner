from flask import Flask, request
import requests
import os
import tinydb

app = Flask(__name__)


@app.route('/')
def hello():
    #image = requests.get('https://www.dropbox.com/s/v6shp2get5b3gez/Dr%20Boom_packed_full.png?dl=1')
    bot = requests.get('https://www.dropbox.com/s/5rxlttrp5adhd9y/bomb%20bot.obj?dl=1').content
    with open('log.txt','a') as out:
        out.write('hey there!\n')
    return bot

@app.route('/object') #object file
def getobject():
    user = request.args.get('user') #can get hold of request arguements
    db = tinydb.TinyDB('barry.json')
    return 'Yeah boi!'

@app.route('/image') #image file
def getImage():
    return 'Also yes!'

if __name__ == '__main__':
    app.run()