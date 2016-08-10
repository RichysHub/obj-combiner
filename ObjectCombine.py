#from packer.objuvpacker import main as pack
import subprocess
import os

def objectCombine(baseMeshFile,*args):

    output_name = ''.join(filter(lambda ch: ch not in '\ /','_'.join(sorted([baseMeshFile]+list(args)))))
    #output_name = 'composite'
    materialFiles = []
    #subprocess.call(['python','packer/objuvpacker.py','output.obj','-o','bloom'])

    vCount = 0
    vnCount = 0
    vtCount = 0

    def addObject(objFile):  # add object mesh to file
        with open('{0}.obj'.format(objFile),'r') as mesh:
            nonlocal vCount
            nonlocal vnCount
            nonlocal vtCount
            offsetV = vCount
            offsetVt = vtCount
            offsetVn = vnCount
            offsets = [offsetV, offsetVt, offsetVn]
            while True:
                line = mesh.readline()
                if line == '':
                    break #blank line indicates end of file
                if line.startswith("v "):
                    vCount += 1
                elif line.startswith("vn"):
                    vnCount += 1
                elif line.startswith("vt"):
                    vtCount += 1
                elif line.startswith("mtllib "):
                    if '/' in objFile or '\\' in objFile:
                        #TODO: test if this works with files in same folder, if so, remove if
                        # adds material library to materialFiles, for adding later to .mtl
                        materialFiles.append(os.path.join(os.path.dirname(objFile), line[7:].rstrip('\n')))
                    else:
                        materialFiles.append(line.lstrip('mtllib ').rstrip('\n'))
                    if vCount == 0:  # The first time we see a mtllib, we add our new one
                        outobj.write('mtllib {0}.mtl\n'.format(output_name))
                    continue
                elif line.startswith("f "):
                    if offsetV > 0:  # only true after first mesh. Could omit, but saves calculations
                        faceVertices = line.split()[1:] #split om spaces, ignoring 'f'
                        for index, vertex in enumerate(faceVertices):
                            coords = vertex.split('/') #splitting v/vt/vn
                            for ind, val in enumerate(coords):
                                if val != '': #handles v//vn format
                                    coords[ind] = str(int(val) + offsets[ind])
                            faceVertices[index] = '/'.join(coords)
                        outobj.write('f ' + ' '.join(faceVertices) + '\n')
                        continue
                outobj.write(line) #default is to write line as is (for comments and the like)

    def addMaterial(mtlFile): #real simple, but allows for more control later
        with open(mtlFile,'r') as material:
            while True:
                line = material.readline()
                if line == '':
                    break
                if line.startswith('#'):  # I don't care about comments, this file is short lived
                    continue
                outmtl.write(line)

    with open('output/{0}.obj'.format(output_name),"w") as outobj:

        addObject(baseMeshFile)
        for meshFile in args:
            addObject(meshFile)

    with open('output/{0}.mtl'.format(output_name),'w') as outmtl:
        for materialFile in materialFiles:
            addMaterial(materialFile)

    print("{0} v, {1} vn, {2} vt".format(vCount, vnCount, vtCount))
