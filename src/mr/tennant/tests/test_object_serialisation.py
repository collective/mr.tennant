import os
import unittest2
import tempfile

from mr.tennant.git import git_hash
from mr.tennant.git import serialise_object
from mr.tennant.testing import DAVID_INTEGRATION_TESTING

class test_object_serialisation(unittest2.TestCase):
    
    layer = DAVID_INTEGRATION_TESTING
    
    def test_python_script(self):
        from Products.PythonScripts.PythonScript import manage_addPythonScript
        manage_addPythonScript(self.layer['app'], 'example.py')
        script = self.layer['app']['example.py']
        serialised = serialise_object(script)
        
        try:
            cwd = os.getcwd()
            
            git_repo = tempfile.mkdtemp()
            with open(os.path.join(git_repo, "example.py"), 'wb') as real_file:
                # Duplicate the file on the filesystem
                real_file.write(script.manage_DAVget())
            os.chdir(git_repo)
            os.system("git init")
            os.system("git add example.py")
            os.system("git cia -m 'example'")
        finally:
            os.chdir(cwd)

        expected_hash = git_hash(serialised)
        path = os.path.join(git_repo, ".git", "objects", expected_hash[:2], expected_hash[2:])
        self.assertEqual(open(path, 'rb').read(), serialised)

