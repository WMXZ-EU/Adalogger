import gc
from os import listdir,stat
import board
from busio import SPI
from sdcardio import SDCard
import storage
from array import array
import time
from time import monotonic
#from cmsis_dsp import  arm_rfft_q31,arm_cmplx_mag_squared_q31,arm_add_q31,arm_shift_q31
from cmsis_dsp import  rfft
import microcontroller
#microcontroller.cpu.frequency=250000000

time.sleep(3)
print(help('modules'))
print(microcontroller.cpu.frequency/1000000,'MHz')

spi = SPI(board.SD_CLK, board.SD_MOSI, board.SD_MISO)
sdcard = SDCard(spi, board.SD_CS, baudrate=24000000)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")

# collect files on disk
file_list = []

def list_files_recursive(path):
    for file in listdir(path):
        try:
            file = path + "/" + file
            stats = stat(file)
            filesize = stats[6]
            isdir = stats[0] & 0x4000

            if isdir:
                list_files_recursive(file)
            else:
                if file[-4:] == ".wav":
                    file_list.append(file)
        except:
            print('error')
            pass


# Specify the directory path you want to start from
directory_path = "/sd"
list_files_recursive(directory_path)
io = 10
print(len(file_list), io, file_list[io])

zz=array('l',range(2*1024))
yy=array('l',range(4*1024))
'''
uu1=memoryview(yy[0:1024])
uu2=memoryview(yy[1024:2048])
uu3=memoryview(yy[2048:3072])
uu4=memoryview(yy[3072:4096])
'''
def process(file):
    with  open(file, 'rb') as fi:
        hh = fi.read(512)
        uu= memoryview(hh).cast('L')
        ndat=uu[127]//4

        while True:
            dd = fi.read(16384)
            if len(dd) < 16384:
                fi.close()
                break
            xx=memoryview(dd).cast('l')
            rfft(512,xx,zz,yy,8)
            del dd
            del xx

    return ndat

'''            
            arm_rfft_q31(1024, xx[0:1024], zz)
            arm_cmplx_mag_squared_q31(zz, uu1, 512)

            arm_rfft_q31(1024, xx[1024:2048], zz)
            arm_cmplx_mag_squared_q31(zz, uu2, 512)

            arm_rfft_q31(1024, xx[2048:3072], zz)
            arm_cmplx_mag_squared_q31(zz, uu3, 512)

            arm_rfft_q31(1024, xx[3072:4096], zz)
            arm_cmplx_mag_squared_q31(zz, uu4, 512)

            arm_add_q31(uu1,uu2,uu1,512)
            arm_shift_q31(uu1,-1,uu1, 512)

            arm_add_q31(uu3,uu4,uu3, 512)
            arm_shift_q31(uu3,-1,uu3,512)

            arm_add_q31(uu1,uu3,uu1,512)
            arm_shift_q31(uu1,-1,uu1, 512)
            #
    # result in uu1
    return ndat
'''
if 1:
    for file in file_list[10:20]:
        gc.collect()
        print(file)
        t0=monotonic()
        ndat=process(file)
        print(ndat,monotonic()-t0)
        #print(gc.mem_alloc(),gc.mem_free())

# xx= struct.unpack("<512l", dd)
# data = np.array(array.array("f",xx))
# utils.from_int32_buffer(dd,out=uu)
# vv = utils.spectrogram(uu)
# spectrum() is always nonnegative, but add a tiny value
# to change any zeros to nonzero numbers
# spectrogram1 = np.log(spectrogram1 + 1e-7)
# spectrogram1 = spectrogram1[1:(512//2)-1]
# min_curr = np.min(spectrogram1)
# max_curr = np.max(spectrogram1)


#import time
#def timeit(s, f, n=100):
#    t0 = time.monotonic_ns()
#    for _ in range(n):
#        x = f()
#    t1 = time.monotonic_ns()
#    r = (t1 - t0) * 1e-6 / n
#    print("%-30s : %8.3fms [result=%f]" % (s, r, x))


#from ulab.numpy import fft, linspace,sin
#import ulab.utils as utils

#x = linspace(0, 10, num=1024)
#y = sin(x)
#print("B",len(y))

#yi=array.array('l',[0]*len(y))
#for ii in range(len(y)):
#    yi[ii]=int(y[ii]*1024*16)
#print("C",yi[0],yi[1],yi[2])
#yo=array.array('l',[0]*len(yi)*2)

#def m_fft(y):
#    a, b = fft.fft(y)
#    return a[0]


#def m_spectrum(y):
#    a = utils.spectrogram(y)
#    return a[0]

#def r_fft(y,yo):
#    arm_rfft_q31(len(yi), yi, yo)
#    return yo[0]

#timeit("fft", lambda: m_fft(y))
#timeit("spectrum", lambda: m_spectrum(y))
#timeit("cmsis", lambda: r_fft(y,yo))

#
#buffer_tmp = np.array(range(2048 // 4))
