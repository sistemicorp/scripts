#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021-2026
Martin Guthrie

"""
import os
import random
import shutil
import subprocess

try:
    # run locally
    from stublogger import StubLogger
except:
    # run from prism
    from public.prism.drivers.common.stublogger import StubLogger


# this is the (example) version of the remote hardware
VERSION = "0.2.0"
DRIVER_TYPE = "FAKE"


class Fake(object):
    """ Example of a hardware driver class
    - there is no hardware, this is a simulation

    """

    def __init__(self, loggerIn=None):
        if loggerIn: self.logger = loggerIn
        else: self.logger = StubLogger()

        # create an instance of the hardware driver...
        # this might be a serial port,
        #                 arduino-simple-rpc Instance,
        #                 VISA, etc
        self._hwdrv = None

        self._uniqie_id = random.randint(0, 999)
        self._id = random.randint(0, 999)

        base_dir = os.path.dirname(__file__)
        self.sound_pass_path = os.path.join(base_dir, "sound", "car_chirp_x.wav")
        self.sound_fail_path = os.path.join(base_dir, "sound", "warning_horn.wav")
        self._aplay_bin = shutil.which("aplay")
        self._audio_warned = False

    def version(self):
        """ Version of this driver.  Typically, this would be coming
        from the remote hardware.  The version of remote software/hardware
        should be something that is expected.

        :return:
        """
        # remote_version = self._hwdrv.version()
        return VERSION

    def unique_id(self):
        """ A string that uniquely identifies this piece of hardware.
        Used for tracking purposes.

        :return: string
        """
        return "{:04}".format(self._uniqie_id)

    def id(self):
        """ The id is related to the channel/slot number which is related
        to the physical locations of the test jigs.  Prism will arrange the
        slots such that the lowest id is channel/slot 0, etc

        :return: integer
        """
        return self._id

    def close(self):
        """ Always called at the end of a test sequence by Prism
        - perform any reset or closing of the hardware if the testing is done, or ended
        - note the result state (Pass|Fail) of the DUT is not known and should not be assumed,
          meaning that this hardware may be in an unknown state.  This close() function
          allows you to get back to a known state, if required.

        :return: None
        """
        self.logger.info("closing")

    def adc_read(self):
        """ Example of reading an ADC

        :return: float
        """
        return round(float(random.uniform(0, 10)), 3)

    def _play_wav(self, wav_path: str):
        """Play WAV via aplay if available; otherwise log and continue.

        Audio device is hardcoded for Docker stability.
        To use a different output, run inside the container:
           aplay -l
           aplay -L
        Then replace "plughw:CARD=Generic_1,DEV=0" below with a valid device string
        (for example: "plughw:CARD=Generic,DEV=3" for HDMI).
        """
        if not os.path.exists(wav_path):
            self.logger.warning("Audio file not found: {}".format(wav_path))
            return

        if not self._aplay_bin:
            if not self._audio_warned:
                self.logger.warning("Audio disabled: 'aplay' not found in PATH")
                self._audio_warned = True
            return

        try:
            result = subprocess.run(
                [self._aplay_bin, "-q", "-D", "plughw:CARD=Generic_1,DEV=0", wav_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=15,
            )
            if result.returncode != 0:
                stderr = (result.stderr or "").strip()
                if stderr:
                    self.logger.warning(
                        "aplay failed with return code {}: {}".format(result.returncode, stderr)
                    )
                else:
                    self.logger.warning("aplay failed with return code {}".format(result.returncode))
        except subprocess.TimeoutExpired:
            self.logger.warning("aplay timed out for {}".format(wav_path))
        except Exception as e:
            self.logger.warning("Audio playback error: {}".format(e))

    def play_sound(self, pass_fail: bool):
        """ Play a sound to indicate pass/fail
        - the example TST0xxTEARDOWN calls here
        - this could be called by show_pass_fail() below
        - this is blocking, play short sounds
        """
        wav_path = self.sound_pass_path if pass_fail else self.sound_fail_path
        self._play_wav(wav_path)

    # ---------------------------------------------------------------------------------------------
    # Prism Player functions
    #

    def jig_closed_detect(self):
        """ Called by Prism to see if the jig has been "closed" (started)
        - Needs to be enabled by hwdrv_fake.py:discover_channels:line ~95
        - Always report jig is closed as this is a Fake driver.

        :return: <True|False>
        """
        self.logger.info("False")
        return False

    def show_pass_fail(self, p=False, f=False, o=False):
        """ Called by Prism with test status
        - can be used by this hardware to display test status, on LEDs for example.

        :param p: pass
        :param f: fail
        :param o: other (test in progress)
        """
        self.logger.info("pass: {}, Fail: {}, Other: {}".format(p, f, o))

    def show_msg(self, msg: str):
        """ Called by Prism with test details in progress
        - can be used by hardware to display test status
        - examples
            show_msg  117 - INFO  : 0, TST0xxSETUP, UNKNOWN, STATE_RUNNING, 6%, 1, 15
            show_msg  117 - INFO  : 0, TST0xxSETUP, PASS, STATE_RUNNING, 6%, 1, 15
            show_msg  117 - INFO  : 0, TST0xxSETUP, PASS, STATE_RUNNING, 6%, 1, 15
            show_msg  117 - INFO  : 0, TST000_Meas, PASS, STATE_RUNNING, 13%, 2, 15
            show_msg  117 - INFO  : 0, TST000_Meas, PASS, STATE_RUNNING, 13%, 2, 15

        :param msg: csv: channel/slot #, Test ID, Pass/Fail, State, %done, item#, total items
        """
        self.logger.info(msg)

    #
    # Prism Player functions
    # ---------------------------------------------------------------------------------------------
