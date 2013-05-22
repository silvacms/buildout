"""Bootstrap a buildout-based project.
$Id$
"""

from optparse import OptionParser
import atexit
import os
import shutil
import subprocess
import sys
import tempfile
import urllib2

parser = OptionParser(usage="python bootstrap.py\n\n"
                      "Bootstrap the installation process.",
                      version="bootstrap.py $Revision$")
parser.add_option(
    "--buildout-config", dest="config", default="buildout.cfg",
    help="specify buildout configuration file to use, default to buildout.cfg")
parser.add_option(
    "--buildout-profile", dest="profile",
    help="specify a buildout profile to extends as configuration")
parser.add_option(
    "--buildout-version", dest="buildout_version", default="2.1.0-infrae1",
    help="specify version of zc.buildout to use, default to 2.1.0")
parser.add_option(
    "--install", dest="install", action="store_true", default=False,
    help="directly start the install process after bootstrap")
parser.add_option(
    "--virtualenv", dest="virtualenv", action="store_true", default=False,
    help="create a virtualenv to install the software. " \
        "This is recommended if you don't need to rely on globally installed " \
        "libraries")
parser.add_option(
    "--verbose", dest="verbose", action="store_true", default=False,
    help="Display more informations.")

options, args = parser.parse_args()

bin_dir = 'bin'
if sys.platform.startswith('win'):
    bin_dir = 'Scripts'

tmp_eggs = tempfile.mkdtemp()
atexit.register(shutil.rmtree, tmp_eggs)
to_reload = False
try:
    import pkg_resources
    # Verify it is distribute
    if not hasattr(pkg_resources, '_distribute'):
        to_reload = True
        raise ImportError
except ImportError:
    # Install setup tools or distribute
    setup_url = 'http://dist.infrae.com/thirdparty/distribute_setup.py'
    ez = {}
    ez_options = {'to_dir': tmp_eggs, 'download_delay': 0, 'no_fake': True}
    exec urllib2.urlopen(setup_url).read() in ez
    ez['use_setuptools'](**ez_options)

    if to_reload:
        reload(pkg_resources)
    import pkg_resources


if sys.platform == 'win32':
    quote = lambda arg: '"%s"' % arg
else:
    quote = str


def execute(cmd, env=None, stdout=None):
    if sys.platform == 'win32':
        # Subprocess doesn't work on windows with setuptools
        if env:
            return os.spawnle(*([os.P_WAIT, sys.executable] + cmd + [env]))
        return os.spawnl(*([os.P_WAIT, sys.executable] + cmd))
    if env:
        # Keep proxy settings during installation.
        for key, value in os.environ.items():
            if key.endswith('_proxy'):
                env[key] = value
    stdout = None
    if not options.verbose:
        stdout = subprocess.PIPE
    return subprocess.call(cmd, env=env, stdout=stdout)


def install(requirement):
    print "Installing %s ..." % requirement
    cmd = 'from setuptools.command.easy_install import main; main()'
    cmd_path = pkg_resources.working_set.find(
        pkg_resources.Requirement.parse('distribute')).location
    if execute(
        [sys.executable, '-c', quote(cmd), '-mqNxd', quote(tmp_eggs),
         '-f', quote('http://pypi.python.org/simple'), '-f', quote('http://dist.infrae.com/thirdparty/'), requirement],
        env={'PYTHONPATH': cmd_path}):
        sys.stderr.write(
            "\n\nFatal error while installing %s\n" % requirement)
        sys.exit(1)

    pkg_resources.working_set.add_entry(tmp_eggs)
    pkg_resources.working_set.require(requirement)


if options.virtualenv:
    python_path = os.path.join(bin_dir, os.path.basename(sys.executable))
    if not os.path.isfile(python_path):
        install('virtualenv>=1.5')
        import virtualenv
        print "Running virtualenv"
        args = sys.argv[:]
        sys.argv = ['bootstrap', os.getcwd(),
                    '--clear', '--no-site-package', '--distribute']
        virtualenv.main()
        execute([python_path] + args)
        sys.exit(0)


if options.profile:
    if not os.path.isfile(options.profile):
        sys.stderr.write('No such profile file: %s\n' % options.profile)
        sys.exit(1)

    print "Creating configuration '%s'" % os.path.abspath(options.config)
    config = open(options.config, 'w')
    config.write("""[buildout]
extends = %s
""" % options.profile)
    config.close()


install('zc.buildout==%s' % options.buildout_version)
import zc.buildout.buildout
zc.buildout.buildout.main(['-c', options.config, 'bootstrap'])


if options.install:
    print "Start installation ..."
    # Run install
    execute(
        [sys.executable, quote(os.path.join(bin_dir, 'buildout')),
         '-c', options.config, 'install'])

sys.exit(0)
