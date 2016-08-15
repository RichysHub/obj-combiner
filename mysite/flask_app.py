from flask import Flask, request, send_file, redirect
import requests
from tinydb import TinyDB, where
import urllib
from imagepacker import pack_images
import os
from shutil import rmtree
from spacemaker import shrink_folder_to

app = Flask(__name__)

# Teardown cleans up the output folder
@app.teardown_request
def clenseOutput(f):
    # removes oldest files until output folder is under limit (in bytes)
    # 104857600 is 100 Mebibytes
    shrink_folder_to(104857600, 'output')

def makeName(*args):
    #currently assumes you're passing 'unique_id's, can revisit if need to pass filenames
    return '-'.join(sorted(*args))

def getContent(drop_code,file_w_ext):
    #passed a 15-digit dropbox code and a filename with extension, returns file contents (for obj and mtl)
    if len(drop_code) != 15:
        print('\nDropbox code {0} of incorrect length'.format(drop_code))
        raise ValueError('Dropbox code of incorrect length')
    return requests.get('https://www.dropbox.com/s/{0}/{1}?dl=1'.format(drop_code,file_w_ext)).text

def storeImage(temporary_dir, drop_code, file_w_ext):
    #passed a 15-digit dropbox code and a filename with extension, path to image
    image_path = '{0}/{1}'.format(temporary_dir, file_w_ext)
    urllib.request.urlretrieve('https://www.dropbox.com/s/{0}/{1}?dl=1'.format(drop_code,file_w_ext), image_path)
    return image_path


# TODO: handle no args given (default model?) - crawl logo?
@app.route('/object') # get request for object file
def getObject():
    return getByExtension('obj')

@app.route('/image') #image file
def getImage():
    return getByExtension('png')

def getByExtension(extension):
    # takes extension, of form .<ext>, ie 'png' or 'obj'
    db = TinyDB('database/crawl.json')
    slot_table = db.table('item_slots')
    db_items = []
    selected_class = request.args.get('class')
    object_ids = []
    # minimum work possible, to get the output name, to check in output/
    for slot in slot_table.all():
        slot_name = slot['name']
        item = request.args.get(slot_name)
        if item is None:
            continue #slot wasn't specified
        db_item = db.search((where('name') == item) & (where('class') == selected_class) & (where('slot') == slot_name))
        if db_item:
            db_item = db_item[0]
            db_items.append(db_item)
            object_ids.append(db_item['unique_id'])

    # output name is a combination of unique ids, therefore is unique to this loadout
    output_name = makeName(object_ids)

    # with filename, check in outputs
    if os.path.isfile('output/{0}.{1}'.format(output_name, extension)):
        print('Returning {0}.{1} from psuedo-cache'.format(output_name, extension))
        return send_file('../output/{0}.{1}'.format(output_name, extension),as_attachment=True)

    if len(db_items) == 0:
        #TODO: redirect this to either homepage, or serve a default file
        return 'nope'
    # handle single input
    elif len(db_items) ==1:
        # gets url for the item's dropbox, and redirects to it
        item = db_items[0]
        if extension == 'obj': # based on extension returns either object or image
            url = 'https://www.dropbox.com/s/{0}/{1}?dl=1'.format(item['obj_code'], item['obj_name'])
        else:
            url = 'https://www.dropbox.com/s/{0}/{1}?dl=1'.format(item['img_code'], item['img_name'])

        return redirect(url)
    else:
        combineObjects(db_items, output_name)
        #return the file
        return send_file('../output/{0}.{1}'.format(output_name, extension),as_attachment=True)

def combineObjects(db_items, output_name):
    # accepts database items and output name, to avoid calculating twice
    object_files = []
    material_files = []
    texture_paths = []

    os.mkdir(output_name) # create the temporary directory (will use this as markfile?)

    for db_item in db_items:
        #Fetch obj and mtl files, save strings to array
        object_files.append(getContent(db_item['obj_code'], db_item['obj_name']))
        material_files.append(getContent(db_item['mtl_code'], db_item['mtl_name']))
        #Fetch texture image and save to file
        image_path = storeImage(output_name, db_item['img_code'], db_item['img_name'])
        texture_paths.append(image_path)

    diffuse_maps = [] #paths, relative to the packer?, to fetch the images
    names = []
    new_mtl_lines = []
    image_out_name = 'output/' + output_name + '.png'

    for mat_index, material_file in enumerate(material_files): #combines all the materials, as well as gleaning relevant info
        for line in material_file.split('\n'): #split into lines by linebreaks
            line = line.strip()

            if line.startswith('newmtl'):
                name = line[7:] #peels off 'newmtl '
                if name and name != 'None':
                    if len(diffuse_maps) != len(names):
                        #We should have no way into this. We should check to exclude lines that use a map_kd from file
                        names.pop() # last material ignored as no diffuse
                    # TODO: name = + name #prepend something here if conflicts become an issue
                    names.append(name)
                else:
                    continue # None materials not added to output
            elif line.startswith('map_'):
                mtype,m = line.split(' ',1)
                if mtype.lower() == 'map_kd': #diffuse map
                    #Add check that m is the correct texture image, else don't add it to the diffuse_maps array
                    diffuse_maps.append(texture_paths[mat_index]) # add filepath to the relevant image
                    line = ' '.join([mtype, image_out_name]) # Change mtl to point to the output image
                else:
                    continue # ignore non-diffuse texture maps
            elif line.startswith('d '):
                continue # ignoring transparency values
            elif line.startswith('#'):
                continue    #ignore the comment lines

            new_mtl_lines.append(line)

        if len(diffuse_maps) != len(names):
            names.pop() #last material had no diffuse

    assert(len(names) == len(diffuse_maps))
    texmap = dict(zip(names,diffuse_maps)) #texture map is mapping of material names, to the images

    # NOTE: def of AABB, and some lines in object reading are only to deal with cropping the input textures
        # this is implemented for completeness,
        # but if items in database are strictly prepackaged, and therefore already cropped, we dont need it

    class AABB():
        def __init__(self, min_x=None, min_y=None, max_x=None, max_y=None):
                self.min_x = min_x
                self.min_y = min_y
                self.max_x = max_x
                self.max_y = max_y

                self.to_tile = False

        def add(self, x,y):
                self.min_x = min(self.min_x, x) if self.min_x else x
                self.min_y = min(self.min_y, y) if self.min_y else y
                self.max_x = max(self.max_x, x) if self.max_x else x
                self.max_y = max(self.max_y, y) if self.max_y else y

        def uv_wrap(self):
                return (self.max_x - self.min_x, self.max_y - self.min_y)

        def tiling(self):
                if self.min_x < 0 or self.min_y < 0 or self.max_x > 1 or self.max_y > 1:
                    return (self.max_x - self.min_x, self.max_y - self.min_y)
                return None

        def __repr__(self):
                return "({},{}) ({},{})".format(
                    self.min_x,
                    self.min_y,
                    self.max_x,
                    self.max_y
                )

    textents = {name: AABB() for name in set(diffuse_maps)}

    uv_lines = []
    curr_mtl = None
    used_mtl = set()

    obj_lines =[]
    # Reading the object files, combing them and updating vertex references
    vertex_counts = {'v':0,'vt':0,'vn':0} #counts of vertices, texture vertices, and normal vertices
    for object_file in object_files:
        line_offset = len(obj_lines) #offset to obtain indices for line in combined file

        offsets = [vertex_counts['v'], vertex_counts['vt'], vertex_counts['vn']]
        for line_idx, line in enumerate(object_file.split('\n')):
            line = line.strip()

            if line.startswith('v '):
                vertex_counts['v'] += 1
            elif line.startswith('vn'):
                vertex_counts['vn'] += 1
            elif line.startswith('vt'):
                vertex_counts['vt'] += 1
                uv_lines.append(line_idx + line_offset)
            elif line.startswith('usemtl'):
                mtl_name = line[7:] # remove 'usemtl '
                curr_mtl = mtl_name
            elif line.startswith('f '):
                #although offsets only apply after the first mesh, we need to go uv calcs
                face_vertices = line.split()[1:] #split on spaces, ignoring 'f'
                for index, vertex in enumerate(face_vertices):
                    vertex_indices = vertex.split('/') #splitting v/vt/vn
                    for ind, val in enumerate(vertex_indices):
                        if val != '': #handles v//vn format
                            #use of ind here allows code to cover v, v/vt, v//vn and v/vt/vn formats
                            vertex_indices[ind] = str(int(val) + offsets[ind])
                    if len(vertex_indices) >= 2 and vertex_indices[1]: #ignores v and v//vn formats
                        uv_idx = int(vertex_indices[1]) - 1 # uv indices start from 1
                        uv_line_idx = uv_lines[uv_idx]
                        uv_line = obj_lines[uv_line_idx][3:] # fetches 'vt ' line that this vertex uses
                        uv = [float(uv.strip()) for uv in uv_line.split()]

                        if curr_mtl and curr_mtl in texmap:
                            used_mtl.add(mtl_name)
                            # update the texture extents in the texture map so that used region is added
                            textents[texmap[curr_mtl]].add(uv[0], uv[1])
                    face_vertices[index] = '/'.join(vertex_indices)

                line = 'f ' + ' '.join(face_vertices) + '\n'
            obj_lines.append(line) #comments, objects, groups and such

    # TODO this currently does not support tiling of uv's, it would be added here

    # TODO if we want to add a small watermark-like image to the output
        #here would be the place to add it to the diffuse_maps

    #Pack the images into a single file
    output_image, uv_changes = pack_images(list(set(diffuse_maps)), extents=textents)

    uv_line = [] #TODO, is this reset and the re-making needed?
    curr_mtl = None

    # apply changes to .obj UV's
    new_obj_lines = []
    for line_idx, line in enumerate(obj_lines):
        if line.startswith("vt"):
            uv_lines.append(line_idx)
            new_obj_lines.append(line)
        elif line.startswith("usemtl"):
            mtl_name = line[7:]
            curr_mtl = mtl_name
            new_obj_lines.append(line)
        elif line.startswith("f"): # face definitions
            for vertex in line.split()[1:]: # individual vertex definitions
                vertex_indices = vertex.split(sep="/")
                if len(vertex_indices) >= 2 and vertex_indices[1]: # ignores v and v//vn formats
                    uv_idx = int(vertex_indices[1]) - 1 # uv indexes start from 1
                    uv_line_idx = uv_lines[uv_idx]
                    uv_line = obj_lines[uv_line_idx][3:] #fetches relevant 'vt ' line
                    uv = [float(uv.strip()) for uv in uv_line.split()]

                    if curr_mtl and curr_mtl in texmap:
                        changes = uv_changes[texmap[curr_mtl]]

                        new_obj_lines[uv_line_idx] = "vt {0} {1}".format(
                            (uv[0] * changes["aspect"][0] + changes["offset"][0]),
                            (uv[1] * changes["aspect"][1] + changes["offset"][1])
                        )
            new_obj_lines.append(line)
        elif line.startswith("mtllib"): # change mtl file name
            print("\tupdated obj's mtllib to",output_name+".mtl")
            new_obj_lines.append("mtllib " + output_name+".mtl")
        else:
            new_obj_lines.append(line)

    # save the combined files to output directory
    with open('output/{0}.obj'.format(output_name),'w') as new_obj:
        new_obj.write('\n'.join(new_obj_lines))
    # material doesn't actually need to be kept
    #with open('output/{0}.mtl'.format(output_name),'w') as new_mtl:
    #    new_mtl.write('\n'.join(new_mtl_lines))
    output_image.save(image_out_name,format='PNG')

    # removes the temporary folder that was storing images, and the images therein
    rmtree(output_name)

@app.route('/')
def hello():
    #TODO: add a proper homepage
    return 'Welcome to Richys.pythonanywhere.com'

#TODO: add a page with which you can search the database, and display items (Pyglet based rendering?)

if __name__ == '__main__':
    app.run()