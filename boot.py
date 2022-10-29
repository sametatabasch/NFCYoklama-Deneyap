# boot.py -- run on boot-up
from NFCAttendance import NFCAttendance

try:
    app = NFCAttendance()
    app.LCD.clear()
    app.write_lesson_name()
    app.write_waiting_message()

    app.read_student_card()

except KeyboardInterrupt:
    print("İşlem Sonlandırıldı ")
