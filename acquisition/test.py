import numpy as np
import math
import sys
sys.path.append('C:\\Users\\factory\\Documents\\GitHub\\LGPython\\diffshift\\acquisition')
import diffshift
diff = diffshift.Diffshift()

probe_posx0 = -2e-6
probe_posxf =  2e-6
probe_posy0 = -2e-6
probe_posyf = 2e-6
probe_size = 1e-6
image_overlap = 0.2
# positions = creatPositionslist(probe_posx0,probe_posxf,probe_posy0,probe_posyf,probe_size,image_overlap)
positions = diff.creatPositionslist(probe_posx0,probe_posxf,probe_posy0,probe_posyf,probe_size,image_overlap)
positions


diffx0 = -100
diffxf = 100
diffy0 = -100
diffyf = 100
pixelsize = 0.4 # 0.1 mrad/pixel
detectorsize = 128*pixelsize
diff_overlap = 0.2
shifts = diff.creatPositionslist(diffx0,diffxf,diffy0,diffyf,detectorsize,diff_overlap)
shifts_corrected = diff.rotationcorrection(shifts)
shifts_corrected

dwell= 0.5
inner_R = 30e-3
outter_R = 100e-3
#%%
filename = padgui.Save_Path + filename
diff.regularshift(shifts_corrected,expt,framet,numimages,filename,dwell)



diff.angularshift(shifts_corrected,inner_R,outter_R,dwell)
diff.shift4dstem(positions,shifts_corrected,dwell,inner_R,outter_R,'angular')





# counter=1
sys.path.append('C:\\Users\\factory\\Documents\\GitHub\\useTEM\\modules\\temscript')
import instrument
sys.path.append('C:\\Users\\factory\\Documents\\GitHub')
import useTEM.modules.temscript.instrument as tem

pc = tem.Instrument.projection
pc.diffractionShift((50e-3,30e-3))

sys.path.append('C:\\Users\\factory\\Documents\\GitHub\\useTEM\\modules\\tiascript')
import application
esv = application.Application()
bc = esv.BeamControl
bc.MoveBeam(-10e-6,0)
ims = esv.ImageServer
bp = ims.BeamPosition
bp((-10e-6,0))
