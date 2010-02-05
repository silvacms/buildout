==============
Silva Buildout
==============

Abstract
========

The Silva Buildout allows you to conveniently set up Zope servers both
for development and production environments.

General documentation for Buildout can be found here:
http://pypi.python.org/pypi/zc.buildout

Use
===

Check out the buildout of the Silva trunk
-----------------------------------------

    svn co https://svn.infrae.com/buildout/silva/trunk/ Silva-buildout-trunk

Go into your "checkout"
-----------------------

    cd Silva-buildout-trunk

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
the ``buildout.cfg`` file to use the ``development.cfg``
configuration::

  [buildout]
  extends = profiles/development.cfg

The ``development.cfg`` configuration that we use in this example is
intended for local development.  Most of the configuration is shared
through ``base.cfg`` and only overridden where necessary.

Create a buildout configuration file or use the initial one as a base
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    cp buildout.cfg.in buildout.cfg

Then optionally edit buildout.cfg to suit your needs.

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

Assuming that your Python is in ``/usr/bin/python2.6``, you would run
this command to bootstrap your Buildout.  Remember that you only have
to run this the first time that you're doing the build::

  /usr/bin/python2.6 bootstrap.py

We use python2.6 here as we are using zope 2.12.x which requires
Python 2.6.

Run the buildout script
-----------------------

This bootstrapping will create a ``bin/buildout`` script which you now
use to start the actual build.  This can take a while::

from your Silva-buildout-trunk directory, run:

  bin/buildout

Whenever you update your configuration, you must rerun
``bin/buildout``, which will update all components and underlying
configuration files for you.

Run your zope
-------------

from your Silva-buildout-trunk directory, run:

    bin/zopeinstance

you can log in to your zope with the default Zope user
'admin'/'admin'. It's probably a good idea to change the password
earlier, rather than later, and definitely before you allow access to
your site from anywhere but your own machine.


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
ZODB file(s).  ``var/log`` contains the Zope logfiles.


Developing with this buildout
=============================

This buildout is aimed at both deploying Silva and developing with
Silva.  You'll find checkouts of the individual Silva components in
the ``parts`` subdirectory in the buildout.  This directory will be
preserved in case you accidentally leave changes in there and run the
buildout again, thanks to the ``infrae.subversion`` buildout recipe.

If you're developing your own Products, place your Products into the
``products-overrides`` directory.  This directory isn't ever touched
by the buildout.

