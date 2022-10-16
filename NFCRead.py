# NFCRead.py -- put your code here!
from lib import mfrc522
from machine import Pin, SPI
from utime import sleep
import deneyap
from config import uidlist


def do_read():
    spi = SPI(1, baudrate=2500000, polarity=0, phase=0, miso=Pin(deneyap.MISO), mosi=Pin(5), sck=Pin(19))
    spi.init()
    rdr = mfrc522.MFRC522(spi=spi, gpioRst=23, gpioCs=4)

    waiting_to_read = False

    while True:
        if not waiting_to_read:
            print("Kart Okutun")
            waiting_to_read = True

        (stat, tag_type) = rdr.request(rdr.REQIDL)

        if stat == rdr.OK:

            (stat, raw_uid) = rdr.anticoll()

            if stat == rdr.OK:
                waiting_to_read = False
                uid = "0x%02x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3], raw_uid[4])
                print( uid,"idli kart okundu")
                '''
                if rdr.select_tag(raw_uid) == rdr.OK:
                    print(uidlist[uid], "Okundu")
                else:
                    print("Select failed")
                '''
        sleep(0.5)
