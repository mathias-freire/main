#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Licensed under the GNU General Public License, version 2
# See the file http://www.gnu.org/copyleft/gpl.txt

from pisi.actionsapi import get
from pisi.actionsapi import autotools
from pisi.actionsapi import pisitools
from pisi.actionsapi import shelltools

def setup():
    autotools.autoreconf("-fiv")
    options = "\
                --disable-static \
                --enable-custom-modes \
                --enable-float-approx \
              "

    if get.buildTYPE() == "_emul32":
        options += "  --libdir=/usr/lib32 \
                  "
    shelltools.export("PKG_CONFIG_PATH", "/usr/lib32/pkgconfig")

    autotools.configure(options)

    pisitools.dosed("libtool", " -shared ", " -Wl,-O1,--as-needed -shared ")

def build():
    autotools.make()

def install():
    autotools.rawInstall("DESTDIR=%s" % get.installDIR())


    if get.buildTYPE() == "_emul32":
        pisitools.dodoc("README", "NEWS", "AUTHORS")
