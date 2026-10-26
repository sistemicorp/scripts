#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2026
Martin Guthrie

"""
import io
import math
import shutil
import struct
import subprocess
import threading
import wave
from public.prism.drivers.common.stublogger import StubLogger


# this is the (example) version of the remote hardware
VERSION = "0.4.0"
DRIVER_TYPE = "SCANNER"

# Prism polls jig_closed_always() this often (driver dict "play_poll_sec"), faster
# polling restarts the script sooner after a scan
PLAY_POLL_SEC = 0.2

# Ready beep, a short tone played on the Prism computer with aplay
BEEP_FREQ_HZ = 2000
BEEP_SEC = 0.08
BEEP_VOLUME = 0.5          # 0 to 1
BEEP_RATE_HZ = 22050
BEEP_DELAY_SEC = 0.3       # the Prism textbox takes about this long to be ready
AUDIO_DEVICE = None        # aplay -D <device>, None for the default, see `aplay -L`
APLAY_TIMEOUT_SEC = 5


def beep_wav():
    """ :return: WAV file bytes of the ready beep tone """
    amplitude = BEEP_VOLUME * (2 ** 15 - 1)
    samples = [int(amplitude * math.sin(2 * math.pi * BEEP_FREQ_HZ * i / BEEP_RATE_HZ))
               for i in range(int(BEEP_SEC * BEEP_RATE_HZ))]
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)  # 16 bit
        w.setframerate(BEEP_RATE_HZ)
        w.writeframes(struct.pack("<{}h".format(len(samples)), *samples))
    return buf.getvalue()


class Scanner(object):
    """ Barcode Scanner HW Driver

    The scanner is in USB keyboard mode, so scans arrive in the Prism textbox,
    not through this driver.  The driver restarts the script after each scan,
    so the operator just keeps scanning.
    """

    def __init__(self, loggerIn=None):
        if loggerIn:
            self.logger = loggerIn
        else:
            self.logger = StubLogger()

        self._player_stopped = False
        self._close = False

        self._aplay = shutil.which("aplay")
        self._beep = beep_wav()
        self._audio_warned = False

    # TODO: beep on the scanner itself.  Scanners support this, but not in keyboard
    #       mode, it needs the scanner in a serial mode (USB-COM).

    def ready_beep(self, delay_sec=BEEP_DELAY_SEC):
        """ Beep after delay_sec, to tell the operator Prism is ready to scan, does not block """
        timer = threading.Timer(delay_sec, self._play_beep)
        timer.daemon = True
        timer.start()
        return timer

    def _audio_warn(self, msg):
        if not self._audio_warned:
            self.logger.warning("Ready beep disabled: {}".format(msg))
            self._audio_warned = True

    def _play_beep(self):
        if not self._aplay:
            self._audio_warn("'aplay' not found in PATH")
            return
        cmd = [self._aplay, "-q"]
        if AUDIO_DEVICE:
            cmd += ["-D", AUDIO_DEVICE]
        cmd.append("-")  # WAV from stdin
        try:
            result = subprocess.run(cmd, input=self._beep, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.PIPE, timeout=APLAY_TIMEOUT_SEC,
                                    check=False)
        except (OSError, subprocess.SubprocessError) as e:
            self._audio_warn(e)
            return
        if result.returncode != 0:
            self._audio_warn(result.stderr.decode(errors="replace").strip())

    def stop_player(self):
        """ Stop restarting the script, until start_player() """
        self._player_stopped = True
        self.logger.info("stop_player")

    def start_player(self):
        """ Restart the script after each scan """
        if self._player_stopped:
            self.logger.info("start_player")
        self._player_stopped = False

    def player_stopped(self):
        return self._player_stopped

    def jig_closed_always(self):
        """ "Auto" Jig Open/Close
        - NOTE: because Prism calls here every 1sec and because Prism needs to
                see the Jig Open/Close, it can take up to 2sec before Prism
                is ready to Scan again
        """
        if self._player_stopped:
            return False

        # toggle response so that Prism thinks the jig is opening and closing.
        temp = self._close
        self._close = not temp
        return temp
