# boot.py -- run on boot-up
from NFCAttendance import NFCAttendance

try:
    app = NFCAttendance()

    app.show_student_name()

except KeyboardInterrupt:
    print("İşlem Sonlandırıldı ")
