"""Bootstrap a buildout-based project, including downloading and
installing setuptools.
"""

from distutils import log
from optparse import OptionParser
import atexit
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib2

if sys.version_info[1] < 5:
    # No HTTPS for Python 2.4 this isn't supported.
    VIRTUALENV_REQ = "virtualenv<1.7"
    SETUPTOOLS_VERSION = "1.4.2"
    SETUPTOOLS_URL = "http://dist.infrae.com/thirdparty/"
else:
    VIRTUALENV_REQ= "virtualenv>=1.5"
    SETUPTOOLS_VERSION = "2.0.1"
    SETUPTOOLS_URL = "https://pypi.python.org/packages/source/s/setuptools/"

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
    "--buildout-version", dest="buildout_version", default="1.4.4",
    help="specify version of zc.buildout to use, default to 1.4.4")
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
quote = str
if sys.platform.startswith('win'):
    bin_dir = 'Scripts'
    quote = lambda arg: '"%s"' % arg
tmp_eggs = tempfile.mkdtemp()
atexit.register(shutil.rmtree, tmp_eggs)


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


def extract_tar(tar, path=".", members=None):
    """Extract all members from the archive to the current working
       directory and set owner, modification time and permissions on
       directories afterwards. `path' specifies a different directory
       to extract to. `members' is optional and must be a subset of the
       list returned by getmembers().
    """
    import copy
    import operator
    from tarfile import ExtractError
    directories = []

    if members is None:
        members = tar

    for tarinfo in members:
        if tarinfo.isdir():
            # Extract directories with a safe mode.
            directories.append(tarinfo)
            tarinfo = copy.copy(tarinfo)
            tarinfo.mode = 448  # decimal for oct 0700
        tar.extract(tarinfo, path)

    # Reverse sort directories.
    if sys.version_info < (2, 4):
        def sorter(dir1, dir2):
            return cmp(dir1.name, dir2.name)
        directories.sort(sorter)
        directories.reverse()
    else:
        directories.sort(key=operator.attrgetter('name'), reverse=True)

    # Set correct owner, mtime and filemode on directories.
    for tarinfo in directories:
        dirpath = os.path.join(path, tarinfo.name)
        try:
            tar.chown(tarinfo, dirpath)
            tar.utime(tarinfo, dirpath)
            tar.chmod(tarinfo, dirpath)
        except ExtractError:
            e = sys.exc_info()[1]
            if tar.errorlevel > 1:
                raise
            else:
                tar._dbg(1, "tarfile: %s" % e)


def build_egg(egg, tarball, to_dir):
    # extracting the tarball
    tmpdir = tempfile.mkdtemp()
    log.warn('Extracting ...')
    old_wd = os.getcwd()
    try:
        os.chdir(tmpdir)
        tar = tarfile.open(tarball)
        extract_tar(tar)
        tar.close()

        # going in the directory
        os.chdir(os.path.join(tmpdir, os.listdir(tmpdir)[0]))
        # building an egg
        log.warn('Installing setuptools ...')
        execute([sys.executable, 'setup.py', '-q', 'bdist_egg', '--dist-dir', to_dir])

    finally:
        os.chdir(old_wd)
        shutil.rmtree(tmpdir)
    if not os.path.exists(egg):
        raise IOError('Could not build the egg.')


def download_setuptools(version, download_base, to_dir):
    """Download setuptools from a specified location and return its filename

    `version` should be a valid setuptools version number that is available
    as an egg for download under the `download_base` URL (which should end
    with a '/'). `to_dir` is the directory where the egg will be downloaded.
    """
    # making sure we use the absolute path
    to_dir = os.path.abspath(to_dir)
    tgz_name = "setuptools-%s.tar.gz" % version
    url = download_base + tgz_name
    saveto = os.path.join(to_dir, tgz_name)
    src = dst = None
    if not os.path.exists(saveto):  # Avoid repeated downloads
        try:
            log.warn("Downloading %s", url)
            src = urllib2.urlopen(url)
            # Read/write all in one block, so we don't create a corrupt file
            # if the download is interrupted.
            data = src.read()
            dst = open(saveto, "wb")
            dst.write(data)
        finally:
            if src:
                src.close()
            if dst:
                dst.close()
    return os.path.realpath(saveto)


def _do_download(version, download_base, to_dir):
    egg = os.path.join(to_dir, 'setuptools-%s-py%d.%d.egg'
                       % (version, sys.version_info[0], sys.version_info[1]))
    if not os.path.exists(egg):
        tarball = download_setuptools(version, download_base, to_dir)
        build_egg(egg, tarball, to_dir)
    sys.path.insert(0, egg)
    import setuptools
    setuptools.bootstrap_install_from = egg


def install_setuptools(version=SETUPTOOLS_VERSION,
                       download_base=SETUPTOOLS_URL,
                       to_dir=tmp_eggs):
    # making sure we use the absolute path
    to_dir = os.path.abspath(to_dir)
    was_imported = 'pkg_resources' in sys.modules or \
        'setuptools' in sys.modules
    try:
        import pkg_resources
    except ImportError:
        return _do_download(version, download_base, to_dir)
    try:
        pkg_resources.require("setuptools>=" + version)
        return
    except pkg_resources.VersionConflict:
        e = sys.exc_info()[1]
        if was_imported:
            sys.stderr.write(
            "The required version of setuptools (>=%s) is not available,\n"
            "and can't be installed while this script is running. Please\n"
            "install a more recent version first, using\n"
            "'easy_install -U setuptools'."
            "\n\n(Currently using %r)\n" % (version, e.args[0]))
            sys.exit(2)
        else:
            del pkg_resources, sys.modules['pkg_resources']    # reload ok
            return _do_download(version, download_base, to_dir)
    except pkg_resources.DistributionNotFound:
        return _do_download(version, download_base, to_dir)


install_setuptools()
import pkg_resources


def install(requirement):
    print "Installing %s ..." % requirement
    cmd = 'from setuptools.command.easy_install import main; main()'
    cmd_path = pkg_resources.working_set.find(
        pkg_resources.Requirement.parse('setuptools')).location
    if execute(
        [sys.executable, '-c', quote(cmd), '-mqNxd', quote(tmp_eggs),
         '-f', quote('http://pypi.python.org/simple'),
         '-f', quote('http://dist.infrae.com/thirdparty/'), requirement],
        env={'PYTHONPATH': cmd_path}):
        sys.stderr.write(
            "\n\nFatal error while installing %s\n" % requirement)
        sys.exit(1)

    pkg_resources.working_set.add_entry(tmp_eggs)
    pkg_resources.working_set.require(requirement)


if options.virtualenv:
    python_path = os.path.join(bin_dir, os.path.basename(sys.executable))
    if not os.path.isfile(python_path):
        install(VIRTUALENV_REQ)
        import virtualenv
        print "Running virtualenv"
        args = sys.argv[:]
        sys.argv = ['bootstrap', os.getcwd(),
                    '--clear', '--no-site-package']
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
