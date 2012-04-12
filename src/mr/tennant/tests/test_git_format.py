import unittest2
from StringIO import StringIO

class test_object_serialisation(unittest2.TestCase):
    
    def test_object_serialisation(self):
        from mr.tennant.git import serialise_string
        
        serialised = serialise_string("hello world", file_type="blob")
        self.assertEqual(serialised, 'x\x9cK\xca\xc9OR04d\xc8H\xcd\xc9\xc9W(\xcf/\xcaI\x01\x00={\x06~')
        
    def test_file_serialisation(self):
        from mr.tennant.git import serialise_string, serialise_file
        
        hello_world = StringIO('hello world')
        serialised = serialise_file(hello_world)
        
        expected_serialised = serialise_string("hello world", file_type="blob")
        self.assertEqual(expected_serialised, serialised)
        
