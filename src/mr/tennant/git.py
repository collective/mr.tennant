import pickle
import zlib
import hashlib

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
            source = pickle.dumps(zope_object)
    return serialise_string(source, 'blob')


def serialise_directory(directory):
    hashes = {}
    modes = {}
    for filename, source in directory.items():
        if hasattr(source, 'isPrincipiaFolderish') and source.isPrincipiaFolderish:
            for item in serialise_directory(source):
                serialised = item[1] # the last item in the loop is the subtree
                yield item
            modes[filename] = "40000"
        else:
            serialised = serialise_object(source)
            modes[filename] = "100644"
            yield git_hash(serialised), serialised
        hashed = hashlib.sha1(serialised.decode("zip")).digest()
        hashes[filename] = hashed
    tree = []
    for filename in directory.keys():
        tree.append("%s %s\x00%s" % (modes[filename], filename, hashes[filename]))
    tree = "\x00".join(tree)
    with_header = serialise_string(tree, 'tree')
    yield git_hash(with_header), with_header
