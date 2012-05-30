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

def get_commits_for_history(obj, refs):
    from dm.historical import getObjectAt
    parent = None
    history = obj.undoable_transactions()
    history = history + [{'user_name':admin, 'time':obj._p_mtime, 'description':'Generated recent commit'}]
    commits = []
    for transaction in history:
        commit = {'username':transaction['user_name'].strip(), 'time':int(transaction['time']), 'description':transaction['description']}
        commit['obj'] = getObjectAt(obj, transaction['time'])
        try:
            tree = list(serialise_directory(commit['obj']))
        except ValueError:
            # This isn't a valid commit, the root is empty
            continue
        for subobj in tree:
            yield subobj # hash/serialised pair
        commit['tree'] = tree[-1][0]
        commits.append(commit)
    
    for commit in reversed(commits):
        msg = "tree %s\n" % commit['tree']
        if parent:
            msg += "parent %s\n" % parent
        if 'username' not in commit:
            commit['username'] = "unknown"
        msg += "author %(username)s <%(username)s@example.com> %(time)d +0000\n" % (commit)
        msg += "committer %(username)s <%(username)s@example.com> %(time)d +0000\n" % (commit)
        msg += "\n"
        msg += commit['description']
        msg = serialise_string(msg, "commit")
        yield (git_hash(msg), msg)
        parent = git_hash(msg)
    refs['HEAD'] = parent

def dump_objects(repo, objects, refs):
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

    for hashed, obj in objects:
        directory_path = os.path.join(repo, ".git", "objects", hashed[:2])
        if not os.path.exists(directory_path):
            os.mkdir(directory_path)
        path = os.path.join(directory_path, hashed[2:])
        with open(path, 'wb') as obj_file:
            obj_file.write(obj)

    refs_path = os.path.join(repo, ".git", "refs")
    if not os.path.exists(refs_path):
        os.mkdir(refs_path)
        os.mkdir(os.path.join(repo, ".git", "refs", "heads"))
        with open(os.path.join(repo, ".git", "refs", "heads", "master"), 'wb') as ref_file:
            ref_file.write(refs['HEAD'])
    with open(os.path.join(repo, ".git", "HEAD"), 'wb') as ref_file:
        ref_file.write("ref: refs/heads/master")
    
        
class export(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    def __call__(self):
        import tempfile
        repo = tempfile.mkdtemp()
    	
        refs = {} # This is filled in by get_commits_for_history before dump_objects needs it
    	dump_objects(repo, get_commits_for_history(self.context, refs=refs), refs=refs)
        return "<html><body><h1>Repository created</h1><p>%s</p></body></html>" % repo
        