import os
import codecs
import shutil
import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, "data")


def read_dict_file(filename, separator=";"):
    with codecs.open(os.path.join(data_dir, filename), "r", encoding='utf-8') as f:
        return dict(line.rstrip().split(separator) for line in f if not line.startswith("#"))


def write_dict_file(filename, separator, dictionary, append = False, header = ""):
    target = os.path.join(data_dir, filename)
    backup = os.path.join(data_dir, "%s.%s.bak" % (filename, datetime.datetime.now().strftime("%Y%m%d.%H%M%S")))
    shutil.copyfile(target, backup)

    with codecs.open(target, "w+" if append else "w", encoding='utf-8') as f:
        if header:
            f.write("%s\n" % header)
        for (k,v) in dictionary.iteritems():
            f.write("%s%s%s\n" % (k, separator, v))


def read_settings():
    return read_dict_file("settings.txt", ":")