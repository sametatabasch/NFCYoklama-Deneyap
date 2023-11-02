import lib.ssd1306 as oledFW
from machine import Pin, SoftI2C
import deneyap,config


class Oled:

    def __init__(self, width: int = 128, height: int = 64, sda: int = None, scl: int = None, address=None):
        """

        :param width: Oled ekran genişliği (px)
        :type width: int
        :param height: Oled ekran yüksekliği (px)
        :type height: int
        :param sda: Oled ekran SDA pini
        :type sda: int
        :param scl: Oled ekran SCL pini
        :type scl: int
        :param address: Oled ekran I2C adresi
        """
        pin_sda = Pin(config.Display.get("SDA")) if sda is None else Pin(sda)
        pin_scl = Pin(config.Display.get("SCL")) if scl is None else Pin(scl)
        address = config.Display.get("i2c_address") if address is None else address
        self.width = width
        self.height = height
        self.rows = [
            ["", -1],
            ["", -1],
            ["", -1],
            ["", -1],
            ["", -1],
            ["", -1],
            ["", -1],
            ["", -1]
        ]
        self.i2c = SoftI2C(sda=pin_sda, scl=pin_scl)
        self.screen = oledFW.SSD1306_I2C(self.width, self.height, self.i2c, addr=address)

        self.screen.contrast(255)
        self.screen.invert(1)

    def center(self, msg):
        """
        Find the start x pixel for centering
        :param msg: string to center
        :return int:
        """
        return (self.width - len(msg) * 8) // 2

    def show(self, Startup=False):
        """

        :param rows: list: [[msg, x],... ] for centered text x= -1
        :return:
        """
        self.screen.fill(0)  # clear screen
        if not Startup:
            self.screen.hline(0, 12, 128, 1)  # draw horizontal line x=0, y=12, width=128, colour=1 center of 2. row
            self.screen.hline(0, 52, 128, 1)  # draw horizontal line x=0, y=52, width=128, colour=1 center of 7. row
        row_num = 1
        for row in self.rows:
            if len(row) > 0:
                startY = ((row_num - 1) * 8)
                self.screen.text(self.to_english(row[0]), self.center(row[0]) if row[1] == -1 else row[1],
                                 startY if startY != 0 else 1, 1)
            row_num += 1
        self.screen.show()

    def to_english(self, input_string: str):
        replacements = {
            "ç": "c",
            "ğ": "g",
            "ı": "i",
            "ö": "o",
            "ş": "s",
            "ü": "u",
            "Ç": "C",
            "Ğ": "G",
            "İ": "I",
            "Ö": "O",
            "Ş": "S",
            "Ü": "U"
        }

        result = input_string
        for turkish_char, english_char in replacements.items():
            result = result.replace(turkish_char, english_char)
        return result
