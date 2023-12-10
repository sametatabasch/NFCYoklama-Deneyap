from Display import Oled
from Buzzer import Buzzer
from time import sleep_ms

class NFCAttendanceError(Exception):

    def __init__(self, code=0):
        self.oled = Oled()
        self.buzzer =Buzzer()

        self.message = self.get_error_message(code=code)
        self.errno = code
        super().__init__(self.message)


    @staticmethod
    def get_error_message(code=0):
        messages = {
            0: "Bir hata oluştu",
            1: "Sunucu ile Bağlantı kurulamadı",
            2: "Access Key Alınamadı",
            3: "Yoklama alınırken hata oluştu Status yanlış",
            4: "Yoklaması Alınacak Ders oluşturulamadı",
            5: "",
            6: "",
            7: "",
            8: "",
        }
        return messages.get(code,False)

    def show_error(self):
        self.buzzer.beep(2)
        self.oled.rows[2] = ["Bir Hata Oldu", -1]
        self.oled.rows[3] = ["Tekrar", -1]
        self.oled.rows[4] = ["Deneyin", -1]
        self.oled.rows[7] = [self.errno, -1]
        self.oled.show()
        sleep_ms(2000)
