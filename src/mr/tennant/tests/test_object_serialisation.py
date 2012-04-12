import unittest2

from mr.tennant.testing import DAVID_INTEGRATION_TESTING

class test_object_serialisation(unittest2.TestCase):
    
    layer = DAVID_INTEGRATION_TESTING
    
    def test_python_script(self):
        raise KeyError()
    
