#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Licensed under the GNU General Public License, version 3.
# See the file http://www.gnu.org/licenses/gpl.txt

from pisi.actionsapi import get
from pisi.actionsapi import autotools
from pisi.actionsapi import pisitools
from pisi.actionsapi import shelltools

def extensions():
    configure_disabled = []

    configure_enabled = [
        'exif', 'ftp', 'soap', 'sockets', 'bcmath',
        'dom', 'wddx', 'tokenizer', 'simplexml', 'mbstring', 'calendar',
        'gd-native-ttf'
    ]
    configure_shared = [
        'dba', 'embedded-mysqli', 'zip'
    ]
    configure_with = [
        'bz2', 'curl', 'iconv', 'mysql', 'mysqli', 'kerberos', 'sqlite3',
        'xsl', 'gdbm', 'db', 'ldap', 'gd', 'gettext',
        'regex=php', 'pic', 'pcre-regex', 'pgsql', 'pdo-mysql', 'pdo-pgsql',
        'openssl'
    ]
    configure_without = []

    conf = []
    for i in configure_disabled:
        conf.append("--disable-%s" % i)
    for i in configure_enabled:
        conf.append("--enable-%s " % i)
    for i in configure_shared:
        conf.append("--enable-%s=shared" % i)
    for i in configure_with:
        conf.append("--with-%s" % i)
    for i in configure_without:
        conf.append("--without-%s" % i)

    return ' '.join(conf)

def setup():
    shelltools.unlinkDir("ext/openssl")

    # create directories for apache, fcgi and fpm's Makefiles
    shelltools.makedirs("fcgi")
    shelltools.makedirs("apache")
    shelltools.makedirs("fpm")
    shelltools.makedirs("common")

    # link configure script
    shelltools.sym("../configure", "fcgi/configure")
    shelltools.sym("../configure", "apache/configure")
    shelltools.sym("../configure", "fpm/configure")
    shelltools.sym("../configure", "common/configure")

    shelltools.export("LC_ALL", "C")
    shelltools.export("CFLAGS", "%s -fwrapv -lkrb5 -lgssapi_krb5 -lpam -DU_USING_ICU_NAMESPACE=1" % get.CFLAGS())
    shelltools.export("NO_INTERACTION", "1")
    shelltools.export("EXTENSION_DIR", "/usr/lib/php/modules")

    shelltools.system("sed -i '/APACHE_THREADED_MPM=/d' sapi/apache2handler/config.m4")
    pisitools.dosed("ext/pgsql/config.m4", "include/postgresql", " include/postgresql/pgsql")

    # Don't touch apache.conf
    for i in pisitools.ls("sapi/*/config.m4"):
        pisitools.dosed(i, "\\-i \\-a \\-n php7", "-i -n php7")
        pisitools.dosed(i, "\\-i \\-A \\-n php7", "-i -n php7")

    autotools.autoconf()

    # workaround for pkg-config 0.28
    pisitools.dosed("configure", " && test -n \"\$OPENSSL_INCS\"")

    common_options = "--sysconfdir=/etc \
                      --cache-file=./config.cache \
                      --with-zlib-dir=/usr/lib \
                      --with-libxml-dir=/usr/lib \
                      --with-jpeg-dir=/usr/lib/ \
                      --with-png-dir=/usr/lib/ \
                      --with-freetype-dir=/usr \
                      --with-zend-vm=GOTO \
                      --with-zend-vm=SWITCH \
                      --with-db4=/usr/lib \
                      --with-pic \
                      --with-libzip \
                      --with-gnu-ld \
                      --with-system-tzdata=/usr/share/zoneinfo \
                      --with-mcrypt=/usr/bin/mcrypt \
                      --with-imap=shared \
                      --with-openssl=shared \
                      --with-imap-ssl \
                      --with-mysql-sock=/run/mysqld/mysqld.sock \
                      --without-pear \
                      --disable-rpath \
                     "

    # Enable FastCGI and CGI
    shelltools.cd("fcgi")
    autotools.configure("--enable-cgi \
                         --disable-cli \
                         --with-config-file-path=/etc/php/cli \
                         --with-config-file-scan-dir=/etc/php/cli/ext \
                         %s \
                         %s" % (common_options, extensions()))

    # Enable Apache
    shelltools.cd("../apache")
    autotools.configure("--with-apxs2=/usr/bin/apxs \
                         --disable-cli \
                         --with-config-file-path=/etc/php/apache2 \
                         --with-config-file-scan-dir=/etc/php/apache2/ext \
                         %s \
                         %s" % (common_options, extensions()))
    # Enable FPM
    shelltools.cd("../fpm")
    autotools.configure("--enable-fpm \
                         --disable-cli \
                         --with-fpm-user=apache \
                         --with-fpm-group=apache \
                         --with-config-file-path=/etc/php/apache2 \
                         --with-config-file-scan-dir=/etc/php/apache2/ext \
                         %s \
                         %s" % (common_options, extensions()))
	
    # Enable common
    shelltools.cd("../common")
    autotools.configure("--enable-cli \
		                 --enable-phpdbg \
                         %s \
                         %s" % (common_options, extensions()))


def build():
    shelltools.cd("fcgi")
    shelltools.export("LC_ALL", "en_US.UTF-8")
    autotools.make()

    shelltools.cd("../apache")
    autotools.make()

    shelltools.cd("../fpm")
    autotools.make()
    
    shelltools.cd("../common")
    autotools.make()


def check():
    shelltools.cd("apache")
    autotools.make("test")

def install():
    shelltools.cd("fcgi")
    autotools.rawInstall("INSTALL_ROOT=\"%s\"" % get.installDIR(), "install-cgi")
    autotools.rawInstall("INSTALL_ROOT=\"%s\"" % get.installDIR(), "install-sapi")

    shelltools.cd("../apache")
    autotools.rawInstall("INSTALL_ROOT=\"%s\"" % get.installDIR(), "install")

    shelltools.cd("../fpm")
    autotools.rawInstall("INSTALL_ROOT=\"%s\"" % get.installDIR(), "install-fpm")
    
    shelltools.cd("../common")
    autotools.rawInstall("INSTALL_ROOT=\"%s\"" % get.installDIR(), "install")

    shelltools.cd("..")

    pisitools.insinto("/etc/php/apache2/", "php.ini-development", "php.ini")
    pisitools.insinto("/etc/php/cli/", "php.ini-development", "php.ini")

    pisitools.dosed("%s/etc/php/*/php.ini" % get.installDIR(), "(extension_dir = .*)", ";\\1")
    pisitools.dosed("%s/etc/php/*/php.ini" % get.installDIR(), r";include_path = \".:/php/includes\"",
                                                             "include_path = \".:/usr/share/php5/PEAR\"")

    pisitools.dodir("/etc/php/ext")
    pisitools.dodir("/etc/php/apache2/ext")
    pisitools.dodir("/etc/php/cli/ext")

    # Operations for php-zip package
    pisitools.dosym("/etc/php/ext/10-php-zip.ini", "/etc/php/cli/ext/10-php-zip.ini")

    # Operations for php-imap package
    pisitools.dosym("/etc/php/ext/11-php-imap.ini", "/etc/php/cli/ext/11-php-imap.ini")
    pisitools.dosym("/etc/php/ext/11-php-imap.ini", "/etc/php/apache2/ext/11-php-imap.ini")

    # Move /var/run to run
    pisitools.domove("/var/run", "/")

    pisitools.remove("/etc/php-fpm.conf.default")

    pisitools.dodir("/var/log/php-fpm/")
