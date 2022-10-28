"""
NFC kullanarak yoklama alma işlermleri
"""
from lib.mfrc522 import MFRC522
from lib.pcd8544 import PCD8544_FRAMEBUF
from machine import Pin, SPI
import deneyap


class NFCAttendance():
    LCD, NFC = '', ''

    def __init__(self):
        pin_miso = Pin(deneyap.MISO)
        pin_mosi = Pin(deneyap.MOSI)
        pin_sck = Pin(deneyap.SCK)

        nfc_spi = SPI(1, baudrate=2500000, polarity=0, phase=0, miso=pin_miso, mosi=pin_mosi, sck=pin_sck)
        lcd_spi = SPI(2, baudrate=2000000, polarity=0, phase=0, miso=pin_miso, mosi=pin_mosi, sck=pin_sck)
        nfc_spi.init()
        lcd_spi.init()
        self.NFC = MFRC522(spi=nfc_spi, gpioRst=deneyap.D0, gpioCs=deneyap.SDA)
        lcd_cs = Pin(deneyap.D13)
        lcd_dc = Pin(deneyap.D12)
        lcd_rst = Pin(deneyap.D1)
        self.LCD = PCD8544_FRAMEBUF(spi=lcd_spi, cs=lcd_cs, dc=lcd_dc, rst=lcd_rst)

    def write_lesson_name(self):
        lesson_name = "BILP-100"
        self.write_nth_row_center(lesson_name, 1)

    def write_waiting_message(self):
        self.write_nth_row_center("Yoklama", 2)
        self.write_nth_row_center("Icin", 3)
        self.write_nth_row_center("Kart Okut", 5)

    def center(self, msg):
        """
        Find the start x pixel for centering
        :param msg: string to center
        :return int:
        """
        return (self.LCD.width - len(msg) * 8) // 2

    def write_nth_row_center(self, msg, n):
        """
        write LCD nth rpw
        :param msg: string to write LCD
        :param n: LCD row number 1-6
        :return:
        """
        self.LCD.text(msg, self.center(msg), (n - 1) * 8, 1)
        self.LCD.show()
