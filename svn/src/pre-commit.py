#!/usr/bin/env python
#-*- coding: utf-8 -*-
"Subversion pre-commit hook. "

import os
import sys

exit_code = 0

class Configuration:
    def __init__(self):
        self.__branches = []

    def load_from_repos(self, repos):
        sys.path.append("%s/hooks" % repos)
        from config import branches
        self.__branches = branches
        
    def get_branch(self):
        return self.__branches

_conf = Configuration()

def get_conf():
    global _conf
    return _conf

def log(str):
    pass

def print_err(str):
    global exit_code
    exit_code += 1
    sys.stderr.write("%s\n" % str)

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


def check_assets_path(look_cmd):
    """ Check assets's path. 

    css:    a/css
    js:     a/js
    images: a/img"""
    def is_js_file(fname):
        return os.path.splitext(fname)[1] in ".js".split()

    def is_css_file(fname):
        return os.path.splitext(fname)[1] in ".css".split()

    def is_img_file(fname):
        return os.path.splitext(fname)[1] in ".gif .jpg .png .jpeg".split()

    def trim_branches(fname):
        for b in get_conf().get_branch():
            trimed = fname[:len(b)]
            if (fname[:len(b)] == b):
                return fname[len(b):]
        return fname

    def js_path_error(fname):
        return trim_branches(fname)[:5] != 'a/js/'

    def css_path_error(fname):
        return trim_branches(fname)[:6] != 'a/css/'

    def img_path_error(fname):
        return trim_branches(fname)[:6] != 'a/img/'

    files = files_changed(look_cmd)

    for i in [js for js in files 
              if is_js_file(js) and js_path_error(js)]:
        print_err('[rule=/a/js/]  but: "%s"' % i)

    for i in [css for css in files 
              if is_css_file(css) and css_path_error(css)]:
        print_err('[rule=/a/css/] but: "%s"' % i)

    for i in [img for img in files 
              if is_img_file(img) and img_path_error(img)]:
        print_err('[rule=/a/img/] but: "%s"' % i)


    cpp_files_with_tabs = [
        ff for ff in files_changed(look_cmd)
        ]
    # if len(cpp_files_with_tabs) > 0:
    #     sys.stderr.write("The assets:\n%s\n"
    #                      % "\n".join(cpp_files_with_tabs))
    #     return len(cpp_files_with_tabs)




def main():
    usage = """usage: %prog REPOS TXN

Run pre-commit options on a repository transaction."""
    from optparse import OptionParser
    parser = OptionParser(usage=usage)
    parser.add_option("-r", "--revision",
                      help="Test mode. TXN actually refers to a revision.",
                      action="store_true", default=False)
    errors = 0

    (opts, (repos, txn_or_rvn)) = parser.parse_args()
    look_opt = ("--transaction", "--revision")[opts.revision]
    look_cmd = "/usr/local/bin/svnlook %s %s %s %s" % (
        "%s", repos, look_opt, txn_or_rvn)

    get_conf().load_from_repos(repos);

    log("<<< LOG_START")
    log(get_conf().get_branch())
    log("opts.revision: %s" % opts.revision)
    log("LOOK_CMD: %s" % look_cmd)
    log(">>> LOG_END")
    # check_cpp_files_for_tabs(look_cmd)
    check_assets_path(look_cmd)

if __name__ == "__main__":
    import sys
    main()
    log('exit_code: %s' % exit_code)
    sys.exit(exit_code)
