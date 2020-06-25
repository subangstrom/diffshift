import numpy as np
import math
import sys
sys.path.append('C:\\Users\\factory\\Documents\\GitHub\\useTEM\\modules\\tiascript')
import application
esv = application.Application()
sys.path.append('C:\\Users\\factory\\Documents\\GitHub\\useTEM\\modules\\temscript')
import instrument
sys.path.append('C:\\Users\\factory\\Documents\\GitHub')
import useTEM.modules.temscript.instrument as tem
# from comtypes.client import CreateObject
from time import sleep

class Diffshift():
    def __init__(self):
        # self.instrumnet = tem.Instrument()
        self.pj = tem.Instrument.projection
        # self.esv = application.Application()
        self.bp = esv.ImageServer.BeamPosition

    def creatPositionslist(self,x0,xf,y0,yf,size,overlap):
        numx = math.ceil((xf - x0)/(size*(1-overlap)))
        numy = math.ceil((yf - y0)/(size*(1-overlap)))
        x = np.linspace(x0,xf,numx)
        y = np.linspace(y0,yf,numy)
        xx, yy = np.meshgrid(x,y)
        positions = [xx.reshape((1,-1))[0],yy.reshape((1,-1))[0]]
        positions = list(map(tuple, zip(*positions)))
        return positions

    def rotationcorrection(self, shifts, angle=22.11):
        shiftlist = []
        for shiftx, shifty in shifts:
            xshift_old = shiftx*np.cos(angle*np.pi/180) - shifty*np.sin(angle*np.pi/180)
            yshift_old = shiftx*np.sin(angle*np.pi/180) + shifty*np.cos(angle*np.pi/180)
            shiftlist.append((xshift_old/1e3,yshift_old/1e3)) #change unit to radian
        return shiftlist

    def regularshift(self,shiftlist,expt,framet,numimages,filename,dwell):
        """
        dwell units of seconds
        """
        for shift in shiftlist:
            #empad start acquire in this line
            self.pj.diffractionShift(shift)
            Send_to_Cam(('Set_Take_n %.8f %.8f %d\n' % (expt, framet, numimages)))
            Send_to_Cam(('Exposure %s\n' % filename), False)
            sleep(dwell)
        #empad end acquire and save data in this line

    def angularshift(self,shiftlist,inner_R,outter_R,dwell):
        """
        inner_R and outter_R units of radians
        dwell units of seconds
        """
        for shift in shiftlist:
            #empad start acquiring in this line
            if shift[0]**2+shift[1]**2 >= inner_R**2 and shift[0]**2+shift[1]**2 <= outter_R**2:
                self.pj.diffractionShift(shift)
                sleep(dwell) #in seconds
                print('recorded')
            else:
                print('skipped')
        #empad stop acquiring and save data

    def shift4dstem(self,positions,shiftlist,dwell,inner_R=0,outter_R=0,angular='regular'):
        for counter,position in enumerate(positions):
            self.bp(position)
            foldername = 'proposition%s' % counter
            if angular is 'regular':
                self.regularshift(shiftlist,dwell)
            else:
                self.angularshift(shiftlist,inner_R,outter_R,dwell)
