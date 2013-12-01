#!/usr/bin/python

import sys
import string

givers = [(name.strip(), email.strip()) for (name, email) in (line.split(',') for line in sys.stdin if line and not line.startswith ("#"))]

import random

def generate():

    for (name, email) in givers:
        password = ''.join( random.choice(string.ascii_letters) for i in range(5) )
        print "%s;%s" % (email, password)

if __name__ == "__main__":
    generate()