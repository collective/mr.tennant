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
    for filename, source in directory.items():
        serialised = serialise_object(source)
        hashed = hashlib.sha1(serialised.decode("zip")).digest()
        hashes[filename] = hashed
        yield git_hash(serialised), serialised
    tree = []
    for filename in directory.keys():
        tree.append("100644 %s\x00%s" % (filename, hashes[filename]))
    tree = "\x00".join(tree)
    with_header = serialise_string(tree, 'tree')
    yield git_hash(with_header), with_header
