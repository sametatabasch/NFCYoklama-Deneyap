# NFCRead.py -- put your code here!
from lib import mfrc522
from machine import Pin, SPI, PWM
from utime import sleep
import deneyap
from config import uidlist

'''
Set Pins
'''
Pmiso = Pin(deneyap.MISO)
Pmosi = Pin(deneyap.MOSI)
Psck = Pin(deneyap.SCK)
Pbuzzer = Pin(deneyap.D15, Pin.OUT)


def do_read():
    spi = SPI(1, baudrate=2500000, polarity=0, phase=0, miso=Pmiso, mosi=Pmosi, sck=Psck)
    spi.init()
    rdr = mfrc522.MFRC522(spi=spi, gpioRst=deneyap.D0, gpioCs=deneyap.SDA)

    waiting_to_read = False
    buzzer = PWM(Pbuzzer)
    buzzer.freq(1047)

    while True:
        if not waiting_to_read:
            print("Kart Okutun")
            waiting_to_read = True

        (stat, tag_type) = rdr.request(rdr.REQIDL)

        if stat == rdr.OK:

            (stat, raw_uid) = rdr.anticoll()

            if stat == rdr.OK:
                waiting_to_read = False
                buzzer.duty(80)
                uid = "0x%02x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3], raw_uid[4])
                print(uid, "idli kart okundu")
                '''
                if rdr.select_tag(raw_uid) == rdr.OK:
                    print(uidlist[uid], "Okundu")
                else:
                    print("Select failed")
                '''
        sleep(0.5)
        buzzer.duty(0)

    buzzer.deinit()