# SPDX-FileCopyrightText: 2018 Jerry Needell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import sys

import board
import busio
import storage
import sdcardio

# Connect to the card and mount the filesystem.
spi = busio.SPI(board.SD_CLK, board.SD_MOSI, board.SD_MISO)
sdcard = sdcardio.SDCard(spi, board.SD_CS)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")
sys.path.append("/sd")
