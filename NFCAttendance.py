"""
NFC kullanarak yoklama alma işlermleri
"""
from lib.mfrc522 import MFRC522
from lib.pcd8544 import PCD8544_FRAMEBUF
from machine import Pin, SPI
import deneyap
import network
import config
from time import sleep

wlan = None


class NFCAttendance():
    LCD, NFC = '', ''
    lcd_rows = [
        ["", -1],
        ["----------", -1],
        ["Yoklama", -1],
        ["Icin", -1],
        ["Kart Okut", -1],
        ["----------", -1]
    ]

    def __init__(self):
        pin_miso = Pin(deneyap.MISO)
        pin_mosi = Pin(deneyap.MOSI)
        pin_sck = Pin(deneyap.SCK)

        nfc_spi = SPI(1, baudrate=2500000, polarity=0, phase=0, miso=pin_miso, mosi=pin_mosi, sck=pin_sck)
        nfc_spi.init()
        self.NFC = MFRC522(spi=nfc_spi, gpioRst=deneyap.D0, gpioCs=deneyap.SDA)

        lcd_mosi = Pin(deneyap.D15)
        lcd_sck = Pin(deneyap.D1)
        lcd_spi = SPI(2, baudrate=2000000, polarity=0, phase=0, mosi=lcd_mosi, sck=lcd_sck)
        lcd_spi.init()
        lcd_cs = Pin(deneyap.D13)
        lcd_dc = Pin(deneyap.D14)
        lcd_rst = Pin(deneyap.D12)
        self.LCD = PCD8544_FRAMEBUF(spi=lcd_spi, cs=lcd_cs, dc=lcd_dc, rst=lcd_rst)
        self.connect_wifi(self)
        self.set_lesson_name()

    def center(self, msg):
        """
        Find the start x pixel for centering
        :param msg: string to center
        :return int:
        """
        return (self.LCD.width - len(msg) * 8) // 2

    def show_lcd(self):
        """

        :param rows: list: [[msg, x],... ] for centered text x= -1
        :return:
        """
        self.LCD.fclear()
        row_num = 1
        for row in self.lcd_rows:
            if len(row) > 0:
                self.LCD.text(row[0], self.center(row[0]) if row[1] == -1 else row[1], (row_num - 1) * 8, 1)

            row_num += 1
        self.LCD.show()

    def set_lesson_name(self):
        """
        todo internet bağlantısı ile api üzerinden ders adı alınacak
        :return:
        """
        self.lcd_rows[0] = ['BILP-100', -1]

    def read_student_card(self):
        self.lcd_rows[2] = ["Yoklama", -1]
        self.lcd_rows[3] = ["Icin", -1]
        self.lcd_rows[4] = ["Kart Okut", -1]
        self.show_lcd()
        waiting_to_read = False
        while True:
            if not waiting_to_read:
                print("Kart Okutun")
                waiting_to_read = True

            (stat, tag_type) = self.NFC.request(self.NFC.REQIDL)

            if stat == self.NFC.OK:
                (stat, raw_uid) = self.NFC.anticoll()

                if stat == self.NFC.OK:
                    waiting_to_read = False
                    uid = "0x%02x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3], raw_uid[4])
                    self.lcd_rows[2] = ["Kart Okundu", -1]
                    self.lcd_rows[3] = [uid, -1]
                    self.show_lcd()

                    print(uid, "idli kart okundu")
                    '''
                    if rdr.select_tag(raw_uid) == rdr.OK:
                        print(uidlist[uid], "Okundu")
                    else:
                        print("Select failed")
                    '''

    @staticmethod
    def connect_wifi(self):
        global wlan
        wlan = network.WLAN(network.STA_IF)  # create a wlan object
        wlan.active(True)  # Activate the network interface
        wlan.disconnect()  # Disconnect the last connected WiFi
        wlan.connect(config.wifi['ssid'], config.wifi['password'])  # connect wifi
        while (wlan.ifconfig()[0] == '0.0.0.0'):
            self.lcd_rows[2] = ["Internet'e", -1]
            self.lcd_rows[3] = ["Baglaniyor", -1]
            self.lcd_rows[4] = ["", -1]
            self.show_lcd()
            sleep(1)
            pass
        return True
