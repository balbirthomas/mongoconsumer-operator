# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import unittest

from ops.testing import Harness
from charm import MongoconsumerCharm


class TestCharm(unittest.TestCase):
    def test_config_changed(self):
        harness = Harness(MongoconsumerCharm)
        self.addCleanup(harness.cleanup)
        harness.begin()
        self.assertEqual(list(harness.charm._stored.things), [])
        harness.update_config({"thing": "foo"})
        self.assertEqual(list(harness.charm._stored.things), ["foo"])
