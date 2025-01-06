# in terminal
# circuitpython_setboard adafruit_feather_rp2040_adalogger
# "c:\program files (x86)\teraterm\ttermpro.exe"

import os
import time

import board
import array
import busio
import sdcardio
import storage
import microcontroller
import rtc
from lib import adafruit_ds3231
import gc
import supervisor
import digitalio

from lib import I2S

def prep_header(num_channels, sampleRate, bitsPerSample):
    header[:4] =  bytes("RIFF", "ascii")  # (4byte) Marks file as RIFF
    header[4:8] = (512-2*4).to_bytes(4, "little" )  # (4byte) File size in bytes
                                                                    # excluding this and RIFF marker
    header[8:12] = bytes("WAVE", "ascii")  # (4byte) File type
    header[12:16] = bytes("fmt ", "ascii")  # (4byte) Format Chunk Marker
    header[16:20] = (16).to_bytes(4, "little")  # (4byte) Length of above format data
    header[20:22] = (1).to_bytes(2, "little")  # (2byte) Format type (1 - PCM)
    header[22:24] = num_channels.to_bytes(2, "little")  # (2byte)
    header[24:28] =  sampleRate.to_bytes(4, "little")  # (4byte)
    header[28:32] =  (sampleRate * num_channels * bitsPerSample // 8).to_bytes(4, "little")  # (4byte)
    header[32:34] =  (num_channels * bitsPerSample // 8).to_bytes(2, "little")  # (2byte)
    header[34:36] =  bitsPerSample.to_bytes(2, "little")  # (2byte)
    header[36:40] =  bytes("JUNK", "ascii")  # (4byte) Junk Chunk Marker
    header[40:44] =  (512-13*4).to_bytes(4, "little")  # (4byte) Junk size in bytes
    header[504:508] =  bytes("data", "ascii")  # (4byte) Data Chunk Marker
    header[508:512] =  (0).to_bytes(4, "little")  # (4byte) Data size in bytes

def update_header(nbytes):
    header[4:8] = (nbytes + 512 - 2 * 4).to_bytes(4, "little")
    header[508:512] = nbytes.to_bytes(4, "little")

#----------------------------------------------------------
def does_file_exist(filename):
    try:
        status = os.stat(filename)
        file_exists = True
    except OSError:
        file_exists = False
    return file_exists

def logger(data):
    global status, time_open, loop_count, data_count, total_bytes_written, old_time, old_hour
    global wav

    if status == CLOSED:
        # open new file
        time_open = time.time()
        t=r.datetime
        if t.tm_hour != old_hour:
            day_string = f"/sd/{t.tm_year:04d}{t.tm_mon:02d}{t.tm_mday:02d}"
            if not does_file_exist(day_string):
                os.mkdir(day_string)
                print('mkday: ',day_string)
            os.chdir(day_string)
            #
            Dir_string = f"{t.tm_hour:02d}"
            if not does_file_exist(Dir_string):
                print('mkdir: ',Dir_string)
                os.mkdir(Dir_string)
            os.chdir(Dir_string)
            old_hour=t.tm_hour
        #
        Date=f"{t.tm_year:04d}{t.tm_mon:02d}{t.tm_mday:02d}_{t.tm_hour:02d}{t.tm_min:02d}{t.tm_sec:02d}"
        fname="{}_{}.wav".format(uid_str,Date)
        t1=time.monotonic()
        wav = open(fname, "wb")
        t1=time.monotonic()-t1
        pos = wav.seek(512)  # advance to first byte of Data section in WAV file
        total_bytes_written = 0
        if 1:
            print('opening:',fname,t1,end=' ')
        status = RECORDING

    if (status == RECORDING) | (status == MUST_STOP):
        # write data
        num_bytes_written = wav.write(data)
        total_bytes_written += num_bytes_written

        # check to close
        tmp_time=(time.time() % t_on )
        if (tmp_time < old_time) | (status == MUST_STOP):

            # create header for WAV file and write to SD card
            update_header(total_bytes_written)
            wav_header=header
            _ = wav.seek(0)  # return to first byte of Header section in WAV file
            num_bytes_written = wav.write(wav_header)

            # close file
            t1 = time.monotonic()
            wav.close()
            t1=time.monotonic()-t1
            #
            num_samples = total_bytes_written // (4 * NCH)
            print('\tnsamp',num_samples, num_samples/fsamp, data_count, loop_count, t1,'\t',data[0])
            data_count = 0
            loop_count = 0

            # should we stop or do we continue with next file?
            if status==MUST_STOP:
                status=STOPPED
            else:
                status = CLOSED
        old_time = tmp_time
    return status

def menu():
    global have_serial,status
    if have_serial==0:
        if supervisor.runtime.usb_connected:
            have_serial=1
    if have_serial==1:
        if supervisor.runtime.serial_bytes_available:
            ch = input().strip()
            if ch == 's':
                status=CLOSED
            elif ch == 'e':
                status=MUST_STOP
            else:
                print(len(ch),ch)
        return 0

def wait_for_Serial(secs):
    t0=time.monotonic()
    while (time.monotonic()-t0) < secs:
        if supervisor.runtime.usb_connected:
            time.sleep(1)
            print(time.monotonic()-t0)
            return 1
    return 0

#============================== Setup ===============================================
CLOSED = 0
RECORDING = 1
MUST_STOP = 2
STOPPED = 3
status = STOPPED

loop_count = 0
data_count = 0

NCH = 1
t_on = 20
fsamp = 48000

header=bytearray(512)
prep_header(num_channels=NCH,sampleRate=fsamp,bitsPerSample=32)

time_open = time.time()
old_time=0
old_hour=24

wav: None
total_bytes_written: int = 0

microcontroller.cpu.frequency=96_000_000
# Connect to the card and mount the filesystem.
spi = busio.SPI(board.SD_CLK, board.SD_MOSI, board.SD_MISO)
sdcard = sdcardio.SDCard(spi, board.SD_CS, baudrate=24000000)
vfs = storage.VfsFat(sdcard)

storage.mount(vfs, "/sd")
os.chdir('/sd/logger')

i2c = board.I2C()  # uses board.SCL and board.SDA
ext_rtc = adafruit_ds3231.DS3231(i2c)

r = rtc.RTC()

have_serial=wait_for_Serial(10)
if have_serial>0:
    print('\n**************microPAM********************\n')
    #
    fs_stat = os.statvfs('/sd')
    print("Disk size in MB",  fs_stat[0] * fs_stat[2] / 1024 / 1024)
    print("Free space in MB", fs_stat[0] * fs_stat[3] / 1024 / 1024)
    print(spi.frequency)
    print()
    #
    # check RTC clocks
    rd=r.datetime
    ldatestr=f"{rd.tm_mday:02d}-{rd.tm_mon:02d}-{rd.tm_year:04d} {rd.tm_hour:02d}:{rd.tm_min:02d}:{rd.tm_sec:02d}"
    print(' local: ',ldatestr)

    dt= ext_rtc.datetime
    datestr=f"{dt.tm_mday:02d}-{dt.tm_mon:02d}-{dt.tm_year:04d} {dt.tm_hour:02d}:{dt.tm_min:02d}:{dt.tm_sec:02d}"
    print('ds3231: ', datestr)
    print('Is time of ds3231 correct? If yes press return, otherwise')
    strx=input('enter time (dd-mm-yyyy HH:MM:SS): ')
    print(strx)
    if len(strx)>0:
        datestr,timestr=strx.split()
        day,month,year=datestr.split('-')
        hour,minute,second=timestr.split(':')
        print(year,month,day,hour,minute,second)
        td=time.struct_time([int(year),int(month),int(day),int(hour),int(minute),int(second),2,-1,-1])
        datetime = time.mktime(td)
        print(datetime)
        ext_rtc.datetime = td
else:
    status=CLOSED

#
#===========================================================================================
# synchronize rtc
r.datetime=ext_rtc.datetime
#
uid=microcontroller.cpu.uid
uid_str=f"{uid[-3]:02X}{uid[-2]:02X}{uid[-1]:02X}"
#

i2s = I2S.i2s_ICS43434(fs=fsamp)

if have_serial>0:
    print()
    print(f"# actual sample frequency {i2s.frequency / 2 / 2 / 32:9.1f} Hz")
    print(f"#               bit clock {i2s.frequency / 2:9.1f} Hz")
    print(f"#             Temperature {microcontroller.cpu.temperature:3.1f}")
    print()

NSAMP= 9600
buffer_in1 = array.array("l", (1 for _ in range(NSAMP)))
buffer_in2 = array.array("l", (2 for _ in range(NSAMP)))

i2s.background_read(loop=buffer_in1, loop2=buffer_in2)

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
#
# main loop
status=CLOSED
while True:
    menu()

    buffer = i2s.last_read
    if len(buffer) > 0:
        if status != STOPPED:
            led.value = True
            logger(buffer)
            led.value = False
            data_count += 1
            if data_count%100==0: gc.collect()
    loop_count += 1
#
# end of program