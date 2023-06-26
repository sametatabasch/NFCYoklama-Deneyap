"""
NFC kullanarak yoklama alma işlermleri
"""
from lib.mfrc522 import MFRC522
from machine import Pin, SPI, SoftI2C
import deneyap
import network
import lib.urquest as urequests
import config
from time import sleep, time, gmtime, mktime, ticks_ms, ticks_diff
import ntptime
import json
import lib.ssd1306 as oledFW

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
    """

    """

    def __init__(self):
        self.ACCESS_KEY = None
        self.lcd_rows = [
            ["", -1],
            ["", -1],
            ["", -1],
            ["", -1],
            ["", -1],
            ["", -1],
            ["", -1],
            ["", -1]
        ]
        self.schedule = {}
        pin_miso = Pin(deneyap.MISO)
        pin_mosi = Pin(deneyap.MOSI)
        pin_sck = Pin(deneyap.SCK)

        self.i2c = SoftI2C(sda=Pin(deneyap.SDA), scl=Pin(deneyap.SCL))
        self.oled = oledFW.SSD1306_I2C(128, 64, self.i2c, addr=0x3d)

        self.oled.contrast(255)
        self.oled.invert(1)

        self.NFC_SPI = SPI(1, baudrate=2500000, polarity=0, phase=0, miso=pin_miso, mosi=pin_mosi, sck=pin_sck)
        self.NFC_SPI.init()
        self.NFC = MFRC522(spi=self.NFC_SPI, gpioRst=deneyap.D0, gpioCs=deneyap.SDA)

        self.NFC_SPI.deinit()
        self.connect_wifi(self)
        set_time()
        self.get_access_key()
        # start waiting
        self.wait()

    def get_access_key(self):
        """
        Access key expire in one day. İf self.ACCESS_KEY = None get new access key
        :return:
        """
        if not self.ACCESS_KEY:
            data = {
                "username": config.api_username,
                "password": config.api_passwd
            }
            url = config.api_url + "/login"

            response_data = self.send_request(url, data)
            if response_data:
                self.ACCESS_KEY = response_data['access_token']
            else:
                print("İstek başarısız!")
                return False

    def send_request(self, url: str, data: dict):
        """

        :param url:
        :param data:
        :return: json
        """
        json_data = json.dumps(data)
        response = urequests.post(url, headers={
            'Content-type': 'application/json',
            'Accept': '*/*',
            'Authorization': "" if not self.ACCESS_KEY else "Bearer " + self.ACCESS_KEY
        }, data=json_data)
        # İstek sonucunu kontrol etme
        if response.status_code == 200:
            print(url + " send request success")
            data = response.json()
            response.close()
            return data
        elif response.status_code == 401:
            print("401 Hatası")
            self.get_access_key()
            return self.send_request(url, data)
        else:
            print("İstek başarısız!")
            print("Durum kodu = " + str(response.status_code))
            print(response.json())
            response.close()
            return False

    def center(self, msg):
        """
        Find the start x pixel for centering
        :param msg: string to center
        :return int:
        """
        return (128 - len(msg) * 8) // 2  # width of oled is 128 px

    def show_on_screen(self):
        """

        :param rows: list: [[msg, x],... ] for centered text x= -1
        :return:
        """
        self.oled.fill(0)  # clear screen
        self.oled.hline(0, 12, 128, 1)  # draw horizontal line x=0, y=12, width=128, colour=1 center of 2. row
        self.oled.hline(0, 52, 128, 1)  # draw horizontal line x=0, y=52, width=128, colour=1 center of 7. row
        row_num = 1
        for row in self.lcd_rows:
            if len(row) > 0:
                startY = ((row_num - 1) * 8)
                self.oled.text(row[0], self.center(row[0]) if row[1] == -1 else row[1], startY if startY != 0 else 1, 1)
            row_num += 1
        self.oled.show()

    def get_schedule(self):
        self.lcd_rows[2] = ["Program icin", -1]
        self.lcd_rows[3] = ["Hoca Karti", -1]
        self.lcd_rows[4] = ["Okutun", -1]
        self.show_on_screen()

        instructor_card_id = self.read_card_uid()
        if instructor_card_id:
            self.lcd_rows[2] = ["Kart", -1]
            self.lcd_rows[3] = ["Kontrol", -1]
            self.lcd_rows[4] = ["Ediliyor", -1]
            self.show_on_screen()
            data = {
                "card_id": instructor_card_id
            }
            response_data = self.send_request(config.api_url + "/get_schedule", data)
            if response_data:
                self.schedule = json.loads(response_data['schedule'])
                return True
            else:
                self.lcd_rows[2] = ["", -1]
                self.lcd_rows[3] = ["Hoca Bulunamadi", -1]
                self.lcd_rows[4] = ["", -1]
                self.show_on_screen()
                sleep(2)
                return False
        else:
            return False

    def check_lesson_time(self):
        """
        It checks if we are at the lesson time and determines the lesson name.
        schedule= {
                    weekday : {
                            "lesson code" : [[startH, startM], [endH, endM]]  ,
                }
        :return: bool

        """
        try:
            day_lessons = self.schedule[str(tr_time()["weekday"])]
            for lesson, times in day_lessons.items():
                '''
                    The start time and end time in the schedule are returned to the mktime(decimal number) type.
                    Because time can be compared more easily in decimal number type.
                '''
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
                    self.lcd_rows[0] = [lesson, -1]  # set lesson name
                    return True
                else:
                    self.lcd_rows[0] = ["", -1]  # clear lesson name
                    continue
            return False
        except KeyError as e:
            '''
                If schedule has not this weekday, it throw KeyError
            '''
            self.lcd_rows[0] = ["", -1]  # clear lesson name
            return False

    def read_card_uid(self):
        """
        try to read NFC Card id in 10 second
        :return: string uid
        """
        self.NFC_SPI.init()
        start_time = ticks_ms()
        timeout = 10000  # 10 saniye süreyle okuma yapmaya çalış

        while ticks_diff(ticks_ms(), start_time) < timeout:
            (stat, tag_type) = self.NFC.request(self.NFC.REQIDL)

            if stat == self.NFC.OK:
                (stat, raw_uid) = self.NFC.anticoll()

                if stat == self.NFC.OK:
                    uid = "%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3])
                    self.NFC.stop_crypto1()
                    self.NFC_SPI.deinit()
                    return uid

        # Belirli süre içinde kart okunmadıysa, None değeri döndür
        self.NFC_SPI.deinit()
        return None


    def take_attendance(self):
        std_list = config.std_list

        try:
            self.lcd_rows[2] = ["Yoklama", -1]
            self.lcd_rows[3] = ["Icin", -1]
            self.lcd_rows[4] = ["Kart Okut", -1]
            self.show_on_screen()
            std_uid = self.read_card_uid()
            if std_uid:
                '''
                    If student card id read
                '''
                print(std_uid)

                self.lcd_rows[2] = ["", -1]
                self.lcd_rows[3] = [std_list.get(std_uid), -1]
                self.lcd_rows[4] = ["", -1]
                self.show_on_screen()
                sleep(1)  # sleep for showing student info
        except Exception as e:
            self.lcd_rows[2] = ["Ogrenci", -1]
            self.lcd_rows[3] = ["Kayitli", -1]
            self.lcd_rows[4] = ["Degil", -1]
            self.show_on_screen()
            sleep(1)
            print("unregistered student")
            print(e.args)

    def wait(self):
        """
        wait for lesson time
        :return:
        """
        print("wait")
        is_program_exist = False
        while not is_program_exist:
            is_program_exist = self.get_schedule()
        while True:
            if self.check_lesson_time():
                self.take_attendance()
            else:
                self.lcd_rows[0] = ["", -1]
                self.lcd_rows[2] = ["Ders", -1]
                self.lcd_rows[3] = ["bekleniyor", -1]
                self.lcd_rows[4] = ["", -1]
                self.show_on_screen()
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
            self.show_on_screen()
            sleep(1)
            pass
        return True
