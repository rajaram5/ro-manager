#!/usr/bin/python

"""
Module to test ROSRS synchronization RO manager commands

See: http://www.wf4ever-project.org/wiki/display/docs/RO+management+tool
"""

import sys
try:
    # Running Python 2.5 with simplejson?
    import simplejson as json
except ImportError:
    import json

from MiscLib import TestUtils

from rocommand import ro

from TestConfig import ro_test_config
from StdoutContext import SwitchStdout

from sync.RosrsSync import RosrsSync

import TestROSupport

class TestSyncCommands(TestROSupport.TestROSupport):
    """
    Test sync ro commands
    """
    def setUp(self):
        super(TestSyncCommands, self).setUp()
        self.__sync = RosrsSync(ro_test_config.ROSRS_URI, ro_test_config.ROSRS_USERNAME, ro_test_config.ROSRS_PASSWORD)
        self.__sync.postWorkspace()
        return

    def tearDown(self):
        super(TestSyncCommands, self).tearDown()
        self.__sync.deleteWorkspace()
        return

    # Actual tests follow

    def testNull(self):
        assert True, 'Null test failed'

    def testPushAll(self):
        """
        Push a Research Object to ROSRS.

        ro push [ <RO-name> [ -d <dir>] ] [ -r <rosrs_uri> ] [ -u <username> ] [ -p <password> ]
        """
        rodir = self.createTestRo("data/ro-test-1", "RO test status", "ro-testRoStatus")
        
        args = [
            "ro", "push",
            "-v" 
            ]
        with SwitchStdout(self.outstr):
            status = ro.runCommand(ro_test_config.CONFIGDIR, ro_test_config.ROBASEDIR, args)
        assert status == 0
        self.assertEqual(self.outstr.getvalue().count("ro push"), 1)
        self.deleteTestRo(rodir)
        return

    # Sentinel/placeholder tests

    def testUnits(self):
        assert (True)

    def testComponents(self):
        assert (True)

    def testIntegration(self):
        assert (True)

    def testPending(self):
        assert (False), "Pending tests follow"

# Assemble test suite

def getTestSuite(select="unit"):
    """
    Get test suite

    select  is one of the following:
            "unit"      return suite of unit tests only
            "component" return suite of unit and component tests
            "all"       return suite of unit, component and integration tests
            "pending"   return suite of pending tests
            name        a single named test to be run
    """
    testdict = {
        "unit":
            [ "testUnits"
            , "testNull"
            , "testPushAll"
            ],
        "component":
            [ "testComponents"
            ],
        "integration":
            [ "testIntegration"
            ],
        "pending":
            [ "testPending"
            ]
        }
    return TestUtils.getTestSuite(TestSyncCommands, testdict, select=select)

if __name__ == "__main__":
    TestUtils.runTests("TestBasicCommands.log", getTestSuite, sys.argv)

# End.
