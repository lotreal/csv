#!/usr/bin/env python
#-*- coding: utf-8 -*-
"Subversion pre-commit hook. "

import os
import sys

LOG_LEVEL = 0

def dump(obj):
    '''return a printable representation of an object for debugging'''
    newobj=obj
    if '__dict__' in dir(obj):
        newobj=obj.__dict__
        if ' object at ' in str(obj) and not newobj.has_key('__type__'):
            newobj['__type__']=str(obj)
        for attr in newobj:
            newobj[attr]=dump(newobj[attr])
    return newobj

class Context:
    def __init__(self):
        self.__branches = []

    def set_branches(self, repos):
        sys.path.append("%s/hooks" % repos)
        from config import branches
        self.__branches = branches
        
    def get_branches(self):
        return self.__branches

    def trim(self, fname):
        for b in self.__branches:
            trimed = fname[:len(b)]
            if (fname[:len(b)] == b):
                return fname[len(b):]
        return fname


class ChangeSet:
    def __init__(self, context):
        self.changes = []
        self.context = context
        for line in command_output(self.context.look_cmd % "changed").split("\n"):
            log(line)
            if line and line[0] in ("A", "U"):
                self.add(Change(line[0], line[4:]))

    def add(self, change):
        self.changes.append(change)

    def verify(self):
        for change in self.changes:
            log('verify %s' % change)
            self.verify_path(change)
            self.verify_content(change)

    def verify_path(self, change):
        paths = {
            'Javascript':  'a/js/',
            'Style': 'a/css/',
            'Image': 'a/img/',
            }

        def vp(fname, ftype):
             assert self.context.trim(fname).startswith(paths[ftype]), \
                 '%s must put in (%s)' % (ftype, fname)

        def verify_asset(change):
            if change.filetype != 'Other':
                return vp(change.filename, change.filetype)

        try:
            verify_asset(change)
        except AssertionError, args:
            change.error('%s' % args)

    def verify_content(self, change):
        pass

    def report(self):
        ec = 0
        for change in self.changes:
            if len(change.errors) > 0:
                ec += 1
                print_err(change.filename)
                for err in change.errors:
                    print_err("[ERROR] %s" % err)
        return ec

class Change:
    def __init__(self, action, filename):
        def get_filetype(fname):
            ext_dict = {
                'Javascript': ('.js'),
                'Style': ('.css'),
                'Image': ('.gif .jpg .png .jpeg'),
                }
            ext = os.path.splitext(fname)[1]
            for ftype in ext_dict:
                if ext and ext in ext_dict[ftype]:
                    return ftype
            return 'Other'

        self.action = action
        self.filename = filename
        self.filetype = get_filetype(filename)

        self.errors = []

    def error(self, message):
        log(message)
        self.errors.append(message)

    def __repr__(self):
        return '{A:"%s", F:"%s", T:"%s" }' % (self.action, self.filename, self.filetype)

def print_err(str):
    sys.stderr.write("%s\n" % str)

def log(str):
    LOG_LEVEL > 0 and print_err('[LOG] %s' % str)


def command_output(cmd):
    " Capture a command's standard output. "
    import subprocess
    return subprocess.Popen(
        cmd.split(), stdout=subprocess.PIPE).communicate()[0]

def files_changed(look_cmd):
    """ List the files added or updated by this transaction.

    "svnlook changed" gives output like:
    U   trunk/file1.cpp
    A   trunk/file2.cpp
    """
    def filename(line):
        return line[4:]
    def added_or_updated(line):
        return line and line[0] in ("A", "U")
    return [
        filename(line)
        for line in command_output(look_cmd % "changed").split("\n")
        if added_or_updated(line)]

def file_contents(filename, look_cmd):
    " Return a file's contents for this transaction. "
    return command_output(
        "%s %s" % (look_cmd % "cat", filename))

def contains_tabs(filename, look_cmd):
    " Return True if this version of the file contains tabs. "
    return "\t" in file_contents(filename, look_cmd)

def check_cpp_files_for_tabs(look_cmd):
    " Check files in this transaction are tab-free. "
    cpp_files_with_tabs = [
        ff for ff in files_changed(look_cmd)
        if contains_tabs(ff, look_cmd)]
    if len(cpp_files_with_tabs) > 0:
        print_err("The following files contain tabs:\n%s\n"
               % "\n".join(cpp_files_with_tabs))
        return len(cpp_files_with_tabs)



def main():
    usage = """usage: %prog REPOS TXN

Run pre-commit options on a repository transaction."""
    from optparse import OptionParser
    parser = OptionParser(usage=usage)
    parser.add_option("-r", "--revision",
                      help="Test mode. TXN actually refers to a revision.",
                      action="store_true", default=False)

    (opts, (repos, txn_or_rvn)) = parser.parse_args()
    look_opt = ("--transaction", "--revision")[opts.revision]
    look_cmd = "/usr/local/bin/svnlook %s %s %s %s" % (
        "%s", repos, look_opt, txn_or_rvn)

    context = Context()
    context.set_branches(repos)
    context.look_cmd = look_cmd

    log("<<< LOG_START")
    log(context.get_branches())
    log("opts.revision: %s" % opts.revision)
    log("LOOK_CMD: %s" % look_cmd)
    log(">>> LOG_END")

    cs = ChangeSet(context)
    cs.verify()
    return cs.report()
    # check_cpp_files_for_tabs(look_cmd)

if __name__ == "__main__":
    import sys
    sys.exit(main())
