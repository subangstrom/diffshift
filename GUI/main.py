import sys
# import temscript
from temscript import projection
from temscript import instrument
import numpy as np
from time import sleep
# from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.uic import loadUi
from PyQt5.QtCore import *
from PyQt5 import QtCore

class ShiftThread(QThread):
    notifyprocess = QtCore.pyqtSignal(str)
    resetsignal = QtCore.pyqtSignal()

    def __init__(self, Shifts, rotation0, inner_R, outter_R, is_angularmode, parent=None):
        super(ShiftThread, self).__init__(parent)
        self.Shifts = Shifts
        self.rotation0 = rotation0
        self.shift_count = 0
        self.inner_R = inner_R
        self.outter_R = outter_R
        self.projection = projection(instrument)
        self.is_angularmode = is_angularmode
        self.running = True
        self.dwelltime = 1 #second

    def run(self):
        while self.running:
            if self.is_angularmode:
                self.angular()
            else:
                self.regularshift()

    def stop(self):
        #print('received stop signal from window')
        self.running = False
        self.resetsignal.emit()



    def regularshift(self):
        for shiftx, shifty in self.Shifts:

            if self.running == False:
                break

            xshift_old = shiftx*np.cos(self.rotation0*np.pi/180) - shifty*np.sin(self.rotation0*np.pi/180)
            yshift_old = shiftx*np.sin(self.rotation0*np.pi/180) + shifty*np.cos(self.rotation0*np.pi/180)
            shift = [xshift_old/1e3,yshift_old/1e3]
            self.projection.diffractionShift(shift)
            self.shift_count = self.shift_count+1
            self.notifyprocess.emit(str(self.shift_count))
            sleep(self.dwelltime) #in seconds

        self.stop()

    def angular(self):

        for shiftx, shifty in self.Shifts:

            if self.running == False:
                break

            xshift_old = shiftx*np.cos(self.rotation0*np.pi/180) - shifty*np.sin(self.rotation0*np.pi/180)
            yshift_old = shiftx*np.sin(self.rotation0*np.pi/180) + shifty*np.cos(self.rotation0*np.pi/180)
            shift = [xshift_old/1e3,yshift_old/1e3]
            print((xshift_old,yshift_old),xshift_old**2+yshift_old**2,self.inner_R**2,self.outter_R**2)

            if self.inner_R**2 <= xshift_old**2+yshift_old**2 <= self.outter_R**2:

                self.projection.diffractionShift(shift)
                self.shift_count += 1
                self.notifyprocess.emit(str(self.shift_count))
                sleep(self.dwelltime) #in seconds
            else:
                self.shift_count += 1
                self.notifyprocess.emit(str(self.shift_count)+'skipped')
        self.stop()



class Diffshift(QDialog):

    def __init__(self):
        super(Diffshift, self).__init__()
        loadUi('Diffshift.ui',self)
        self.setWindowTitle('Diffshift')

        self.thread = QThread()
        #self.thread.start()

        #self.Start.clicked.connect(self.on_Start_clicked)
        self.Abort.setEnabled(False)
        self.rotation0 = float(self.Rotation.text())
        self.total_shifts = 0
        self.projection = projection.Projection()

        self.detectorsize = 128
        self.overlap = 0.2  #default 20% overlape
        self.shift_startposition = self.projection._proj.DiffractionShift

        self.shiftthread = ShiftThread(self.projection, [], self.rotation0, 0, 0, True)
        self.shiftthread.notifyprocess.connect(self.displayCurrentShift)
        self.shiftthread.resetsignal.connect(self.resetshift)
        self.Abort.clicked.connect(lambda: self.shiftthread.stop())

        self.finished.connect(self.stop_thread)

    def stop_thread(self):
        self.shiftthread.stop()
        self.thread.quit()
        self.thread.wait()

    def setupShifts(self):
        rotation0 = float(self.Rotation.text()) #in degree, a rotation offset to align diffraction with the detector
        # pixelsize = float(self.Pixelsz.text()) #in mrad given by camera length
        Xwidth = float(self.Xwidth.text()) #in mrad
        Ywidth = float(self.Ywidth.text()) #in mrad
        inner_R = float(self.Inner.text())
        outter_R = float(self.Outter.text())
        if self.Angular.isChecked():

            Shifts, total_shifts = self.shiftslist(outter_R, outter_R, rotation0)
        else:
            Shifts, total_shifts = self.shiftslist(Xwidth, Ywidth, rotation0)
        return Shifts, total_shifts

    def shiftslist(self, Xwidth, Ywidth, rotation):

        pixelsize = float(self.Pixelsz.text())
        detectorsize = self.detectorsize*pixelsize
        shift_stepsize = detectorsize*(1-self.overlap)

        Xshift = np.arange(-Xwidth + detectorsize/2, Xwidth - detectorsize/2, shift_stepsize)
        Yshift = np.arange(-Ywidth + detectorsize/2, Ywidth - detectorsize/2, shift_stepsize)

        Shifts = [(x, y) for x in Xshift for y in Xshift]
        Shifts = self.rotationcorrection(Shifts, rotation)
        total_shifts = Xshift.size*Yshift.size
        return Shifts, total_shifts

    def rotationcorrection(self, shifts, angle=22.11):
        shiftlist = []
        for shiftx, shifty in shifts:
            xshift_old = shiftx*np.cos(angle*np.pi/180) - shifty*np.sin(angle*np.pi/180)
            yshift_old = shiftx*np.sin(angle*np.pi/180) + shifty*np.cos(angle*np.pi/180)
            shiftlist.append((xshift_old/1e3, yshift_old/1e3)) #change unit to radian
        return shiftlist

    def resetshift(self):
        self.projection.diffractionShift(self.shift_startposition)
        self.Shift.setText('')
        self.Start.setEnabled(True)
        self.Abort.setEnabled(False)
        self.shiftthread.shift_count = 0

    #@pyqtSlot()
    def on_Start_clicked(self):

        print('clicked')
        self.Shifts, self.total_shifts = self.setupShifts()
        self.shiftthread.Shifts = self.Shifts
        self.shiftthread.rotation0 = self.rotation0
        self.shiftthread.inner_R = float(self.Inner.text())
        self.shiftthread.outter_R = float(self.Outter.text())
        self.shiftthread.dwelltime = float(self.Dwell.text())/1e3
        self.Abort.setEnabled(True)
        self.shiftthread.running = True
        print(self.Angular.isChecked())
        self.shiftthread.is_angularmode = self.Angular.isChecked()
        self.shiftthread.start()



    def on_Abort_clicked(self):
        self.Shift.setText('should abort workerthread and reset diffshift')

    def displayCurrentShift(self,currentshift):

        self.Shift.setText(f'{currentshift} of {str(self.total_shifts)}')

# %%
app = QApplication(sys.argv)
widget = Diffshift()
widget.show()
sys.exit(app.exec_())
