from flask import Flask, request
import requests
import os
from tinydb import TinyDB, where
import urllib

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

    db = TinyDB('database/crawl.json') #load in the database
    slot_table = db.table('item_slots')

    items = {}

    for slot in slot_table.all():
        # also need to peel the class - may need to add to slots, or rename creatively
        slot_name = slot['name']
        item = request.args.get(slot_name)
        items.update({slot_name:item})  # we may not need to create this, may be able to do a single loop
        if item is None: #potentially it returns 'None' as a string?
            continue

        db_item = db.search(where('name') == item)

        if db_item == []:
            continue

        item_obj = db_item[0]['object'] # [0] get the first result (could make notes if len > 1)
        urllib.request.urlretrieve('https://www.dropbox.com/s/' + item_obj,'work_directory/' + item_obj[16:-5])#download to work_directory
        # 16:-5 is used to peel off the 15 char code + /, and to remove the ?dl=1

    # TODO: add shortcut if no items equipped, to return the base class model (and a scornful look :P )
        # may also want to control things like no class

    # TODO: sanitise imputs!!!

    for item in items:
        pass


    return str(items)

    # will need to create the output name, by combining the item slot+name(ignoring Nones) then combining together
    # need to fetch the urls from the item names, querying database a lot
        # one query to get each item after that, it's dict manipulation
    # unlike the local version, we can't get hold of the .mtl without the directions
        # will need to store .mtl and image urls too
            #may need to save the filenames for those documents?

    # if we're storing to a local file, we are basically setting us up to use the existing objectCombine function

    # look through the items find the files (.obj,.mtl,.png/jpg) (require only 1 image per item)
        #save the files to the temporary drive
            #need to ensure we have proper names - image in particular will be referenced in .mtl
                #should save the filename in the database too
        # .obj and .mtl go into the temp, images go directly into the output folder

        #can download (tested for .obj) with urllib.request.urlretieve(url,file_name)
        #though 'technically' legacy, I think I can handle that if needed


    # folders containing the files lies on a dropbox account (we don't care whos)
        # we assume dropbox, because it'll save some space in the database
    # plan to create a manager spreadsheet living on google docs
        # potentially multiple, one for each class
        # potentially just sheets = class, and some other way splitting slots
    # this spreadhseet will be easier to manage
    # write a python script to take an outputted csv (or even just a link to the doc) and update the database
        # once this gets sorted, adding items will be:
            # create objects, upload to dropbox
            # add links to the files in the spreadsheet
            # export the csv and run through the database editor
                # either rewrite db at home, and upload, or do it live
                # 'edit' will be a purge and replace (probably easier than writing checks to see if it exists already)
                        # basically going the easy route, rather than writing own VCS

    # might make more sense to have a table per class, this helps avoid name conflicts
        # for now we'll just use default - we're expecting the database to be replaced often
    # might want to include something to do with slots, even just have 'slot' as an entry
        # once again, helps avoid name conflicts
            # ie, can have 'mace' exist as both a main_hand and and an off_hand
            # can't do this with an 'is_offhand' field, as the model has to actually change

    # user = request.args.get('user') #can get hold of request arguements
    # db = tinydb.TinyDB('barry.json') #note for how to do database with tinydb

    # return 'yeah boi!'

@app.route('/image') #image file
def getImage():
    return 'Also yes!'

if __name__ == '__main__':
    app.run()