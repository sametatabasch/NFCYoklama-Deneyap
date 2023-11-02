import deneyap
import lib.urquest as urequests
import config
from time import mktime, sleep_ms
import json
from boot import tr_time

from NFCReader import NFC
from Display import Oled
from Keypad import Keypad
from Buzzer import Buzzer

wlan = None


class NFCAttendance():
    """
    NFC kullanarak yoklama alma işlermleri
    """

    def __init__(self):
        self.ACCESS_KEY = None
        self.schedule = {}
        self.is_schedule_exist = False
        self.current_lesson_code = ""
        self.current_lesson_start_hour = 0

        self.NFC = NFC()
        self.oled = Oled()
        self.keypad = Keypad()
        self.buzzer = Buzzer(config.Pins.get("buzzer_pin"))

        self.get_access_key()
        # start waiting
        self.wait()

    def send_request(self, url: str, data: dict):
        """

        :param url:
        :param data:
        :return: json
        """
        try:
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
        except Exception as e:
            # todo bağlantı hatası olduğunda send request fonksiyonunu kullanan tüm fonksiyonlarda ne şekilde davranılacağı belirlenmeli
            print("Bağlantı Hatası")
            print(e)
            return False

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

    def get_schedule(self):
        self.oled.rows[2] = ["Program icin", -1]
        self.oled.rows[3] = ["Hoca Karti", -1]
        self.oled.rows[4] = ["Okutun", -1]
        self.oled.show()

        instructor_card_id = self.NFC.read_card_uid()
        if instructor_card_id:
            self.oled.rows[2] = ["Kart", -1]
            self.oled.rows[3] = ["Kontrol", -1]
            self.oled.rows[4] = ["Ediliyor", -1]
            self.oled.show()
            sleep_ms(2000)
            data = {
                "card_id": instructor_card_id
            }
            response = self.send_request(config.api_url + "/get_schedule", data)
            if response.status_code == 200:
                response_data = response.json()
                self.oled.rows[2] = [response_data["name"], -1]
                self.oled.rows[3] = [response_data["last_name"], -1]
                self.oled.rows[4] = ["Programi Alindi", -1]
                self.oled.show()
                sleep_ms(2000)
                self.schedule = json.loads(response_data['schedule'])
                return True
            else:
                self.oled.rows[2] = ["", -1]
                self.oled.rows[3] = ["Hoca Bulunamadi", -1]
                self.oled.rows[4] = ["", -1]
                self.oled.show()
                sleep_ms(2000)
                return False
        else:
            return False

    def add_new_student(self, student_card_uid):
        student_number = self.get_student_number_with_keypad()
        if student_number:

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
                self.oled.rows[0] = [student['student_number'], -1]
                self.oled.rows[2] = ["Ogrenci Numarasi", -1]
                self.oled.rows[3] = ["Kaydedildi", -1]
                self.oled.rows[4] = ["", -1]
                self.oled.show()
                sleep_ms(2000)

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

                    self.oled.rows[0] = [lesson, -1]
                    return True
                else:
                    self.oled.rows[0] = ["", -1]  # clear lesson name
                    continue
            return False
        except KeyError as e:
            '''
                If schedule has not this weekday, it throw KeyError
            '''
            self.oled.rows[0] = ["", -1]  # clear lesson name
            return False

    def get_student(self, student_data: dict):
        self.oled.rows[2] = ["Öğrenci Kontrol", -1]
        self.oled.rows[3] = ["Ediliyor", -1]
        self.oled.rows[4] = ["", -1]
        self.oled.show()
        sleep_ms(1000)
        response = self.send_request(config.api_url + "/get_student", student_data)
        if response.status_code == 200:
            return response.json().get('student')
        else:
            print("Öğrenci bilgileir alınırken sorun oldu")
            print(response)
            print(response.json())
            print(student_data)
            return False

    def card_attendance(self):
        try:
            self.oled.rows[2] = ["Yoklama", -1]
            self.oled.rows[3] = ["Icin", -1]
            self.oled.rows[4] = ["Kart Okut", -1]
            self.oled.rows[7] = ["*'a basılı tut", -1]
            self.oled.show()
            student_card_uid = self.NFC.read_card_uid()
            if student_card_uid:
                '''
                    If student card id read
                '''
                self.buzzer.beep()
                print(student_card_uid)
                self.save_attendance({'card_id': student_card_uid})

        except Exception as e:
            print("take_attendance hatası")
            print(e.args)
            self.oled.rows[2] = ["Bir Hata Oldu", -1]
            self.oled.rows[3] = ["Tekrar", -1]
            self.oled.rows[4] = ["Deneyin", -1]
            self.oled.show()
            sleep_ms(5000)

    def get_student_number_with_keypad(self):
        self.oled.rows[2] = ["Öğrenci :", -1]
        self.oled.rows[3] = ["Numarası", -1]
        self.oled.rows[4] = ["", -1]
        self.oled.rows[7] = ["A Sil | B Çık", -1]
        self.oled.show()
        sleep_ms(1000)
        keys = []
        while len(keys) < 9:
            key = self.keypad.get_key()
            if key == "A":
                keys.pop()
            elif key == "B":
                return False
            elif key in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]:
                keys.append(key)

            self.oled.rows[4] = ["".join(keys), -1]
            self.oled.show()
        self.oled.rows[2] = ["Onaylıyor", -1]
        self.oled.rows[3] = ["musunuz?", -1]
        self.oled.rows[4] = ["".join(keys), -1]
        self.oled.rows[7] = ["A Evet | B Çık", -1]
        self.oled.show()
        onay = self.keypad.get_key()
        if onay == "A":
            return "".join(keys)
        else:
            return False

    def manuel_attendance(self):
        std_number = self.get_student_number_with_keypad()
        if std_number:
            self.save_attendance({"student_number": std_number})
        else:
            return False

    def save_attendance(self, student_data):
        print("save_attendance")
        try:
            student = self.get_student(student_data)
            if student:
                if self.current_lesson_code in student['lessons']:
                    attendance_data = {
                        "student_id": student['id'],
                        "lesson_code": self.current_lesson_code,
                        "start_hour": self.current_lesson_start_hour
                    }
                    response = self.send_request(config.api_url + "/take_attendance", attendance_data)
                    if response.status_code == 200:
                        self.buzzer.beep(count=2)
                        self.oled.rows[2] = [student['name'], -1]
                        self.oled.rows[3] = [student['last_name'], -1]
                        self.oled.rows[4] = [student['student_number'], -1]
                        self.oled.show()

                        sleep_ms(2000)  # sleep for showing student info
                    elif response.status_code == 429:
                        self.buzzer.beep(count=3, _sleep=150)
                        self.oled.rows[2] = ["Zaten", -1]
                        self.oled.rows[3] = ["Yoklama Kaydınız", -1]
                        self.oled.rows[4] = ["Var", -1]
                        self.oled.show()

                        sleep_ms(2000)  # sleep for showing student info
                else:
                    self.buzzer.beep(count=3, _sleep=150)
                    self.oled.rows[2] = ["Derse", -1]
                    self.oled.rows[3] = ["Kaydınız", -1]
                    self.oled.rows[4] = ["Bununmuyor", -1]
                    self.oled.show()
                    sleep_ms(2000)  # sleep for showing student info
            else:
                self.oled.rows[2] = ["Kayıtsız Öğrenci", -1]
                if student_data.get("card_id"):
                    self.oled.rows[3] = ["Kaydetmek için", -1]
                    self.oled.rows[4] = ["A'ya basın", -1]
                    self.oled.show()

                    # Buton 5 saniye içinde basılıp basılmadığını kontrol et
                    key = self.keypad.get_key(5000)
                    if key == 'A':
                        if student_data.get("card_id") is not None:
                            self.add_new_student(student_data['card_id'])
                else:
                    self.oled.rows[3] = ["", -1]
                    self.oled.rows[4] = ["", -1]
                    self.oled.show()
                    sleep_ms(1000)
        except Exception as e:
            print("take_attendance hatası")
            print(e.args)
            self.oled.rows[2] = ["Bir Hata Oldu", -1]
            self.oled.rows[3] = ["Tekrar", -1]
            self.oled.rows[4] = ["Deneyin", -1]
            self.oled.show()
            sleep_ms(5000)

    def wait(self):
        """
        wait for lesson time
        :return:
        """
        print("wait")
        self.buzzer.beep(count=4, _sleep=150)
        while not self.is_schedule_exist:
            self.is_schedule_exist = self.get_schedule()
        while True:
            if self.check_lesson_time():
                self.card_attendance()
                key = self.keypad.get_key(500)
                if key == "*":
                    self.manuel_attendance()
            else:
                self.oled.rows[0] = ["", -1]
                self.oled.rows[2] = ["Ders", -1]
                self.oled.rows[3] = ["bekleniyor", -1]
                self.oled.rows[4] = ["", -1]
                self.oled.show()
                sleep_ms(60 * 60 * 5 * 1000)
