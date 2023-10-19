from machine import Pin, PWM, DAC
import time

class Buzzer:
    def __init__(self, pin_number):
        self.buzzer_pin = Pin(pin_number)
        self.buzzer_pwm = PWM(self.buzzer_pin)

    def beep(self, frequency, duration_ms):
        self.buzzer_pwm.freq(frequency)  # Frekansı ayarla
        self.buzzer_pwm.duty(1000)  # Şiddeti ayarla (0-1023 arası)
        time.sleep_ms(duration_ms)
        self.buzzer_pwm.duty(0)
