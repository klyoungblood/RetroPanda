#!/usr/bin/env python

from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from direct.task.Task import Task
from direct.actor.Actor import Actor
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame

import sys
import os
import random

random.seed()

buf_size = 2048
gb_green_1 = (.525,.753,.424,1)

# make a solid-colored background
def MakeBackground(parent, color):
    bg=CardMaker('card')
    bg.setColor(color)
    bgc=parent.attachNewNode(bg.generate())
    
    #put it behind the grass, and scale it to fill the buffer
    bgc.setPos(-1,1,-1)
    bgc.setScale(2.0)
        
    bgc.reparentTo(parent)
    return bgc

# turns a PNG file into a background tile    
def MakeTile(parent, texpath):
    cm = CardMaker('card')    
    tex = loader.loadTexture(texpath)
    
    #tex.setMagfilter(SamplerState.FT_nearest)
    #tex.setMinfilter(SamplerState.FT_nearest)
    cm.setUvRange(tex)
    card = render.attachNewNode(cm.generate())
    card.setTexture(tex)    

    card.setScale(32.0/buf_size)
    card.setTransparency(TransparencyAttrib.MAlpha, 1)

    card.reparentTo(parent)
    return card
    
# class to build and control a sprite from a directory of PNG files
class Sprite():
    def __init__(self,parent,texpath):
        cm = CardMaker('card')        
        texd1 = loader.loadTexture(texpath+'/d1.png')
        texd2 = loader.loadTexture(texpath+'/d2.png')
        texu1 = loader.loadTexture(texpath+'/u1.png')
        texu2 = loader.loadTexture(texpath+'/u2.png')
        texr1 = loader.loadTexture(texpath+'/r1.png')
        texr2 = loader.loadTexture(texpath+'/r2.png')
        self.textures={'d':[texd1,texd2],'u':[texu1,texu2],'r':[texr1,texr2]}
        cm.setUvRange(texd1)
        card = render.attachNewNode(cm.generate())
        card.setTexture(texd1)   
        
        card.setScale(32.0/buf_size)
        card.setTransparency(TransparencyAttrib.MAlpha, 1)

        card.reparentTo(parent)
        self.card=card
        self.frame=0
        self.facing='d'
        
    def face(self,dir):
        if dir == 'u':
            self.card.setTexture(self.textures['u'][self.frame])
            self.card.clearTexTransform()
        elif dir == 'r':
            self.card.setTexture(self.textures['r'][self.frame])
            self.card.clearTexTransform()
        elif dir == 'l':
            # left-facing sprite flips the UVs of the right-facing to mirror the sprite
            self.card.setTexture(self.textures['r'][self.frame])
            self.card.setTexScale(TextureStage.getDefault(), -1, 1)
        else: #assume down
            self.card.setTexture(self.textures['d'][self.frame])
            self.card.clearTexTransform()
        self.facing=dir
            
    def cycle(self):
        self.frame = not self.frame
        self.face(self.facing)
    
        
    
class RetroEngine(ShowBase):

    def __init__(self):
        
        loadPrcFileData('', 'win-size 1280 720') 
        loadPrcFileData('', 'show-frame-rate-meter  t')
        #uncomment the following to turn off vsync (useful for benchmarking)
        #loadPrcFileData('', 'sync-video #f') 
        ShowBase.__init__(self)
        self.disableMouse()
        self.setBackgroundColor((0, 0, 0, 1))

        # game boy is 160x144, 256x144 is the nearest 16:9 resolution
        self.x_size=256.0
        self.y_size=144.0

        # we now get buffer thats going to hold the texture of our new scene
        altBuffer = self.win.makeTextureBuffer("hello", buf_size, buf_size)

        # now we have to setup a new scene graph to make this scene
        retro = NodePath("new render")

        # this takes care of setting up the camera properly
        self.altCam = self.makeCamera(altBuffer)
        lens = OrthographicLens()
        lens.setFilmSize(2, 2)
        lens.setNearFar(-1000, 1000)
        self.altCam.node().setLens(lens)

        self.altCam.reparentTo(retro)
        self.altCam.setPos(0, -10, 0)
        
        # Panda contains a built-in viewer that lets you view the results of
        # your render-to-texture operations.  This code configures the viewer.

        self.accept("v", self.bufferViewer.toggleEnable)
        self.accept("V", self.bufferViewer.toggleEnable)
        self.bufferViewer.setPosition("llcorner")
        self.bufferViewer.setCardSize(1.0, 0.0)
        
        # Create a texture from our alt buffer
        RetroTexture = altBuffer.getTexture()
        RetroTexture.setMagfilter(SamplerState.FT_nearest)
        RetroTexture.setMinfilter(SamplerState.FT_nearest)
        
        # Set up a fullscreen card to set the texture on.
        cm = CardMaker("My Fullscreen Card")
        cm.setFrameFullscreenQuad()

        # Set up a not-quite GBA-sized viewport on the buffer
        
        x_range = self.x_size/buf_size
        y_range = self.y_size/buf_size
        cm.setUvRange((0.5-x_range,0.5-y_range),(0.5+x_range, 0.5+y_range))

        # Now place the card in the scene graph and apply the texture to it.
        card = NodePath(cm.generate())
        card.reparentTo(self.render2d)
        card.setTexture(RetroTexture)      
       
        #stress-test using a randomly generated field of grass tiles on a solid background
        baseTile = MakeTile(render,'tiles/field_rough.png')
        
        bg=MakeBackground(retro,gb_green_1)
        
        # this will be the overall background after everything is flattened
        tilePP = NodePath('tile')
        tilePP.reparentTo(retro)
        
        for x in range(0,int(buf_size/16)):
            # we flatten each row as we create it as flattening all elements at once is
            # highly inefficient
            tileP = NodePath('tile')
            tileP.reparentTo(retro)
            for y in range (0,int(buf_size/16)):
                if random.randint(1,2) == 2:
                    tile = retro.attachNewNode("Placeholder")
                    tile.setPos((x*32)/buf_size-1,0,(y*32)/buf_size-1)
                    baseTile.instanceTo(tile)
                    tile.reparentTo(tileP)
        
            tileP.flattenStrong()
            tileP.reparentTo(tilePP)
            
        # now flatten all the rows into one geom
        tilePP.flattenStrong()
        
        self.sprites=[]
        
        # put a player sprite on the field
        sprite = Sprite(retro,'sprites/player')
                
        # center the sprite, and put it in front of the grass
        sprite.card.setPos(0,-1,0)     
        
        self.sprites.append(sprite)
        self.player=sprite
        
        # keyboard controls
        base.accept("arrow_up", self.handleInput, ['u'])
        base.accept("arrow_down", self.handleInput, ['d'])        
        base.accept("arrow_left", self.handleInput, ['l'])
        base.accept("arrow_right", self.handleInput, ['r'])        
        self.accept("escape", self.handleInput, ['b'])

        # center the 'camera' on the player
        card.setTexOffset(TextureStage.getDefault(),16.0/buf_size,0)
        
        taskMgr.doMethodLater(0.25, self.cycleSprites, 'Cycle sprites')
             
    def handleInput(self,key):
        if key == 'b':
            sys.exit(0)
        else:
            self.player.face(key)
            
    def cycleSprites(self,task):
        for sprite in self.sprites:
            sprite.cycle()
        return task.again
            
            

demo = RetroEngine()
demo.run()
