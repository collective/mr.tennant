import unittest2

class test_object_serialisation(unittest2.TestCase):
    
    def test_object_serialisation(self):
        from mr.tennant.git import serialise_string
        
        hello_world = 'hello world'
        serialised = serialise_string(hello_world, file_type="blob")
        self.assertEqual(serialised, 'x\x9cK\xca\xc9OR04d\xc8H\xcd\xc9\xc9W(\xcf/\xcaI\x01\x00={\x06~')
        
    
