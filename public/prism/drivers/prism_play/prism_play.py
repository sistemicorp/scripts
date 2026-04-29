#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021-2026
Martin Guthrie

"""
import os
from public.prism.drivers.prism_play.prism_play_pipe import PrismPlayPipe


try:
    # run locally
    from stublogger import StubLogger
except:
    # run from prism
    from public.prism.drivers.common.stublogger import StubLogger


class PrismPlay(object):

    VERSION = "0.1.0"
    DRIVER_TYPE = "PrismPlay"

    def __init__(self, channel, work_dir, loggerIn=None):
        if loggerIn:
            self.logger = loggerIn
        else:
            self.logger = StubLogger()

        # For example purposes, we will use the channel number as the unique ID and ID
        self._unique_id = channel
        self._id = channel

        self._artifact_path = None
        self._references = None
        self._play_received = False

        self.play_pipe = PrismPlayPipe(
            client=False, channel=channel, logger=self.logger, work_dir=work_dir
        )
        self.play_pipe.create()
        self.play_pipe.open()

    def version(self):
        """ Version of this driver.  Typically, this would be coming
        from the remote hardware.  The version of remote software/hardware
        should be something that is expected.

        :return:
        """
        return self.VERSION

    def unique_id(self):
        """ A string that uniquely identifies this piece of hardware.
        Used for tracking purposes.

        :return: string
        """
        return "{:04}".format(self._unique_id)

    def id(self):
        """ The id is related to the channel/slot number which is related
        to the physical locations of the test jigs.  Prism will arrange the
        slots such that the lowest id is channel/slot 0, etc

        :return: integer
        """
        return self._id

    def close(self):
        """ Always called at the end of a test sequence by Prism

        :return: None
        """

        self.logger.info("closing")
        self.play_pipe.close()

    # ---------------------------------------------------------------------------------------------
    # Prism Player functions
    #

    def jig_closed_detect(self):
        """ Called by Prism to see if the jig has been "closed" (started)

          - Returns True when play command is received from the prism_play_pipe, False otherwise
          - Sets internal variable for artifact and references passed in play command
        :return: <True|False>
        """

        # Reset artifact and references on each play command
        self._artifact_path = None
        self._references = None
        self._play_received = False

        msg = self.play_pipe.read(timeout=1)
        if msg and msg.get(self.play_pipe.Fields.CMD, None) == self.play_pipe.Cmd.PLAY:
            self.logger.info("Received play command: {}".format(msg))
            self._artifact_path = msg.get(self.play_pipe.Fields.ARTIFACT, None)
            self._references = msg.get(self.play_pipe.Fields.REFERENCES, None)
            self._play_received = True
            return True
        return False

    def show_pass_fail(self, p=False, f=False, o=False):
        """ Called by Prism with test status
        - can be used by this hardware to display test status, on LEDs for example.

        :param p: pass
        :param f: fail
        :param o: other (test in progress)
        """
        self.logger.info("pass: {}, Fail: {}, Other: {}".format(p, f, o))

        if o is True:
            status = PrismPlayPipe.Status.RUNNING
            result = None
        elif f is True:
            status = PrismPlayPipe.Status.COMPLETE
            result = PrismPlayPipe.Result.FAIL
        elif p is True:
            status = PrismPlayPipe.Status.COMPLETE
            result = PrismPlayPipe.Result.PASS
        else: # TODO: Check meaning of this status
            status = PrismPlayPipe.Status.IDLE
            result = None

        msg = {PrismPlayPipe.Fields.STATUS: status, PrismPlayPipe.Fields.RESULT: result}
        if not self.play_pipe.write(msg):
            self.logger.error("Failed to write pass/fail status to prism play pipe")

    def show_msg(self, msg: str):
        """ Called by Prism with test details in progress
        - can be used by hardware to display test status

        :param msg: channel/slot #, Test ID, Pass/Fail, State, %done, item#, total items
        """
        self.logger.info(msg)
        msg = {
            PrismPlayPipe.Fields.STATUS: PrismPlayPipe.Status.STEP,
            PrismPlayPipe.Fields.MESSAGE: msg
        }
        if not self.play_pipe.write(msg):
            self.logger.error("Failed to write step status to prism play pipe")

    def get_artifact_path(self):
        """ Get the artifact specified in the play command.

          - Update path based on the location of public/<work_dir> directory if needed.

        :return: artifact path or None
        """
        if not self._artifact_path:
            return None

        self.logger.debug(
            f"Original artifact path: {self._artifact_path}, "
            f"base path: {self.play_pipe.abs_work_path}"
        )
        _index = self._artifact_path.find(self.play_pipe.rel_work_path)
        if _index != -1:
            return os.path.join(
                self.play_pipe.abs_work_path,
                # +1 to remove leading slash
                self._artifact_path[_index + len(self.play_pipe.rel_work_path) + 1:]
            )
        return self._artifact_path

    def get_references(self):
        """ Get the references specified in the play command

        :return: list of references or None
        """
        return self._references

    def get_play_received(self):
        """ Get whether a play command has been received

          - Set in jig_closed_detect()

        :return: True if play command received, False otherwise
        """
        return self._play_received
