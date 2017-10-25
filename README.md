# obj-combiner
Flask project for dynamic mesh combining, for use in Tabletop Simulator

# Motivation
Tabletop simulator (TTS) is a game that allows users to play any games they could otherwise do on a tabletop. Rather than focusing on implementing rule enforcement, the focus is on simulating the tabletop experience, physics and all.

One community that has taken to TTS is that of tabletop RPG.
Telling stories of characters is always enhanced when players are given visual aides, but with endless combinations of character, equipment and suchforth, creating player models is no small feat.

This project aims to utilise a repository of basic elements, be they weapons, armors, or any other accessories, and allow the dynammic combination, into a single model.

TTS supports the wavefront .obj format for custom models. By packing the composite models together with this script, one would avoid having to combine within the TTS engine, which would be at best, clumsy and prone to errors.

# Details
From a request, composite a single .obj, and pack textures to a single image

Within TTS, each player's client will request both the .obj file, and the image for the texture. Therefore, the results of combining are saved into a cache directory, which is emptied periodically.

Currently cache is implementes as a Least Recently Created cache, though LRU would probably be better suited.

Files in the database refer to dropbox files, currently using placeholder files, of unknown origin.
Constructed using flask, for hosting upon pythonanywhere

# Status
Repository dormant, project on hold.

Current state is quite the mess, this project was relatively early in my Python learning
Large amount of code copied from theFroh's imagepacker, in an attempt to get a working product.
Submitted pull request to this, which has been accepted to fix a small bug. Much of the use of that code in this project should definitely be refactored into imports.

Really a proof of concept, further work is planned, including refined OO style, and large custom library of models

Single character model created for new system.
Single weapon created while investigating models styles.
Many more character models and equipment models planned.
Code here would combine models into single wavefron .obj, and single image texture

Created and posed in Blender
![Lunge Spin Showcase](http://i.imgur.com/4CIRCGL.gif)
![Sword & Board Angles Showcase](http://i.imgur.com/i7QxDrI.gif)
![Sword & Board Spin Showcase](http://i.imgur.com/ZFjKTcR.gif)
![Textures Flame Sword](http://i.imgur.com/rUw8gvl.gif)
