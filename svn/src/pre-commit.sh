#!/bin/sh
export LANG=en_US.UTF-8

REPOS="$1"
TXN="$2"
TYPE="$3"
if test -z "$TYPE" ; then
    TYPE="-t"
fi

SVNLOOK=/usr/local/bin/svnlook

look() {  
    $SVNLOOK "$@" "$TYPE" "$TXN" "$REPOS"  
}  

if look log | grep '.' > /dev/null ; then :; else  
    echo "Must fill in SVN log" 1>&2
    exit 1  
fi  

# Make sure that the log message contains some text.
if [ "$(look log | wc -m)" -lt 4 ]; then 
    echo "SVN log contains at least three chars" 1>&2
    exit 1 
fi 

disexts='\.(bak|tmp|o|obj|log|rar|zip|7z|gz|tar|tgz)$'
disfiles='(^|/)(Thumbs\.db|desktop\.ini)$'
disdirs='(^|/)(_notes|\.DS_Store|_runtime|cache|tmp|temp)/$'
disdot='(^|/)(\.)'
diss="$disexts|$disfiles|$disdirs|$disdot"

if look changed | grep '^A ' | sed -r 's#^A +##' | grep -iE $diss 1>&2 ; then
    echo "Temporary files can not be submitted" 1>&2
    echo "REM: /*.(bak|tmp|o|obj|log|rar|zip|7z|gz|tar|tgz)" 1>&2
    echo "REM: Thumbs.db|desktop.ini" 1>&2
    echo "REM: /(_notes|\.DS_Store|_runtime|cache|tmp|temp)/" 1>&2
    echo "REM: /.*" 1>&2
    exit 1
fi

if look log | grep '[SYS-IMG-ONLY]' > /dev/null ; then
    exit 0
fi  

disexts='\.(jpg|jpeg|gif|png)$'
diss="$disexts"

if look changed | grep '^A ' | sed -r 's#^A +##' | grep -iE $diss 1>&2 ; then
    echo "Pictures can not be submitted unless you specify: [SYS-IMG-ONLY]" 1>&2
    echo "REM: *.(jpg|jpeg|gif|png)" 1>&2
    exit 1
fi


# All checks passed, so allow the commit.
exit 0
