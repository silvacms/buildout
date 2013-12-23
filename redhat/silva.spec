Summary: Silva CMS
Name: silva
License: BSD
Group: Application/Internet
Version: 3.0.4
Release: 1
Vendor: SilvaCMS Community
Source0: https://github.com/silvacms/buildout
BuildRequires: git
BuildRequires: libxml2-devel
BuildRequires: libxslt-devel
BuildRequires: libjpeg-devel
BuildRequires: python27-devel
Requires: python27
Requires: libjpeg
Requires: libxml2
Requires: libxslt
Packager: Sylvain Viollon <sylvain@infrae.com>

%description
Install Silva CMS.

%prep
test -d silva || git clone https://github.com/silvacms/buildout silva

%build
umask 022
cd silva
cat >buildout.cfg <<EOF
[buildout]
extends = profiles/silva-development.cfg
parts += uwsgi
[deploy.ini]
error-log = /var/log/silva/error.log
[uwsgi]
daemonize = /var/log/silva/access.log
pidfile = /var/run/silva/wsgi.pid
max-requests = 100000
uwsgi-socket = 0.0.0.0:8081
EOF
/opt/local/bin/python27 bootstrap.py
./bin/buildout -v

%install
test -n "$RPM_BUILD_ROOT" -a "$RPM_BUILD_ROOT" != / && rm -rf $RPM_BUILD_ROOT
umask 022
cd silva
/opt/local/bin/python27 debian/unbuildout.py . --staging "$RPM_BUILD_ROOT" --etc-prefix /opt/local/etc/silva --package-prefix /opt/local/lib/silva --var-prefix /var --prefix /opt/local --python /opt/local/bin/python27

chmod -R a+rX $RPM_BUILD_ROOT/opt/local/lib/silva

mkdir -p $RPM_BUILD_ROOT/etc/rc.d/init.d
cat >$RPM_BUILD_ROOT/etc/rc.d/init.d/silva <<EOF
#!/bin/bash
#
# silva     Startup script for Silva CMS.
#
# chkconfig: - 95 05
# description: Silva CMS.
# pidfile: /var/run/silva/uwsgi.pid
### BEGIN INIT INFO
# Provides: silva
# Required-Start:
# Required-Stop:
### END INIT INFO

NAME=silva
USER=silva
PID_DIRECTORY=/var/run/silva
CONFIG=/opt/local/etc/silva/uwsgi.xml
SERVER=/opt/local/bin/silva-uwsgi
SERVER_PID=\$PID_DIRECTORY/wsgi.pid

# Create directory to store PID file if it doesn't exists.
if ! test -d \$PID_DIRECTORY; then
    mkdir \$PID_DIRECTORY
    chown \$USER: \$PID_DIRECTORY
fi

start() {
    # Investigate status of the server and start it.
    if test ! -f \$SERVER_PID ; then
        echo "Starting \$NAME ..."
        sudo -u \$USER \$SERVER \$CONFIG
    else
        PID=\`cat \$SERVER_PID\`
        if [ -z "\`ps axf | grep \${PID} | grep -v grep\`" ]; then
            echo "Delete PID file and start \$NAME ..."
            rm -f \$SERVER_PID
            sudo -u \$USER \$SERVER \$CONFIG
        fi
    fi
    return 0
}

stop() {
    if test -f \$SERVER_PID ; then
        echo -n "Stopping \$NAME"
        sudo -u \$USER \$SERVER --stop \$SERVER_PID  2>&1 >/dev/null
        echo "."
        rm -f \$SERVER_PID
    fi
    return 0
}

status() {
    if test -f \$SERVER_PID ; then
        PID=\`cat \$SERVER_PID\`
        if [ -z "\`ps axf | grep \${PID} | grep -v grep\`" ]; then
            echo "Server process dead but PID file exists."
        else
            echo "Server running."
        fi
    else
        echo "No PID file found for the server, not running."
    fi
}

restart() {
    stop
    echo "Cooldown ..."
    sleep 5
    start
}

case "\$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status
        ;;
    restart)
        restart
        ;;
    reload)
        restart
        ;;
    force-reload)
        restart
        ;;
    *)
        echo \$"Usage: \$0 {start|stop|restart|reload|force-reload}"
        exit 1
esac

exit \$?
EOF
chmod +x $RPM_BUILD_ROOT/etc/rc.d/init.d/silva

mkdir -p $RPM_BUILD_ROOT/var/lib/silva
echo "admin:admin" > $RPM_BUILD_ROOT/var/lib/silva/inituser
mkdir $RPM_BUILD_ROOT/var/lib/silva/filestorage
ln -s /opt/local/etc/silva $RPM_BUILD_ROOT/var/lib/silva/etc

%clean
test -n "$RPM_BUILD_ROOT" -a "$RPM_BUILD_ROOT" != / && rm -rf $RPM_BUILD_ROOT
test -d silva && rm -rf silva

%files
%defattr(-, root, root)
/etc/rc.d/init.d/silva
/opt/local/etc/silva
/opt/local/lib/silva
/opt/local/bin

%defattr(-,silva,silva)
%dir /var/log/silva
/var/lib/silva

%pre
getent group silva >/dev/null || groupadd -r silva
getent passwd silva >/dev/null || useradd -r -g silva -s /bin/bash -d /var/lib/silva silva

%post
/sbin/chkconfig --add silva
if test $1 -ne 1 ; then
  /sbin/service silva restart
fi

%preun
if test $1 -eq 0 ; then
  /sbin/service silva stop
  /sbin/chkconfig --del silva
fi
