from lib import mfrc522
from machine import Pin, SPI
import deneyap

def do_write():

    spi = SPI(1, baudrate=2500000, polarity=0, phase=0, miso=Pin(deneyap.MISO), mosi=Pin(5), sck=Pin(19))
    spi.init()
    rdr = mfrc522.MFRC522(spi=spi, gpioRst=23, gpioCs=4)

    print("")
    print("Place card before reader to write address 0x08")
    print("")

    try:
        while True:

            (stat, tag_type) = rdr.request(rdr.REQIDL)

            if stat == rdr.OK:

                (stat, raw_uid) = rdr.anticoll()

                if stat == rdr.OK:
                    print("New card detected")
                    print("  - tag type: 0x%02x" % tag_type)
                    print("  - uid	 : 0x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]))
                    print("")

                    if rdr.select_tag(raw_uid) == rdr.OK:

                        key = b'\x83\xff\xff\xff\xff\xff'

                        if rdr.auth(rdr.AUTHENT1A, 8, key, raw_uid) == rdr.OK:
                            stat = rdr.write(8, b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f")
                            rdr.stop_crypto1()
                            if stat == rdr.OK:
                                print("Data written to card")
                            else:
                                print("Failed to write data to card")
                        else:
                            print("Authentication error")
                    else:
                        print("Failed to select tag")

    except KeyboardInterrupt:
        print("Bye")