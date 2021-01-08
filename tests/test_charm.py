# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import unittest

from ops.testing import Harness
from charm import MongoconsumerCharm


class TestCharm(unittest.TestCase):
    def test_recording_config_can_be_changed(self):
        harness = Harness(MongoconsumerCharm)
        self.addCleanup(harness.cleanup)
        harness.begin()
        harness.update_config({"record_events": "false"})
