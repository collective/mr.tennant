import os
import pickle
import zlib
import hashlib

from Acquisition import aq_base


def git_hash(serialised):
    return hashlib.sha1(serialised.decode("zip")).hexdigest()

def serialise_string(string, file_type):
    with_header = "%s %u\x00%s" % (file_type, len(string), string)
    return zlib.compress(with_header, 1)

def serialise_file(f):
    f.seek(0)
    string = f.read()
    return serialise_string(string, 'blob')

def serialise_object(zope_object):
    try:
        source = zope_object.manage_DAVget()
    except AttributeError:
        if isinstance(zope_object, str):
            # Workaround for mocks. This package is evil, it deserves evil hacks
            source = zope_object
        else:
            raise
    return serialise_string(source, 'blob')

def serialise_directory(directory):
    hashes = {}
    modes = {}
    if not directory.items():
        raise ValueError("Empty directory")
    for filename, source in directory.items():
        unwrapped = aq_base(source)
        if hasattr(unwrapped, 'isPrincipiaFolderish') and unwrapped.isPrincipiaFolderish:
            print ("Recursing into %s" % filename)
            items = None
            if hasattr(unwrapped, "items"):
                items = source.items
            if items is None:
                if hasattr(unwrapped, "objectItems"):
                    items = source.objectItems
            if items is None:
                items = lambda:[]
            if not items():
                # Empty subtree, don't export it
                print filename, "seems empty"
                continue
            for item in serialise_directory(source):
                serialised = item[1] # the last item in the loop is the subtree
                yield item
            modes[filename] = "40000"
        else:
            try:
                serialised = serialise_object(source)
                modes[filename] = "100644"
            except:
                # We can't serialise this object, it's probably not codeish
                print "Can't get", filename
                if filename == "example.py":
                    import pdb; pdb.set_trace( )
                continue
            else:
                yield git_hash(serialised), serialised
        hashed = hashlib.sha1(serialised.decode("zip")).digest()
        hashes[filename] = hashed
    tree = []
    for filename in sorted(directory.keys()):
        if filename not in hashes:
            # We didn't generate a hash, its most likely an empty directory
            print "Giving up on", filename
            continue
        tree.append("%s %s\x00%s" % (modes[filename], filename, hashes[filename]))
    tree = "".join(tree)
    with_header = serialise_string(tree, 'tree')
    yield git_hash(with_header), with_header

def serialise_commit(tree, message="initial", parent=None):
    return serialise_string("""tree %s
committer Zope <zope@example.com> 1243040974 -0700

%s""" % (tree, message), "commit")

def get_commits_for_history(obj):
    from dm.historical import getHistory
    objects = {}
    history = reversed(getHistory(obj))
    parent = None
    for obj in history:
        try:
            tree = list(serialise_directory(obj['obj']))
        except ValueError:
            # This isn't a valid commit, the root is empty
            continue
        objects.update(dict(tree))
        commit = "tree %s\n" % tree[-1][0]
        if parent:
            commit += "parent %s\n" % parent
        commit += "author %s <%s@example.com> %d +0000\n" % (obj['user_name'].strip(), obj['user_name'].strip(), int(obj['time']))
        commit += "committer %s <%s@example.com> %d +0000\n" % (obj['user_name'].strip(), obj['user_name'].strip(), int(obj['time']))
        commit += "\n"
        commit += obj['description']
        commit = serialise_string(commit, "commit")
        objects[git_hash(commit)] = commit
        parent = git_hash(commit)
    return objects.items(), parent

def dump_objects(repo, objects, HEAD):
    """
    from mr.tennant.git import dump_objects, serialise_directory, serialise_commit
    repo = tempfile.mkdtemp()
    tree = list(serialise_directory(folderish_object))
    commit = serialise_commit(tree[-1][0])
    objects = tree
    objects.append([git_hash(commit), commit])
    dump_objects(repo, objects, HEAD=git_hash(commit))
    """
    git_path = os.path.join(repo, ".git")
    if not os.path.exists(git_path):
        os.mkdir(git_path)
    objects_path = os.path.join(repo, ".git", "objects")
    if not os.path.exists(objects_path):
        os.mkdir(objects_path)

    refs_path = os.path.join(repo, ".git", "refs")
    if not os.path.exists(refs_path):
        os.mkdir(refs_path)
        os.mkdir(os.path.join(repo, ".git", "refs", "heads"))
        with open(os.path.join(repo, ".git", "refs", "heads", "master"), 'wb') as ref_file:
            ref_file.write(HEAD)
    with open(os.path.join(repo, ".git", "HEAD"), 'wb') as ref_file:
        ref_file.write("ref: refs/heads/master")
    
    for hashed, obj in objects:
        directory_path = os.path.join(repo, ".git", "objects", hashed[:2])
        if not os.path.exists(directory_path):
            os.mkdir(directory_path)
        path = os.path.join(directory_path, hashed[2:])
        with open(path, 'wb') as obj_file:
            obj_file.write(obj)
        
class export(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    def __call__(self):
        import tempfile
        repo = tempfile.mkdtemp()
    	objects, HEAD = get_commits_for_history(self.context)
    	dump_objects(repo, objects, HEAD=HEAD)
        return "<html><body><h1>Repository created</h1><p>%s</p></body></html>" % repo
        