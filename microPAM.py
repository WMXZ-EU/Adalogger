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
import adafruit_ds3231
import gc
import supervisor
import digitalio

from lib import I2S

# This helper function will print the contents of the SD
def print_directory(path, tabs=0, recursive=0):
    for file in os.listdir(path):
        if file == "?":
            continue  # Issue noted in Learn
        stats = os.stat(path + "/" + file)
        filesize = stats[6]
        isdir = stats[0] & 0x4000

        if filesize < 1000:
            sizestr = str(filesize) + " by"
        elif filesize < 1000000:
            sizestr = "%0.1f KB" % (filesize / 1000)
        else:
            sizestr = "%0.1f MB" % (filesize / 1000000)

        prettyprintname = ""
        for _ in range(tabs):
            prettyprintname += "   "
        prettyprintname += file
        if isdir:
            prettyprintname += "/"
        print('{0:<40} Size: {1:>10}'.format(prettyprintname, sizestr))

        # recursively print directory contents
        if recursive>0:
            print_directory(path + "/" + file, tabs + 1)

def create_wav_header(sampleRate, bitsPerSample, num_channels, num_samples):
    datasize = num_samples * num_channels * bitsPerSample // 8
    o = bytes("RIFF", "ascii")  # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(4, "little"
                                  )  # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE", "ascii")  # (4byte) File type
    o += bytes("fmt ", "ascii")  # (4byte) Format Chunk Marker
    o += (16).to_bytes(4, "little")  # (4byte) Length of above format data
    o += (1).to_bytes(2, "little")  # (2byte) Format type (1 - PCM)
    o += num_channels.to_bytes(2, "little")  # (2byte)
    o += sampleRate.to_bytes(4, "little")  # (4byte)
    o += (sampleRate * num_channels * bitsPerSample // 8).to_bytes(4, "little")  # (4byte)
    o += (num_channels * bitsPerSample // 8).to_bytes(2, "little")  # (2byte)
    o += bitsPerSample.to_bytes(2, "little")  # (2byte)
    o += bytes("data", "ascii")  # (4byte) Data Chunk Marker
    o += datasize.to_bytes(4, "little")  # (4byte) Data size in bytes
    return o

#----------------------------------------------------------
CLOSED = 0
RECORDING = 1
MUST_STOP = 2
STOPPED = 3
status = STOPPED

loop_count = 0
data_count = 0

NCH = 1
t_on = 60
fsamp = 48000

time_open = time.time()
old_time=0

wav: None
total_bytes_written: int = 0
def logger(data):
    global status, time_open, loop_count, data_count, total_bytes_written,old_time
    global wav

    if status == CLOSED:
        # open new file
        time_open = time.time()
        t=r.datetime
        Date=f"{t.tm_year:04d}{t.tm_mon:02d}{t.tm_mday:02d}_{t.tm_hour:02d}{t.tm_min:02d}{t.tm_sec:02d}"
        fname="{}_{}.wav".format(uid_str,Date)
        t1=time.monotonic()
        wav = open(fname, "wb")
        print(time.monotonic()-t1)
        pos = wav.seek(44)  # advance to first byte of Data section in WAV file
        total_bytes_written = 0
        print(time.monotonic()-t1)
        if 1:
            print('opening:',fname, time_open , loop_count, data_count)
            print('   ',end=' ')
            for x in data[:14]: print(f"{x:08x}",end=' ')
            print()
            data_count = 0
            loop_count = 0
        print(time.monotonic()-t1)
        status = RECORDING

    if (status == RECORDING) | (status == MUST_STOP):
        # write data
        num_bytes_written = wav.write(data)
        total_bytes_written += num_bytes_written

        # check to close
        tmp_time=(time.time() % t_on )
        if (tmp_time < old_time) | (status == MUST_STOP):
            t1 = time.monotonic()

            # create header for WAV file and write to SD card
            num_samples = total_bytes_written // (4 * NCH)
            wav_header = create_wav_header(
                fsamp,
                32,
                NCH,
                num_samples,
            )
            print('num_samples',num_samples, num_samples/fsamp)
            _ = wav.seek(0)  # return to first byte of Header section in WAV file
            num_bytes_written = wav.write(wav_header)

            # close file
            wav.close()
            print(time.monotonic() - t1, gc.mem_free())
            #
            # should we stop or do we continue with next file?
            if status==MUST_STOP:
                status=STOPPED
            else:
                status = CLOSED
        old_time = tmp_time
    return status

def menu():
    if supervisor.runtime.serial_bytes_available:
        ch = input().strip()
        if ch == 's':
            return 1
        elif ch == 'e':
            return -1
        else:
            print(len(ch),ch)
    return 0

def wait_for_Serial(secs):
    while time.monotonic() < 10:
        if supervisor.runtime.usb_connected:
            time.sleep(1)
            print(time.monotonic())
            break


microcontroller.cpu.frequency=96_000_000
# Connect to the card and mount the filesystem.
spi = busio.SPI(board.SD_CLK, board.SD_MOSI, board.SD_MISO)
sdcard = sdcardio.SDCard(spi, board.SD_CS,baudrate=24000000)
vfs = storage.VfsFat(sdcard)

storage.mount(vfs, "/sd")
os.chdir('/sd/logger')

# Use the filesystem as normal! Our files are under /sd
if 0:
    print("Files on filesystem:")
    print("====================")
    print_directory("/sd/logger")

i2c = board.I2C()  # uses board.SCL and board.SDA
ext_rtc = adafruit_ds3231.DS3231(i2c)

wait_for_Serial(3)
print('\n**************microPAM********************\n')
#
fs_stat = os.statvfs('/sd')
print("Disk size in MB",  fs_stat[0] * fs_stat[2] / 1024 / 1024)
print("Free space in MB", fs_stat[0] * fs_stat[3] / 1024 / 1024)
print(spi.frequency)
print()
#

dt= ext_rtc.datetime
datestr=f"{dt.tm_mday:02d}-{dt.tm_mon:02d}-{dt.tm_year:04d} {dt.tm_hour:02d}:{dt.tm_min:02d}:{dt.tm_sec:02d}"
print('ds3132', datestr)
print('Is time correct? If yes press return, otherwise')
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
#
#===========================================================================================
r = rtc.RTC()
print('local',r.datetime)
#
r.datetime=ext_rtc.datetime
#
uid=microcontroller.cpu.uid
uid_str=f"{uid[-3]:02X}{uid[-2]:02X}{uid[-1]:02X}"
#

i2s = I2S.i2s_ICS43434(fs=fsamp)

print()
print(f"# actual sample frequency {i2s.frequency / 2 / 2 / 32:9.1f} Hz")
print(f"#               bit clock {i2s.frequency / 2:9.1f} Hz")
print(f"#             Temperature {microcontroller.cpu.temperature:3.1f}")
print()

NSAMP= 4*1200
buffer_in1 = array.array("l", (1 for _ in range(2*NSAMP)))
buffer_in2 = array.array("l", (2 for _ in range(2*NSAMP)))

i2s.background_read(loop=buffer_in1, loop2=buffer_in2)

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
#
# main loop
while True:
    ch=menu()
    if ch==1:
        status=CLOSED
    elif ch==-1:
        status=MUST_STOP

    buffer = i2s.last_read
    if len(buffer) > 0:
        if status != STOPPED:
            led.value = True
            logger(buffer)
            led.value = False
            data_count += 1
            if (data_count%100==0): gc.collect()
    loop_count += 1
#
# end of program