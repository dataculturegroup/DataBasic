#! /usr/bin/python3
import subprocess

def find_locales():
    out = subprocess.run(['locale', '-a'], stdout=subprocess.PIPE).stdout
    try:
        # Even though I use utf8 on my system output from "locale -a"
        # included "bokml" in Latin-1. Then this won't work, but the
        # exception will.
        res = out.decode('utf-8')
    except:
        res = out.decode('latin-1')
    return res.rstrip('\n').splitlines()

if __name__ == "__main__":
    for loc in find_locales():
        print(loc)