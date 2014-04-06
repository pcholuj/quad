import time
import smbus
import math
import logging
import RPIO
import struct
from config import config
import logging
from array import *


############################################################################################
#
#  Adafruit i2c interface plus performance / error handling changes
#
############################################################################################
class I2C:
    def __init__(self, address, bus=smbus.SMBus(1)):
        self.address = address
        self.bus = bus
        self.logger = logging.getLogger(config['logger']['name'])

    def reverseByteOrder(self, data):
        "Reverses the byte order of an int (16-bit) or long (32-bit) value"
        # Courtesy Vishal Sapre
        dstr = hex(data)[2:].replace('L','')
        byteCount = len(dstr[::2])
        val = 0
        for i, n in enumerate(range(byteCount)):
            d = data & 0xFF
            val |= (d << (8 * (byteCount - i - 1)))
            data >>= 8
        return val

    def write8(self, reg, value):
        "Writes an 8-bit value to the specified register/address"
        while True:
            try:
                self.bus.write_byte_data(self.address, reg, value)
                self.logger.debug('I2C: Wrote 0x%02X to register 0x%02X', value, reg)
                break
            except IOError, err:
                self.logger.exception('Error %d, %s accessing 0x%02X: Check your I2C address', err.errno, err.strerror, self.address)
                time.sleep(0.001)

    def writeList(self, reg, list):
        "Writes an array of bytes using I2C format"
        while True:
            try:
                self.bus.write_i2c_block_data(self.address, reg, list)
                break
            except IOError, err:
                self.logger.exception('Error %d, %s accessing 0x%02X: Check your I2C address', err.errno, err.strerror, self.address)
                time.sleep(0.001)

    def readU8(self, reg):
        "Read an unsigned byte from the I2C device"
        while True:
            try:
                result = self.bus.read_byte_data(self.address, reg)
                self.logger.debug('I2C: Device 0x%02X returned 0x%02X from reg 0x%02X', self.address, result & 0xFF, reg)
                return result
            except IOError, err:
                self.logger.exception('Error %d, %s accessing 0x%02X: Check your I2C address', err.errno, err.strerror, self.address)
                time.sleep(0.001)

    def readS8(self, reg):
        "Reads a signed byte from the I2C device"
        while True:
            try:
                result = self.bus.read_byte_data(self.address, reg)
                self.logger.debug('I2C: Device 0x%02X returned 0x%02X from reg 0x%02X', self.address, result & 0xFF, reg)
                if (result > 127):
                    return result - 256
                else:
                    return result
            except IOError, err:
                self.logger.exception('Error %d, %s accessing 0x%02X: Check your I2C address', err.errno, err.strerror, self.address)
                time.sleep(0.001)

    def readU16(self, reg):
        "Reads an unsigned 16-bit value from the I2C device"
        while True:
            try:
                hibyte = self.bus.read_byte_data(self.address, reg)
                result = (hibyte << 8) + self.bus.read_byte_data(self.address, reg+1)
                self.logger.debug('I2C: Device 0x%02X returned 0x%04X from reg 0x%02X', self.address, result & 0xFFFF, reg)
                if result == 0x7FFF or result == 0x8000:
                    logger.critical('I2C read max value')
                    time.sleep(0.001)
                else:
                    return result
            except IOError, err:
                self.logger.exception('Error %d, %s accessing 0x%02X: Check your I2C address', err.errno, err.strerror, self.address)
                time.sleep(0.001)

    def readS16(self, reg):
        "Reads a signed 16-bit value from the I2C device"
        while True:
            try:
                hibyte = self.bus.read_byte_data(self.address, reg)
                if (hibyte > 127):
                    hibyte -= 256
                result = (hibyte << 8) + self.bus.read_byte_data(self.address, reg+1)
                self.logger.debug('I2C: Device 0x%02X returned 0x%04X from reg 0x%02X', self.address, result & 0xFFFF, reg)
                if result == 0x7FFF or result == 0x8000:
                    logger.critical('I2C read max value')
                    time.sleep(0.001)
                else:
                    return result
            except IOError, err:
                self.logger.exception('Error %d, %s accessing 0x%02X: Check your I2C address', err.errno, err.strerror, self.address)
                time.sleep(0.001)
                
    def readList(self, reg, length):
        "Reads a a byte array value from the I2C device"
        while True:
            try:
                result = self.bus.read_i2c_block_data(self.address, reg, length)
                self.logger.debug('I2C: Device 0x%02X from reg 0x%02X', self.address, reg)
                return result
            except IOError, err:
                self.logger.exception('Error %d, %s accessing 0x%02X: Check your I2C address', err.errno, err.strerror, self.address)
                time.sleep(0.001)


############################################################################################
#
#  Gyroscope / Accelerometer class for reading position / movement
#
############################################################################################
class Accelerometr :
    i2c = None

    RPIO_SENSOR_DATA_RDY = 25
    # Registers/etc.
    __MPU6050_RA_XG_OFFS_TC= 0x00       # [7] PWR_MODE, [6:1] XG_OFFS_TC, [0] OTP_BNK_VLD
    __MPU6050_RA_YG_OFFS_TC= 0x01       # [7] PWR_MODE, [6:1] YG_OFFS_TC, [0] OTP_BNK_VLD
    __MPU6050_RA_ZG_OFFS_TC= 0x02       # [7] PWR_MODE, [6:1] ZG_OFFS_TC, [0] OTP_BNK_VLD
    __MPU6050_RA_X_FINE_GAIN= 0x03      # [7:0] X_FINE_GAIN
    __MPU6050_RA_Y_FINE_GAIN= 0x04      # [7:0] Y_FINE_GAIN
    __MPU6050_RA_Z_FINE_GAIN= 0x05      # [7:0] Z_FINE_GAIN
    __MPU6050_RA_XA_OFFS_H= 0x06    # [15:0] XA_OFFS
    __MPU6050_RA_XA_OFFS_L_TC= 0x07
    __MPU6050_RA_YA_OFFS_H= 0x08    # [15:0] YA_OFFS
    __MPU6050_RA_YA_OFFS_L_TC= 0x09
    __MPU6050_RA_ZA_OFFS_H= 0x0A    # [15:0] ZA_OFFS
    __MPU6050_RA_ZA_OFFS_L_TC= 0x0B
    __MPU6050_RA_XG_OFFS_USRH= 0x13     # [15:0] XG_OFFS_USR
    __MPU6050_RA_XG_OFFS_USRL= 0x14
    __MPU6050_RA_YG_OFFS_USRH= 0x15     # [15:0] YG_OFFS_USR
    __MPU6050_RA_YG_OFFS_USRL= 0x16
    __MPU6050_RA_ZG_OFFS_USRH= 0x17     # [15:0] ZG_OFFS_USR
    __MPU6050_RA_ZG_OFFS_USRL= 0x18
    __MPU6050_RA_SMPLRT_DIV= 0x19
    __MPU6050_RA_CONFIG= 0x1A
    __MPU6050_RA_GYRO_CONFIG= 0x1B
    __MPU6050_RA_ACCEL_CONFIG= 0x1C
    __MPU6050_RA_FF_THR= 0x1D
    __MPU6050_RA_FF_DUR= 0x1E
    __MPU6050_RA_MOT_THR= 0x1F
    __MPU6050_RA_MOT_DUR= 0x20
    __MPU6050_RA_ZRMOT_THR= 0x21
    __MPU6050_RA_ZRMOT_DUR= 0x22
    __MPU6050_RA_FIFO_EN= 0x23
    __MPU6050_RA_I2C_MST_CTRL= 0x24
    __MPU6050_RA_I2C_SLV0_ADDR= 0x25
    __MPU6050_RA_I2C_SLV0_REG= 0x26
    __MPU6050_RA_I2C_SLV0_CTRL= 0x27
    __MPU6050_RA_I2C_SLV1_ADDR= 0x28
    __MPU6050_RA_I2C_SLV1_REG= 0x29
    __MPU6050_RA_I2C_SLV1_CTRL= 0x2A
    __MPU6050_RA_I2C_SLV2_ADDR= 0x2B
    __MPU6050_RA_I2C_SLV2_REG= 0x2C
    __MPU6050_RA_I2C_SLV2_CTRL= 0x2D
    __MPU6050_RA_I2C_SLV3_ADDR= 0x2E
    __MPU6050_RA_I2C_SLV3_REG= 0x2F
    __MPU6050_RA_I2C_SLV3_CTRL= 0x30
    __MPU6050_RA_I2C_SLV4_ADDR= 0x31
    __MPU6050_RA_I2C_SLV4_REG= 0x32
    __MPU6050_RA_I2C_SLV4_DO= 0x33
    __MPU6050_RA_I2C_SLV4_CTRL= 0x34
    __MPU6050_RA_I2C_SLV4_DI= 0x35
    __MPU6050_RA_I2C_MST_STATUS= 0x36
    __MPU6050_RA_INT_PIN_CFG= 0x37
    __MPU6050_RA_INT_ENABLE= 0x38
    __MPU6050_RA_DMP_INT_STATUS= 0x39
    __MPU6050_RA_INT_STATUS= 0x3A
    __MPU6050_RA_ACCEL_XOUT_H= 0x3B
    __MPU6050_RA_ACCEL_XOUT_L= 0x3C
    __MPU6050_RA_ACCEL_YOUT_H= 0x3D
    __MPU6050_RA_ACCEL_YOUT_L= 0x3E
    __MPU6050_RA_ACCEL_ZOUT_H= 0x3F
    __MPU6050_RA_ACCEL_ZOUT_L= 0x40
    __MPU6050_RA_TEMP_OUT_H= 0x41
    __MPU6050_RA_TEMP_OUT_L= 0x42
    __MPU6050_RA_GYRO_XOUT_H= 0x43
    __MPU6050_RA_GYRO_XOUT_L= 0x44
    __MPU6050_RA_GYRO_YOUT_H= 0x45
    __MPU6050_RA_GYRO_YOUT_L= 0x46
    __MPU6050_RA_GYRO_ZOUT_H= 0x47
    __MPU6050_RA_GYRO_ZOUT_L= 0x48
    __MPU6050_RA_EXT_SENS_DATA_00= 0x49
    __MPU6050_RA_EXT_SENS_DATA_01= 0x4A
    __MPU6050_RA_EXT_SENS_DATA_02= 0x4B
    __MPU6050_RA_EXT_SENS_DATA_03= 0x4C
    __MPU6050_RA_EXT_SENS_DATA_04= 0x4D
    __MPU6050_RA_EXT_SENS_DATA_05= 0x4E
    __MPU6050_RA_EXT_SENS_DATA_06= 0x4F
    __MPU6050_RA_EXT_SENS_DATA_07= 0x50
    __MPU6050_RA_EXT_SENS_DATA_08= 0x51
    __MPU6050_RA_EXT_SENS_DATA_09= 0x52
    __MPU6050_RA_EXT_SENS_DATA_10= 0x53
    __MPU6050_RA_EXT_SENS_DATA_11= 0x54
    __MPU6050_RA_EXT_SENS_DATA_12= 0x55
    __MPU6050_RA_EXT_SENS_DATA_13= 0x56
    __MPU6050_RA_EXT_SENS_DATA_14= 0x57
    __MPU6050_RA_EXT_SENS_DATA_15= 0x58
    __MPU6050_RA_EXT_SENS_DATA_16= 0x59
    __MPU6050_RA_EXT_SENS_DATA_17= 0x5A
    __MPU6050_RA_EXT_SENS_DATA_18= 0x5B
    __MPU6050_RA_EXT_SENS_DATA_19= 0x5C
    __MPU6050_RA_EXT_SENS_DATA_20= 0x5D
    __MPU6050_RA_EXT_SENS_DATA_21= 0x5E
    __MPU6050_RA_EXT_SENS_DATA_22= 0x5F
    __MPU6050_RA_EXT_SENS_DATA_23= 0x60
    __MPU6050_RA_MOT_DETECT_STATUS= 0x61
    __MPU6050_RA_I2C_SLV0_DO= 0x63
    __MPU6050_RA_I2C_SLV1_DO= 0x64
    __MPU6050_RA_I2C_SLV2_DO= 0x65
    __MPU6050_RA_I2C_SLV3_DO= 0x66
    __MPU6050_RA_I2C_MST_DELAY_CTRL= 0x67
    __MPU6050_RA_SIGNAL_PATH_RESET= 0x68
    __MPU6050_RA_MOT_DETECT_CTRL= 0x69
    __MPU6050_RA_USER_CTRL= 0x6A
    __MPU6050_RA_PWR_MGMT_1= 0x6B
    __MPU6050_RA_PWR_MGMT_2= 0x6C
    __MPU6050_RA_BANK_SEL= 0x6D
    __MPU6050_RA_MEM_START_ADDR= 0x6E
    __MPU6050_RA_MEM_R_W= 0x6F
    __MPU6050_RA_DMP_CFG_1= 0x70
    __MPU6050_RA_DMP_CFG_2= 0x71
    __MPU6050_RA_FIFO_COUNTH= 0x72
    __MPU6050_RA_FIFO_COUNTL= 0x73
    __MPU6050_RA_FIFO_R_W= 0x74
    __MPU6050_RA_WHO_AM_I= 0x75

    __CALIBRATION_ITERATIONS = 100

    def __init__(self, address=0x68, dlpf=4):
        #-------------------------------------------------------------------------------------------
        # Set up the base logging
        #-------------------------------------------------------------------------------------------
        self.logger = logging.getLogger(config['logger']['name'])

        self.i2c = I2C(address)
        self.address = address
        self.grav_x_offset = 0.0
        self.grav_y_offset = 0.0
        self.grav_z_offset = 0.0
        self.gyro_x_offset = 0.0
        self.gyro_y_offset = 0.0
        self.gyro_z_offset = 0.0
        self.sensor_data = array('B', [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.result_array = array('h', [0, 0, 0, 0, 0, 0, 0])

        self.logger.info('Reseting MPU-6050')

        #---------------------------------------------------------------------------
        # Reset all registers
        #---------------------------------------------------------------------------
        self.logger.debug('Reset all registers')
        self.i2c.write8(self.__MPU6050_RA_PWR_MGMT_1, 0x80)
        time.sleep(5.0)
    
        #---------------------------------------------------------------------------
        # Sets sample rate to 1kHz/1+3 = 250Hz or 4ms
        ####### Code currently loops at 170Hz, so 250Hz guarantees fresh data ######
        ####### while allowing sufficient time to read it                     ######
        #---------------------------------------------------------------------------
        self.logger.debug('Sample rate 250Hz')
        self.i2c.write8(self.__MPU6050_RA_SMPLRT_DIV, 0x03)
        time.sleep(0.1)
    
        #---------------------------------------------------------------------------
        # Sets clock source to gyro reference w/ PLL
        #---------------------------------------------------------------------------
        self.logger.debug('Clock gyro PLL')
        self.i2c.write8(self.__MPU6050_RA_PWR_MGMT_1, 0x02)
        time.sleep(0.1)

        #---------------------------------------------------------------------------
        # Disable FSync, Use of DLPF => 1kHz sample frequency used above divided by the
        # sample divide factor.
        # 0x01 = 180Hz
        # 0x02 =  100Hz
        # 0x03 =  45Hz
        # 0x04 =  20Hz
        # 0x05 =  10Hz
        # 0x06 =   5Hz
        #---------------------------------------------------------------------------
        self.logger.debug('configurable DLPF to filter out non-gravitational acceleration for Euler')
        self.i2c.write8(self.__MPU6050_RA_CONFIG, dlpf)
        time.sleep(0.1)
    
        #---------------------------------------------------------------------------
        # Disable gyro self tests, scale of
        # 0x00 =  +/- 250 degrees/s
        # 0x08 =  +/- 500 degrees/s
        # 0x10 = +/- 1000 degrees/s
        # 0x18 = +/- 2000 degrees/s
        #---------------------------------------------------------------------------
        self.logger.debug('Gyro +/-500 degrees/s')
        self.i2c.write8(self.__MPU6050_RA_GYRO_CONFIG, 0x08)
        time.sleep(0.1)
    
        #---------------------------------------------------------------------------
        # Disable accel self tests, scale of +/-2g
        # 0x00 =  +/- 2g
        # 0x08 =  +/- 4g
        # 0x10 =  +/- 8g
        # 0x18 = +/- 16g
        #---------------------------------------------------------------------------
        self.logger.debug('Accel +/- 2g')
        self.i2c.write8(self.__MPU6050_RA_ACCEL_CONFIG, 0x00)
        time.sleep(0.1)

        #---------------------------------------------------------------------------
        # Setup INT pin to latch and AUX I2C pass through
        #---------------------------------------------------------------------------
        self.logger.debug('Enable interrupt')
        self.i2c.write8(self.__MPU6050_RA_INT_PIN_CFG, 0x20)
        time.sleep(0.1)
    
        #---------------------------------------------------------------------------
        # Enable data ready interrupt
        #---------------------------------------------------------------------------
        self.logger.debug('Interrupt data ready')
        self.i2c.write8(self.__MPU6050_RA_INT_ENABLE, 0x01)
        time.sleep(0.1)


    def readSensorsRaw(self):
        #---------------------------------------------------------------------------
        # Hard loop on the data ready interrupt until it gets set high.  This clears
        # the interrupt also - sleep is just 0.5ms as data is updates every 4ms - need
        # to allow time for the data to be read.  The alternative would be to have a
        # thread waking on the interrupt, but CPU efficiency here isn't a driving force.
        #---------------------------------------------------------------------------
        while not (self.i2c.readU8(self.__MPU6050_RA_INT_STATUS) == 0x01):
            time.sleep(0.0005)

        #---------------------------------------------------------------------------
        # For speed of reading, read all the sensors and parse to SHORTs after
        #---------------------------------------------------------------------------
        sensor_data = self.i2c.readList(self.__MPU6050_RA_ACCEL_XOUT_H, 14)

        for index in range(0, 14, 2):
            if (sensor_data[index] > 127):
                sensor_data[index] -= 256
            self.result_array[int(index / 2)] = (sensor_data[index] << 8) + sensor_data[index + 1]
        return self.result_array


    def readSensors(self):
        #---------------------------------------------------------------------------
        # +/- 2g 2 * 16 bit range for the accelerometer
        # +/- 500 degrees per second * 16 bit range for the gyroscope - converted to radians
        #---------------------------------------------------------------------------
        [ax, ay, az, temp, gx, gy, gz] = self.readSensorsRaw()

        fax = ax * 4.0 / 65536 - self.grav_x_offset
        fay = ay * 4.0 / 65536 - self.grav_y_offset
        faz = az * 4.0 / 65536 - self.grav_z_offset + 1.0

        fgx = gx * 1000.0 * math.pi / (65536 * 180) - self.gyro_x_offset
        fgy = gy * 1000.0 * math.pi / (65536 * 180) - self.gyro_y_offset
        fgz = gz * 1000.0 * math.pi / (65536 * 180) - self.gyro_z_offset

        return fax, fay, faz, fgx, -fgy, fgz
    
    def calibrateGyros(self):
        for loop_count in range(0, self.__CALIBRATION_ITERATIONS):
            [ax, ay, az, temp, gx, gy, gz] = self.readSensorsRaw()
            self.gyro_x_offset += gx
            self.gyro_y_offset += gy
            self.gyro_z_offset += gz

            time.sleep(0.05)

        self.gyro_x_offset *= 1000.0 * math.pi / (65536 * 180 * self.__CALIBRATION_ITERATIONS)
        self.gyro_y_offset *= 1000.0 * math.pi / (65536 * 180 * self.__CALIBRATION_ITERATIONS)
        self.gyro_z_offset *= 1000.0 * math.pi / (65536 * 180 * self.__CALIBRATION_ITERATIONS)


    def calibrateGravity(self, file_name):
        grav_x_offset = 0
        grav_y_offset = 0
        grav_z_offset = 0

        for loop_count in range(0, self.__CALIBRATION_ITERATIONS):
            [ax, ay, az, temp, gx, gy, gz] = self.readSensorsRaw()
            grav_x_offset += ax
            grav_y_offset += ay
            grav_z_offset += az

            time.sleep(0.05)

        grav_x_offset *= (4.0 / (65536 * self.__CALIBRATION_ITERATIONS))
        grav_y_offset *= (4.0 / (65536 * self.__CALIBRATION_ITERATIONS))
        grav_z_offset *= (4.0 / (65536 * self.__CALIBRATION_ITERATIONS))

        #---------------------------------------------------------------------------
        # Open the offset config file
        #---------------------------------------------------------------------------
        cfg_rc = True
        try:
            with open(file_name, 'w+') as cfg_file:
                cfg_file.write('%f\n' % grav_x_offset)
                cfg_file.write('%f\n' % grav_y_offset)
                cfg_file.write('%f\n' % grav_z_offset)
                cfg_file.flush()

        except IOError, err:
            self.logger.critical('Could not open offset config file: %s for writing', file_name)
            cfg_rc = False

        return cfg_rc


    def readGravity(self, file_name):
        #---------------------------------------------------------------------------
        # Open the Offsets config file, and read the contents
        #---------------------------------------------------------------------------
        cfg_rc = True
        try:
            with open(file_name, 'r') as cfg_file:
                str_grav_x_offset = cfg_file.readline()
                str_grav_y_offset = cfg_file.readline()
                str_grav_z_offset = cfg_file.readline()

            self.grav_x_offset = float(str_grav_x_offset)
            self.grav_y_offset = float(str_grav_y_offset)
            self.grav_z_offset = float(str_grav_z_offset)

        except IOError, err:
            self.logger.critical('Could not open offset config file: %s for reading', file_name)
            cfg_rc = False

        return cfg_rc

    def getEulerAngles(self, fax, fay, faz):
        #---------------------------------------------------------------------------
        # What's the angle in the x and y plane from horizontal in radians?
        # Note fax, fay, fax are all the calibrated outputs reading 0, 0, 0 on
        # horizontal ground as a measure of speed in a given direction.  For Euler we
        # need to re-add gravity of 1g so the sensors read 0, 0, 1 for a horizontal setting
        #---------------------------------------------------------------------------
        
        pitch = math.atan2(fax, math.pow(math.pow(faz, 2) + math.pow(fay, 2), 0.5))
        roll = math.atan2(fay,  math.pow(math.pow(faz, 2) + math.pow(fax, 2), 0.5))
        tilt = math.atan2(math.pow(math.pow(fax, 2) + math.pow(fay, 2), 0.5), faz)
        return pitch, roll, tilt