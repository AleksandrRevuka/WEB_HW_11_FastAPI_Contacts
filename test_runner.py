"""runner"""
import unittest

from tests import test_connect_db, test_repository_addressbook

ABTestSuite = unittest.TestSuite()
ABTestSuite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(test_repository_addressbook.TestAddressBook))
ABTestSuite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(test_connect_db.TestdConnectDB))

runner = unittest.TextTestRunner(verbosity=2)
runner.run(ABTestSuite)
