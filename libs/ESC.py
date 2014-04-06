from RPIO import PWM
import time

############################################################################################
#
#  Class for managing each blade + motor configuration via its ESC
#
############################################################################################
class ESC:
    pwm = None
    RPIO_DMA_CHANNEL = 1

    def __init__(self, pin, name, dma):

        #---------------------------------------------------------------------------
        # The GPIO BCM numbered pin providing PWM signal for this ESC
        #---------------------------------------------------------------------------
        self.bcm_pin = pin

        #---------------------------------------------------------------------------
        # The PWM pulse width range required by this ESC in microseconds
        #---------------------------------------------------------------------------
        self.min_pulse_width = 1000
        self.max_pulse_width = 2000

        #---------------------------------------------------------------------------
        # The PWM pulse range required by this ESC
        #---------------------------------------------------------------------------
        self.current_pulse_width = self.min_pulse_width
        self.name = name

        #---------------------------------------------------------------------------
        # Initialize the RPIO DMA PWM
        #---------------------------------------------------------------------------
        if not PWM.is_setup():
            PWM.set_loglevel(PWM.LOG_LEVEL_ERRORS)
            PWM.setup(1)
            PWM.init_channel(self.RPIO_DMA_CHANNEL, 3000) # 3ms carrier period
        PWM.add_channel_pulse(self.RPIO_DMA_CHANNEL, self.bcm_pin, 0, self.current_pulse_width)


    def update(self, spin_rate):
        self.current_pulse_width = spin_rate

        if self.current_pulse_width < self.min_pulse_width:
            self.current_pulse_width = self.min_pulse_width
        if self.current_pulse_width > self.max_pulse_width:
            self.current_pulse_width = self.max_pulse_width

        PWM.add_channel_pulse(self.RPIO_DMA_CHANNEL, self.bcm_pin, 0, self.current_pulse_width)