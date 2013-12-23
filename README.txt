==============
Silva Buildout
==============

Abstract
========

The Silva buildout allows you to conveniently set up Silva both for
development and production environments. More information about the
usage of this buildout can be found in the developer documentation:

http://docs.silvacms.org/latest

General documentation for Buildout can be found here:

http://www.buildout.org

Use
===

Check out the buildout of Silva CMS
-----------------------------------

You need to have git installed in order to get the buildout. After you
can just clone it:

  $ git clone https://github.com/silvacms/buildout Silva

Go into your "checkout"
-----------------------

  $ cd Silva

Make a buildout profile
-----------------------

This Buildout supports a number of different configurations.  The
configuration files are in the ``profiles/`` subdirectory.  Every
configuration therein derives from the ``base.cfg`` configuration
file.  ``base.cfg`` is not intended to be used as a configuration
itself.

To use one of the configurations, you must create a new file called
``buildout.cfg`` in the root directory of the buildout (i.e. in the
directory this ``README.txt`` file is in).  Put these contents into
the ``buildout.cfg`` file to use the ``simple-instance.cfg``
configuration::

  [buildout]
  extends = profiles/simple-instance.cfg

The ``simple-instance.cfg`` configuration that we use in this example is
intended for a simple Silva instance.  Most of the configuration is shared
through ``base.cfg`` and only overridden where necessary.

Create a buildout configuration file or use the initial one as a base
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  $ cp buildout.cfg.in buildout.cfg

Then optionally edit ``buildout.cfg`` to suit your needs.

De initial buildout configuration extends the development profile
called development.cfg which you can find in the profiles folder. In
most cases this is the profile you want to use while developing. But
you can also use another profile located in the profiles folder if you
want.

Bootstrap everything
--------------------

When you run the Buildout for the first time, you must run the
``bootstrap.py`` script.  Important: This script must be run with the
Python interpreter that you intend to use for your Zope.

Assuming that your Python is in ``/usr/bin/python2.7``, you would run
this command to bootstrap your Buildout.  Remember that you only have
to run this the first time that you're doing the build::

  $ python2.7 bootstrap.py

We use python2.7 here as we are using Zope 2.13.x which requires
Python 2.7. Other requirements are needed: libxml2, libxslt, libjpeg,
and zlib.

A detailed list of those requirements can be found in the Silva
technical documentation:

http://docs.silvacms.org/latest/buildout/requirements.html

Run the buildout script
-----------------------

This bootstrapping will create a ``bin/buildout`` script which you now
use to start the actual build.  This can take a while::

From your ``Silva`` directory, run:

  $ bin/buildout

Whenever you update your configuration, you must rerun
``bin/buildout``, which will update all components and underlying
configuration files for you.

Run your zope
-------------

From your ``Silva`` directory, run:

  $ bin/paster serve deploy.ini

Or to run in debug mode, run:

  $ bin/paster serve debug.ini

You can log in to your zope with the default Zope user
'admin'/'admin'. It's probably a good idea to change the password
earlier, rather than later, and definitely before you allow access to
your site from anywhere but your own machine.

Upgrading a previous installation
=================================

In order to upgrade an existing installation, you can consult the
guidelines online in the Silva technical documentation:

http://docs.silvacms.org/latest/buildout.html#upgrading-your-installation

Directory structure
===================

This script will download amongst other things download and compile
Zope, Silva, and the Python Imaging Library (PIL).  After it's
finished, you'll find a couple of more scripts in the ``bin/``
subdirectory.  There you'll find scripts to start the Zope instance(s)
and servers, if you have any configured, Depending of the
configuration you used, you might also find the associated
``bin/zeopack`` and ``bin/repozo`` scripts that are used for packing
and backing up the ZODB respectively.

Another directory of interest is ``var/filestorage``, which holds the
ZODB file(s).  ``var/log`` contains the Zope log files.

Creating a debian package
=========================

You can create a Debian/Ubuntu package out of this buildout in order
to make the deployement in production of your site more easy and
reliable.

In order to do this, just run this command in the buildout directory::

  $ debuild -uc -us

It will create a package that will install Silva in /opt/local. Data
will be stored in /var/lib/silva.

For more information about how to create a package, please refer to
the corresponding documentation for Debian or Ubuntu.

Original Code
=============

This buildout was originally obtained from Git:
https://github.com/silvacms/buildout




