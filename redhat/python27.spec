
# Configuration
%define name            python
%define version         2.7.6
%define libversion      2.7
%define pythonsuffix    27
%define release         1
%define _prefix         /opt/local
# End of configuration

Summary: An interpreted, interactive, object-oriented programming language.
Name: %{name}%{pythonsuffix}
Version: %{version}
Release: %{release}
License: Modified CNRI Open Source License
Group: Development/Languages
Source: Python-%{version}.tgz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
BuildRequires: expat-devel
BuildRequires: db4-devel
BuildRequires: sqlite-devel
BuildRequires: openssl-devel
BuildRequires: readline-devel
BuildRequires: zlib-devel
BuildRequires: gcc
BuildRequires: make
Requires: readline
Requires: zlib
Requires: openssl
Requires: sqlite
Requires: expat
Requires: db4
Prefix: %{_prefix}
Packager: Sylvain Viollon <sylvain@infrae.com>

%description
Python is an interpreted, interactive, object-oriented programming
language.  It incorporates modules, exceptions, dynamic typing, very high
level dynamic data types, and classes. Python combines remarkable power
with very clear syntax. It has interfaces to many system calls and
libraries, as well as to various window systems, and is extensible in C or
C++. It is also usable as an extension language for applications that need
a programmable interface.  Finally, Python is portable: it runs on many
brands of UNIX, on PCs under Windows, MS-DOS, and OS/2, and on the
Mac.

%package devel
Summary: The libraries and header files needed for Python extension development.
Requires: python%{pythonsuffix}
Group: Development/Libraries

%description devel
The Python programming language interpreter can be extended with
dynamically loaded extensions and can be embedded in other programs.
This package contains the header files and libraries needed to do
these types of tasks.

Install python-devel if you want to develop Python extensions.  The
python package will also need to be installed.

%changelog

#######
#  PREP
#######
%prep
%setup -n Python-%{version}

########
#  BUILD
########
%build
./configure --enable-unicode=ucs4 --disable-shared --disable-ipv6 --prefix=%{_prefix}
make

##########
#  INSTALL
##########
%install
[ -d "$RPM_BUILD_ROOT" -a "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT
make DESTDIR=$RPM_BUILD_ROOT install

# update binary name
(
    cd $RPM_BUILD_ROOT%{_prefix}/bin
    for file in * ; do if test "$file" != "python2.7" ; then rm -f "$file" ; fi; done
    mv python2.7 python%{pythonsuffix}
    chmod 755 python%{pythonsuffix}
    )
(
    cd $RPM_BUILD_ROOT%{_prefix}/share/man/man1; mv python.1 python%{pythonsuffix}.1
    )

# fix any hardcoded #!/usr/local line in installed files
find "$RPM_BUILD_ROOT" -type f -print0 |
      xargs -0 grep -l -e '#!.*/usr/local/bin/python' | while read file
do
   FIXFILE="$file"
   sed 's|^#!.*/usr/local/bin/python|#!/usr/bin/env python'"%{pythonsuffix}"'|' \
         "$FIXFILE" >/tmp/fix-python-path.$$
   cat /tmp/fix-python-path.$$ >"$FIXFILE"
   rm -f /tmp/fix-python-path.$$
done


# MAKE FILE LISTS
rm -f mainpkg.files develpkg.files
find "$RPM_BUILD_ROOT""%{_prefix}"/lib/python%{libversion}/ -type f |
	sed "s|^${RPM_BUILD_ROOT}|/|" |
	grep -v '/python%{libversion}/config/' >mainpkg.files
find "$RPM_BUILD_ROOT""%{_prefix}"/bin -type f -o -type l |
	sed "s|^${RPM_BUILD_ROOT}|/|" >>mainpkg.files
find "$RPM_BUILD_ROOT""%{_prefix}"/share -type f -o -type l |
	sed "s|^${RPM_BUILD_ROOT}|/|" >>mainpkg.files

find "$RPM_BUILD_ROOT""%{_prefix}"/lib/pkgconfig -type f -follow |
	sed "s|^${RPM_BUILD_ROOT}|/|" >develpkg.files
find "$RPM_BUILD_ROOT""%{_prefix}"/include/python%{libversion} -type f |
	sed "s|^${RPM_BUILD_ROOT}|/|" >>develpkg.files
find "$RPM_BUILD_ROOT""%{_prefix}"/lib/python%{libversion}/config -type f |
	sed "s|^${RPM_BUILD_ROOT}|/|"  >>develpkg.files
find "$RPM_BUILD_ROOT""%{_prefix}"/lib -maxdepth 1 -type f -name '*.a'  |
	sed "s|^${RPM_BUILD_ROOT}|/|"  >>develpkg.files


########
#  CLEAN
########
%clean
[ -n "$RPM_BUILD_ROOT" -a "$RPM_BUILD_ROOT" != / ] && rm -rf $RPM_BUILD_ROOT
rm -f mainpkg.files develpkg.files

########
#  FILES
########
%files -f mainpkg.files
%defattr(-,root,root)

%files devel -f develpkg.files
%defattr(-,root,root)

