def serialise_string(string, file_type):
    with_header = "%s %d\x00%s" % (file_type, len(string), string)
    return with_header.encode("zip")