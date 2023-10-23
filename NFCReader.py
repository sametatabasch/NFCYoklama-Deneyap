from lib.mfrc522 import MFRC522
import deneyap
from machine import SPI, Pin

from time import ticks_ms, ticks_diff


class NFC:
    def __init__(self, miso: int = None, mosi: int = None, sck: int = None, rst: int = None, cs: int = None):
        pin_miso = Pin(deneyap.MISO) if miso is None else Pin(miso)
        pin_mosi = Pin(deneyap.MOSI) if mosi is None else Pin(mosi)
        pin_sck = Pin(deneyap.SCK) if sck is None else Pin(sck)
        pin_rst = deneyap.D0 if rst is None else rst
        pin_cs = deneyap.D1 if rst is None else cs
        self.NFC_SPI = SPI(1, baudrate=2500000, polarity=0, phase=0, miso=pin_miso, mosi=pin_mosi, sck=pin_sck)
        self.NFC_SPI.init()
        self.Reader = MFRC522(spi=self.NFC_SPI, gpioRst=pin_rst, gpioCs=pin_cs)

        self.NFC_SPI.deinit()
        print("NFCReader")

    def read_card_uid(self):
        """
        try to read NFC Card id in 10 second
        :return: string uid
        """
        self.NFC_SPI.init()
        start_time = ticks_ms()
        timeout = 1000  # 10 saniye süreyle okuma yapmaya çalış

        while ticks_diff(ticks_ms(), start_time) < timeout:
            (stat, tag_type) = self.Reader.request(self.Reader.REQIDL)

            if stat == self.Reader.OK:
                (stat, raw_uid) = self.Reader.anticoll()

                if stat == self.Reader.OK:
                    uid = "%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3])
                    self.Reader.stop_crypto1()
                    self.NFC_SPI.deinit()
                    return uid

        # Belirli süre içinde kart okunmadıysa, None değeri döndür
        self.NFC_SPI.deinit()
        return None
