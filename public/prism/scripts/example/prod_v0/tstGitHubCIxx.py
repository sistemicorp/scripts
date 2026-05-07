#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019-2026
Andrew Oaks

"""
import logging
from core.test_item import TestItem
from public.prism.api import ResultAPI

from public.prism.drivers.prism_play.prism_play import PrismPlay


# file and class name must match
class tstGitHubCIxx(TestItem):

    # Database key values slot assignments (0-4)
    KEY_SLOT_COMMIT_HASH = 0

    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("tst00xx.{}".format(self.chan))

        self.hw_prism_play = None

    def TST0xxSETUP(self):
        """  Setup up for testing
        - main purpose is to get a local handle to the connected hardware
        - store the ID of the hardware for tracking purposes

            {"id": "TST0xxSETUP",           "enable": true },

        """
        ctx = self.item_start()  # always first line of test
        _result = ResultAPI.RECORD_RESULT_INCOMPLETE

        drivers = self.shared_state.get_drivers(self.chan, type=PrismPlay.DRIVER_TYPE)
        self.logger.info(drivers)  # review this output to see HW attributes
        self.hw_prism_play = drivers[0]["obj"]["hwdrv"]

        if not self.hw_prism_play.get_play_received():
            self.log_bullet("ERROR: Prism play command not received")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        _result = ResultAPI.RECORD_RESULT_PASS
        self.item_end(_result)  # always last line of test

    def TST0xxTEARDOWN(self):
        """  Always called at the end of testing
        - process any cleanup, closing, etc
        - if there was a FAIL of an earlier test item, this is STILL called

            {"id": "TST0xxTEARDOWN",        "enable": true },

        """
        ctx = self.item_start()  # always first line of test

        # play sound based on whether passing or failing
        # NOTE: playing these sounds could have also been placed
        #       in the driver that implements player show_pass_fail()

        self.item_end(ResultAPI.RECORD_RESULT_PASS)  # always last line of test

    def TST001_KeyAdd(self):
        """ Example of adding a GitHub reference key to the test record for tracking purposes

        Content/order of the references is determined by the developer.  In this example
        $GITHUB_WORKFLOW_SHA is passed as the first reference.

        {"id": "TST001_KeyAdd",         "enable": true },
        """
        ctx = self.item_start()   # always first line of test

        github_refs = self.hw_prism_play.get_references()
        if not github_refs:
            self.logger.error("ERROR: References not passed in play command")
            self.log_bullet("ERROR: GitHub integration")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.log_bullet(f"Commit hash: {github_refs[0]}")
        ctx.record.add_key(
            "commit_hash", github_refs[0], slot=self.KEY_SLOT_COMMIT_HASH
        )

        self.item_end(ResultAPI.RECORD_RESULT_PASS)  # always last line of test

    def TST002_UseArtifact(self):
        """  Example of using the artifact downloaded from GitHub in a test

            {"id": "TST002_UseArtifact",           "enable": true },

        """
        ctx = self.item_start()  # always first line of test
        _result = ResultAPI.RECORD_RESULT_INCOMPLETE

        artifact_path = self.hw_prism_play.get_artifact_path()
        self.log_bullet(f"Artifact: {artifact_path}")
        if not artifact_path:
            self.logger.error("ERROR: Artifact path not passed in play command")
            self.log_bullet("ERROR: GitHub integration")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        # Do something with the artifact file
        try:
            with open(artifact_path, "r") as f:
                artifact_content = f.read()
                self.log_bullet(f"Artifact content: {artifact_content}")
            _result = ResultAPI.RECORD_RESULT_PASS
        except Exception as e:
            self.logger.error(f"Error reading artifact {artifact_path}: {e}")
            self.log_bullet("ERROR: GitHub integration")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.item_end(_result)  # always last line of test
