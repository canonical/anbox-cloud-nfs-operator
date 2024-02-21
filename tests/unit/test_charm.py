# Copyright 2023 Simon
# See LICENSE file for licensing details.

import unittest

from charm import NFSOperatorCharm
from ops.model import MaintenanceStatus
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(NFSOperatorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_install(self):
        # Check the charm is in MaintenanceStatus
        self.assertIsInstance(self.harness.model.unit.status, MaintenanceStatus)
