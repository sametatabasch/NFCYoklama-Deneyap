# NFCRead.py -- put your code here!
from lib import mfrc522
from machine import Pin, SPI
from utime import ticks_ms
import deneyap


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
                print("Kart Okundu")
                waiting_to_read = False
                print("type: 0x%02x" % tag_type)
                print("uid: 0x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]))
                for i in raw_uid:
                    print(i)
                    print("0x%02x" % i)
                print("")

                if rdr.select_tag(raw_uid) == rdr.OK:

                    key = b'\xff\xff\xff\xff\xff\xff'

                    ms = ticks_ms()

                    blockArray = bytearray(16)
                    for sector in range(1, 64):
                        if rdr.auth(rdr.AUTHENT1A, sector, key, raw_uid) == rdr.OK:
                            rdr.read(sector, into=blockArray)
                            print("data@%d: %s" % (sector, blockArray))
                        else:
                            print("Auth err - Sector",sector)
                    rdr.stop_crypto1()

                    print("Read in " + str(ticks_ms() - ms))  # took 4594 ms

                else:
                    print("Select failed")
