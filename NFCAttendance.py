"""
NFC kullanarak yoklama alma işlermleri
"""
from machine import Pin, SoftI2C
import deneyap
import network
import lib.urquest as urequests
import config
from time import sleep, time, gmtime, mktime, ticks_ms, ticks_diff
import ntptime
import json
import lib.ssd1306 as oledFW

from Buzzer import Buzzer
from NFCReader import NFC
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
        self.is_schedule_exist = False
        self.student_list = {}
        self.current_lesson_code = ""
        self.current_lesson_start_hour = 0

        self.i2c = SoftI2C(sda=Pin(deneyap.SDA), scl=Pin(deneyap.SCL))
        self.oled = oledFW.SSD1306_I2C(128, 64, self.i2c, addr=0x3d)

        self.oled.contrast(255)
        self.oled.invert(1)

        self.NFC = NFC()

        self.connect_wifi(self)
        set_time()
        self.get_access_key()
        self.buzzer = Buzzer(deneyap.D8)
        # start waiting
        self.wait()

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

        if response.status_code == 401:
            print("401 Kimlik Hatası")
            self.get_access_key()
            return self.send_request(url, data)
        return response

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

            response = self.send_request(url, data)

            if response.status_code == 200:
                self.ACCESS_KEY = response.json()['access_token']
            else:
                print("İstek başarısız!")
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
                self.oled.text(self.to_english(row[0]), self.center(row[0]) if row[1] == -1 else row[1],
                               startY if startY != 0 else 1, 1)
            row_num += 1
        self.oled.show()

    def get_schedule(self):
        self.lcd_rows[2] = ["Program icin", -1]
        self.lcd_rows[3] = ["Hoca Karti", -1]
        self.lcd_rows[4] = ["Okutun", -1]
        self.show_on_screen()

        instructor_card_id = self.NFC.read_card_uid()
        if instructor_card_id:
            self.lcd_rows[2] = ["Kart", -1]
            self.lcd_rows[3] = ["Kontrol", -1]
            self.lcd_rows[4] = ["Ediliyor", -1]
            self.show_on_screen()
            data = {
                "card_id": instructor_card_id
            }
            response = self.send_request(config.api_url + "/get_schedule", data)
            if response.status_code == 200:
                response_data = response.json()
                self.lcd_rows[2] = [response_data["name"], -1]
                self.lcd_rows[3] = [response_data["last_name"], -1]
                self.lcd_rows[4] = ["Programi Alindi", -1]
                self.show_on_screen()
                sleep(2)
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

    def add_new_student(self, student_card_uid):
        answer = input("Öğrenci bilgileri kaydedilsin mi? e/h \n")
        if answer == "e":
            self.lcd_rows[0] = ["", -1]
            self.lcd_rows[2] = ["Ogrenci Numarasi", -1]
            self.lcd_rows[3] = ["Kaydediliyor", -1]
            self.lcd_rows[4] = ["...", -1]
            self.show_on_screen()

            student_number = input("Öğrenci Numarasını girin:")

            student_data = {
                "student": {
                    "name": "",
                    "last_name": "",
                    "card_id": student_card_uid,
                    "student_number": student_number
                }
            }
            response = self.send_request(config.api_url + "/create_student", student_data)
            if response.status_code == 200:
                response_data = response.json()
                student = response_data['student']
                print(student["student_number"])
                print(student["card_id"])
                self.lcd_rows[0] = [student['student_number'], -1]
                self.lcd_rows[2] = ["Ogrenci Numarasi", -1]
                self.lcd_rows[3] = ["Kaydedildi", -1]
                self.lcd_rows[4] = ["", -1]
                self.show_on_screen()
                sleep(2)

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
                    self.current_lesson_code = lesson  # set lesson name
                    self.current_lesson_start_hour = times[0][0]  # set lesson name

                    self.lcd_rows[0] = [lesson, -1]
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

    def get_student(self, student_card_uid):
        self.lcd_rows[2] = ["Kart Kontrol", -1]
        self.lcd_rows[3] = ["Ediliyor", -1]
        self.lcd_rows[4] = ["", -1]
        self.show_on_screen()
        response = self.send_request(config.api_url + "/get_student", {"card_id": student_card_uid})
        if response.status_code == 200:
            return response.json().get('student')
        else:
            return False

    def take_attendance(self):
        try:
            self.lcd_rows[2] = ["Yoklama", -1]
            self.lcd_rows[3] = ["Icin", -1]
            self.lcd_rows[4] = ["Kart Okut", -1]
            self.show_on_screen()
            student_card_uid = self.NFC.read_card_uid()
            if student_card_uid:
                '''
                    If student card id read
                '''
                print(student_card_uid)
                student = self.get_student(student_card_uid)
                if student:
                    if self.current_lesson_code in student['lessons']:
                        # todo yoklama bilgisinin veri tabanına kaydı işlemleri yapılacak
                        attendance_data = {
                            "student_id": student['id'],
                            "lesson_code": self.current_lesson_code,
                            "start_hour": self.current_lesson_start_hour
                        }
                        response = self.send_request(config.api_url + "/take_attendance", attendance_data)
                        if response.status_code == 200:

                            self.lcd_rows[2] = [student['name'], -1]
                            self.lcd_rows[3] = [student['last_name'], -1]
                            self.lcd_rows[4] = [student['student_number'], -1]
                            self.show_on_screen()

                            sleep(2)  # sleep for showing student info
                        elif response.status_code == 429:
                            self.lcd_rows[2] = ["Zaten", -1]
                            self.lcd_rows[3] = ["Yoklama Kaydınız", -1]
                            self.lcd_rows[4] = ["Var", -1]
                            self.show_on_screen()

                            sleep(2)  # sleep for showing student info
                    else:
                        self.lcd_rows[2] = ["Derse", -1]
                        self.lcd_rows[3] = ["Kaydınız", -1]
                        self.lcd_rows[4] = ["Bununmuyor", -1]
                        self.show_on_screen()
                        sleep(2)  # sleep for showing student info
                else:
                    self.lcd_rows[2] = ["Kayıtsız Öğrenci", -1]
                    self.lcd_rows[3] = ["Kaydetmek için", -1]
                    self.lcd_rows[4] = ["Butona basın", -1]
                    self.show_on_screen()
                    buton_pin = Pin(deneyap.GPKEY, Pin.IN, Pin.PULL_UP)
                    # Buton 5 saniye içinde basılıp basılmadığını kontrol et
                    start_time = ticks_ms()  # Başlangıç zamanı
                    while ticks_diff(ticks_ms(), start_time) < 5000:
                        if buton_pin.value() == 0:  # Buton basıldıysa
                            self.add_new_student(student_card_uid)
                            sleep(0.5)  # 0.5 saniye bekle
                            break  # Döngüden çık
        except Exception as e:
            print("take_attendance hatası")
            print(e.args)

    def wait(self):
        """
        wait for lesson time
        :return:
        """
        print("wait")
        self.buzzer.beep(700,1000)
        while not self.is_schedule_exist:
            self.is_schedule_exist = self.get_schedule()
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
