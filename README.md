ChopHuman-blender
=================

This project has been combined with the chophuman finishing tool at
https://github.com/floppya/ChopHuman

This repo will no longer receive updates.

About
-----
ChopHuman-blender is a [Blender](http://www.blender.org/) 2.6x plug-in which assists
in the generation of [2-D cutout-style](http://en.wikipedia.org/wiki/Cutout_animation)
characters from [MakeHuman](http://www.makehuman.org/) meshes. This is far from being
a nice piece of software but does, sort of, work. At this point it only generates
diffuse and normal maps of the body parts in a right-facing, profile orientation.

Installation
------------
Copy the chophuman folder into your blender addons directory and then enable
it in User Settings under the MakeHuman group. So far, this has only been
used in Blender 2.65.

Usage
-----
It currently assumes the existence of a lamp named 'Lamp' and a camera named
'Camera'; essentially the default scene minus the cube. Running it adds a
bunch of modifier masks and vertex groups, plus rearranges the camera, lights
and the arms of the MakeHuman mesh.

* This is currently in a very unpolished state so get some coffee going.
* Import your MakeHuman model.
* In object mode, select the root-level object which contains all the
MakeHuman meshes (clothes, skin, etc).
* The ChopHuman panel can be found in the object properties.
* First, click 'Chop' which creates mask modifiers for each limb, on each mesh.
* Then click 'Render' which will render each limb on its own.

Now that you have a bunch of renders of the limbs, you might find 
[ChopHuman-finisher](https://github.com/floppya/chophuman-finisher) useful.
It aims to simplify cleaning up and rigging the renders for export to
other animation tools.

License
-------
MIT licensed.