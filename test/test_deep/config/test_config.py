import sys
import unittest

from deep.config import IN_APP_INCLUDE


class ConfigTest(unittest.TestCase):
    def test_in_app_includes(self):

        modules = sys.modules

        include = IN_APP_INCLUDE()
        self.assertEqual(include, [sys.exec_prefix])
