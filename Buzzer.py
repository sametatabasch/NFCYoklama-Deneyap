from machine import Pin, PWM
import time

import config


class BuzzerPwm:
    def __init__(self, pin_number):
        self.buzzer_pin = Pin(config.Buzzer.get("pin")) if pin_number is None else Pin(pin_number, Pin.OUT,
                                                                                       Pin.PULL_DOWN)
        self.buzzer_pwm = PWM(self.buzzer_pin)
        self.buzzer_pwm.deinit()

    def beep(self, count=1, freq=1000, duty=512):
        self.buzzer_pwm.init()
        for c in range(count):
            self.buzzer_pwm.freq(freq)  # Frekansı ayarla
            self.buzzer_pwm.duty(duty)  # Şiddeti ayarla (0-1023 arası)
            time.sleep_ms(500)
        self.buzzer_pwm.deinit()

    def test(self):
        self.buzzer_pwm.init()
        for fre in range(100, 1100, 100):
            print("Frekans:", fre, "Duty:", 500)
            self.buzzer_pwm.freq(fre)  # Frekansı ayarla
            self.buzzer_pwm.duty(500)  # Şiddeti ayarla (0-1023 arası)
            time.sleep_ms(1000)
        self.buzzer_pwm.deinit()


class Buzzer:
    def __init__(self, pin_number=None):
        self.buzzer_pin = Pin(config.Buzzer.get("pin")) if pin_number is None else Pin(pin_number, Pin.OUT)
        self.buzzer_pin.off()

    def beep(self, count=1, _sleep=250):
        for c in range(count):
            self.buzzer_pin.value(1)
            time.sleep_ms(_sleep)
            self.buzzer_pin.off()
            time.sleep_ms(_sleep)
