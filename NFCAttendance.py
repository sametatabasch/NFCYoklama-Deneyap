"""
NFC kullanarak yoklama alma işlermleri
"""
from lib.mfrc522 import MFRC522
from lib.pcd8544 import PCD8544_FRAMEBUF
from machine import Pin, SPI
import deneyap
import network
import config
from time import sleep, time, gmtime, mktime, ticks_ms, ticks_diff
import ntptime

wlan = None


def set_time():
    # if needed, overwrite default time server
    ntptime.host = "1.tr.pool.ntp.org"

    try:
        ntptime.settime()
    except Exception as err:
        print("Error syncing time")
        print(err.args)


def tr_time(is_tuple=False):
    """

    :return: tuple (year, month, mday, hour, minute, second, weekday, yearday)
    """
    tm = gmtime(time() + 10800)  # UTC+3

    return tm if is_tuple else {
        "year": tm[0],
        "month": tm[1],
        "mday": tm[2],
        "hour": tm[3],
        "minute": tm[4],
        "second": tm[5],
        "weekday": tm[6],
        "yearday": tm[7]
    }


class NFCAttendance():
    LCD, NFC = '', ''
    LCD_SPI, NFC_SPI = "", ""
    lcd_rows = [
        ["", -1],
        ["----------", -1],
        ["Yoklama", -1],
        ["Icin", -1],
        ["Kart Okut", -1],
        ["----------", -1]
    ]

    def __init__(self):
        self.connect_wifi(self)

        pin_miso = Pin(deneyap.MISO)
        pin_mosi = Pin(deneyap.MOSI)
        pin_sck = Pin(deneyap.SCK)

        self.NFC_SPI = SPI(1, baudrate=2500000, polarity=0, phase=0, miso=pin_miso, mosi=pin_mosi, sck=pin_sck)
        self.NFC_SPI.init()
        self.NFC = MFRC522(spi=self.NFC_SPI, gpioRst=deneyap.D0, gpioCs=deneyap.SDA)

        lcd_mosi = Pin(deneyap.D15)
        lcd_sck = Pin(deneyap.D1)
        self.LCD_SPI = SPI(2, baudrate=2000000, polarity=0, phase=0, mosi=lcd_mosi, sck=lcd_sck)
        self.LCD_SPI.init()
        lcd_cs = Pin(deneyap.D13)
        lcd_dc = Pin(deneyap.D14)
        lcd_rst = Pin(deneyap.D12)
        self.LCD = PCD8544_FRAMEBUF(spi=self.LCD_SPI, cs=lcd_cs, dc=lcd_dc, rst=lcd_rst)

        self.NFC_SPI.deinit()
        self.LCD_SPI.deinit()

        set_time()
        # start waiting
        self.wait()

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
        self.LCD_SPI.init()
        self.LCD.fclear()
        row_num = 1
        for row in self.lcd_rows:
            if len(row) > 0:
                self.LCD.text(row[0], self.center(row[0]) if row[1] == -1 else row[1], (row_num - 1) * 8, 1)

            row_num += 1
        self.LCD.show()
        self.LCD_SPI.deinit()

    def check_lesson_time(self):
        """
        It checks if we are at the lesson time and determines the lesson name.
        :return: bool
        """

        """
        todo internet bağlantısı ile api üzerinden ders adı alınacak
        :return:
        """
        """
                schedule= {
                    weekday : {
                            "lesson code" : [[startH, startM], [endH, endM]]  ,
                }
                """
        schedule = {
            4: {
                "BILP-201": [[8, 30], [9, 50]],
                "BILP-107": [[13, 0], [17, 0]]

            },
            5: {
                "BILP-201": [[12, 0], [13, 30]]

            }
        }
        try:
            day_lessons = schedule[tr_time()["weekday"]]
            for lesson, times in day_lessons.items():

                startT = tr_time()
                startT["hour"] = times[0][0]
                startT["minute"] = times[0][1]
                startT = mktime((startT["year"], startT["month"], startT["mday"], startT["hour"], startT["minute"],
                                 startT["second"], startT["weekday"], startT["yearday"]))
                endT = tr_time()
                endT["hour"] = times[1][0]
                endT["minute"] = times[1][1]
                endT = mktime((endT["year"], endT["month"], endT["mday"], endT["hour"], endT["minute"],
                               endT["second"], endT["weekday"], endT["yearday"]))

                if startT <= mktime(tr_time(True)) <= endT:
                    self.lcd_rows[0] = [lesson, -1]
                    return True
        except KeyError as e:
            return False

    def read_student_card_uid(self):
        """

        :return: string uid
        """
        self.lcd_rows[2] = ["Yoklama", -1]
        self.lcd_rows[3] = ["Icin", -1]
        self.lcd_rows[4] = ["Kart Okut", -1]
        self.show_lcd()
        self.NFC_SPI.init()
        waiting_to_read = False
        start_time = ticks_ms()
        while True:
            if not waiting_to_read:
                print("Kart Okutun")
                waiting_to_read = True

            (stat, tag_type) = self.NFC.request(self.NFC.REQIDL)

            if stat == self.NFC.OK:
                (stat, raw_uid) = self.NFC.anticoll()

                if stat == self.NFC.OK:
                    uid = "%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3])
                    self.NFC.stop_crypto1()
                    self.NFC_SPI.deinit()
                    return uid
            if ticks_diff(ticks_ms(), start_time) > 1000 * 60:
                break  # check every one minute lesson time

    def take_attendance(self):
        std_list = {
            "93bdd50b": "Samet ATABAS",
            "3413fc51": "Kart 1",
            "2aca190b": "Kart 2",
            "d226d935": "Dis",
            "d56ef659": "Personel"
        }

        std_uid = self.read_student_card_uid()
        print(std_uid)
        try:
            self.lcd_rows[2] = ["", -1]
            self.lcd_rows[3] = [std_list.get(std_uid), -1]
            self.lcd_rows[4] = ["", -1]
            self.show_lcd()
            sleep(1)
        except Exception as e:
            print("unregistered student")
            print(e.args)

    def wait(self):
        """
        wait for lesson time
        :return:
        """
        print("wait")
        while True:
            if self.check_lesson_time():
                self.take_attendance()
            else:
                # todo turn of ldc led
                self.lcd_rows[2] = ["Ders", -1]
                self.lcd_rows[3] = ["bekleniyor", -1]
                self.lcd_rows[4] = ["", -1]
                self.show_lcd()
                sleep(60 * 60 * 5)

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
