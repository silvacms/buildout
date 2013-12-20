#!/usr/bin/env python2.7

import ConfigParser
import argparse
import os
import shutil
import stat
import re
import sys
import subprocess
import tempfile

EXECUTABLE = (stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP |
              stat.S_IROTH | stat.S_IXOTH)
OPTIONS_RE = re.compile(r'([a-zA-Z0-9-]+)=(.*)')


class Installable(object):

    def __init__(self, origin, target, options):
        self._origin = origin
        self._target = target
        self._options = options

    def get_origin_path(self):
        """Return the original path to install.
        """
        return self._origin

    def get_staging_path(self):
        """Return the path where the file/files must be created, in the
        staging tree if there is one.
        """
        target_name = self.get_target_path()
        if not self._options['staging']:
            return target_name
        return os.path.join(
            self._options['staging'],
            target_name.lstrip(os.path.sep))

    def get_target_path(self):
        """Return the path where the file/files will be installed when
        the staging tree will be installed in place.
        """
        return self._target

    def install(self, filters=[]):
        """Install the file/files.
        """
        raise NotImplementedError


class Replacement(Installable):

    def install(self, filters=[]):
        pass


class File(Installable):
    permissions = stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IROTH

    def install(self, filters=[]):
        target_path = self.get_staging_path()
        target_directory = os.path.dirname(target_path)
        if not os.path.isdir(target_directory):
            os.makedirs(target_directory)
        lines = []
        with open(self.get_origin_path(), 'r') as stream:
            for line in stream.readlines():
                for method in filters:
                    line = method(line)
                    if line is None:
                        break
                else:
                    lines.append(line)
        with open(target_path, 'w') as stream:
            stream.writelines(lines)
        os.chmod(target_path, self.permissions)


class OneLineReplaceFile(File):
    pass


class PythonScriptFile(OneLineReplaceFile):
    permissions = EXECUTABLE


class ConfigurationFile(OneLineReplaceFile):
    pass


class ShellScriptFile(File):
    permissions = EXECUTABLE


class Others(Installable):

    def __init__(self, origin, target, options, keeppyc=False, onlysub=None):
        super(Others, self).__init__(origin, target, options)
        self.keeppyc = keeppyc
        self.onlysub = onlysub

    def get_path_to_install(self):
        return self.get_origin_path()

    def install(self, filters=[]):
        origin_path = self.get_path_to_install()
        target_path = self.get_staging_path()
        if self.onlysub:
            origin_path = os.path.join(origin_path, self.onlysub)
            target_path = os.path.join(target_path, self.onlysub)
        target_directory = os.path.dirname(target_path)
        if not os.path.isdir(target_directory):
            os.makedirs(target_directory)
        if os.path.isdir(origin_path):
            ignore = None
            if not self.keeppyc:
                ignore = shutil.ignore_patterns('*.pyc', '*pyo')
            shutil.copytree(
                origin_path,
                target_path,
                ignore=ignore)
        elif os.path.isfile(origin_path):
            shutil.copy2(
                origin_path,
                target_path)


class PythonPackage(Others):

    def __init__(self, origin, options, keeppyc=False):
        target = os.path.join(options['lib_prefix'], os.path.basename(origin))
        super(PythonPackage, self).__init__(origin, target, options, keeppyc)


class SourcePackage(PythonPackage):
    unsourcify = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'unsourcify.py')

    def __init__(self, origin, options, keeppyc=False):
        target = None
        self._path_to_install = tempfile.mkdtemp('unbuildout')
        subprocess.call(
            (options['python'], self.unsourcify,
             '--source', origin,
             '--destination', self._path_to_install),
            cwd=tempfile.gettempdir())
        base_name = os.path.basename(origin) + '-'
        for candidate_name in os.listdir(self._path_to_install):
            if candidate_name.startswith(base_name):
                self._path_to_install = os.path.join(
                    self._path_to_install, candidate_name)
                target = os.path.join(options['lib_prefix'], candidate_name)
                break
        else:
            raise ValueError('Cannot find built package.')
        super(PythonPackage, self).__init__(origin, target, options, keeppyc)

    def get_path_to_install(self):
        return self._path_to_install


class Status(object):

    def __init__(self, options):

        def create(names, factory):
            if not names:
                return dict()
            files = map(lambda (o, t): factory(o, *t[0], **t[1]), names.iteritems())
            return dict(zip(map(lambda f: f.get_origin_path(), files), files))

        self._options = options
        self._py_scripts = create(options['python scripts'], PythonScriptFile)
        self._shell_scripts = create(options['shell scripts'], ShellScriptFile)
        self._configs = create(options['configurations'], ConfigurationFile)
        self._others = create(options['others'], Others)
        self._replacements = create(options['replacements'], Replacement)
        self._packages = dict()

    def get_ignores(self):
        return self._options['ignores'].keys()

    def get_python_packages_origin(self):
        return (map(lambda path: (path, False),
                    self._options['eggs'].keys()) +
                map(lambda path: (path, True),
                    self._options['source-eggs'].keys()))

    def get_renames(self):
        """Get paths to installables that should renamed (and that
        aren't packages).
        """
        renames = []

        def add(installables, strip=False):
            new = []
            for path, installable in installables.items():
                key = path.lower()
                if strip:
                    key = key.rstrip(os.path.sep)
                new.append((key, installable))
            renames.extend(new)

        add(self._configs)
        add(self._py_scripts)
        add(self._shell_scripts)
        add(self._replacements, strip=True)
        add(self._others, strip=True)

        return sorted(renames, key=lambda (key, installable): -len(key))

    def add_python_package(self, name, is_source=False):
        """Add a python package if it doesn't exists and return it.
        """
        factory = PythonPackage
        if is_source:
            factory = SourcePackage
        package = factory(name, self._options)
        self._packages[package.get_origin_path()] = package
        return package

    def get_python_packages(self):
        """Return a directory original names -> python packages.
        """
        return self._packages.copy()

    def iter_installables(self):
        """Iter over all the installables.
        """
        for script in self._py_scripts.values():
            yield script
        for script in self._shell_scripts.values():
            yield script
        for config in self._configs.values():
            yield config
        for other in self._others.values():
            yield other
        for package in self._packages.values():
            yield package


class PathFilter(object):
    """Replace paths inside a package. It can only replace one path on
    a given line.
    """

    def __init__(self, status):
        self._renames = status.get_renames()

    def available(self, installable):
        return isinstance(installable, OneLineReplaceFile)

    def __call__(self, line):
        for path, installable in self._renames:
            try:
                replace = line.lower().index(path)
            except ValueError:
                continue
            return ''.join((line[:replace],
                            installable.get_target_path(),
                            line[replace+len(path):]))
        return line


class IgnoreFilter(object):

    def __init__(self, status):
        self._ignores = status.get_ignores()

    def available(self, installable):
        return isinstance(installable, OneLineReplaceFile)

    def __call__(self, line):
        for ignore in self._ignores:
            if ignore in line:
                return None
        return line


class PackageFilter(object):

    def __init__(self, status):
        self._origins = status.get_python_packages_origin()
        self._packages = dict()
        self._add = status.add_python_package

    def available(self, installable):
        return isinstance(installable, PythonScriptFile)

    def __call__(self, line):
        for path, package in self._packages.items():
            if path in line:
                line = line.replace(path, package.get_target_path())
                break
        else:
            for (origin, is_source) in self._origins:
                if origin in line:
                    match = re.search(
                        r"^([^'\n\"]+)",
                        line[line.index(origin):])
                    if match is not None:
                        path = match.groups()[0]
                        package = self._add(path, is_source)
                        self._packages[path] = package
                        line = line.replace(path, package.get_target_path())
        return line


class VariableDeclarationFilter(object):
    variable = re.compile('^([A-Z_]+)="([^"]*)"$')

    def __init__(self, status):
        self._status = status
        self._renames = status.get_renames()

    def available(self, installable):
        return isinstance(installable, ShellScriptFile)

    def python_path(self, name, value):
        python_path = value.split(':')
        for ignore in self._status.get_ignores():
            python_path = filter(
                lambda path: not path.startswith(ignore),
                python_path)
        for origin_path, package in self._status.get_python_packages().items():
            try:
                index = python_path.index(origin_path)
            except ValueError:
                continue
            python_path[index] = package.get_target_path()
        return name, ':'.join(python_path)

    def default_variable(self, name, value):
        for path, installable in self._renames:
            try:
                replace = value.lower().index(path)
            except ValueError:
                continue
            return name, ''.join((value[:replace],
                                  installable.get_target_path(),
                                  value[replace+len(path):]))
        return name, value

    HANDLERS = {'PYTHONPATH': python_path, None: default_variable}

    def __call__(self, line):
        match = self.variable.match(line)
        if match is None:
            return line
        variable = match.group(1)
        value = match.group(2)
        handler = self.HANDLERS.get(variable)
        if handler is None:
            handler = self.HANDLERS.get(None)
        new_variable, new_value = handler(self, variable, value)
        return '%s="%s"%s' % (new_variable, new_value, os.linesep)


def get_option_status():
    """Return a status out of the options passed to this script.
    """
    parser = argparse.ArgumentParser(description='Remove buildout.')
    parser.add_argument(
        '--staging', dest='staging',
        help='Staging directory to create the installation tree')
    parser.add_argument(
        '--prefix', dest='prefix', default='/opt/local',
        help='Installation prefix (target)')
    parser.add_argument(
        '--bin-prefix', dest='bin_prefix',
        help='Custom installation prefix for bin files')
    parser.add_argument(
        '--etc-prefix', dest='etc_prefix',
        help='Custom installation prefix for etc files')
    parser.add_argument(
        '--package-prefix', dest='package_prefix',
        help='Custom installation prefix for Python packages')
    parser.add_argument(
        '--var-prefix', dest='var_prefix',
        help='Custom installation prefix for var files')
    parser.add_argument(
        '--manifest', dest='manifest', default='debian/MANIFEST',
        help='Listing of files and directories to install')
    parser.add_argument(
        '--python', dest='python', default=sys.executable,
        help='Python executable to use in order to install source packages')
    parser.add_argument(
        'buildout', default=os.getcwd(),
        help='Directory containing the buildout installation tree')

    args = parser.parse_args()
    if not args.manifest or not os.path.isfile(args.manifest):
        raise ValueError('Manifest of files to install missing.')

    if not os.path.isdir(args.buildout):
        raise ValueError('Buildout directory is missing')

    if os.path.isdir(args.staging):
        shutil.rmtree(args.staging)

    config = ConfigParser.ConfigParser()
    config.optionxform = str
    config.read(args.manifest)

    def build_prefix(path, default=None):
        if not path or not os.path.isabs(path):
            return os.path.join(args.prefix, path or default)
        return path

    expand = {'buildout': os.path.abspath(args.buildout),
              'staging': args.staging and os.path.abspath(args.staging) or None,
              'prefix': args.prefix,
              'python': args.python,
              'bin_prefix': build_prefix(args.bin_prefix, 'bin'),
              'etc_prefix': build_prefix(args.etc_prefix, 'etc'),
              'lib_prefix': build_prefix(args.package_prefix, 'lib'),
              'var_prefix': build_prefix(args.var_prefix, 'var')}

    options = {}
    for section in config.sections():
        paths = {}
        for path in config.options(section):
            args = []
            kwargs = {}
            info = config.get(section, path).split()
            for bit in info:
                match = OPTIONS_RE.match(bit)
                if match:
                    kwargs[match.group(1)] = match.group(2)
                else:
                    args.append(bit)
            if not os.path.isabs(path):
                path = os.path.join(expand['buildout'], path)
            if os.path.isdir(path) and not path.endswith(os.path.sep):
                path += os.path.sep
            if len(args) < 1:
                paths[path] = True
            else:
                installed = args.pop()
                paths[path] = (installed.format(**expand), options) + tuple(args), kwargs
        options[section] = paths

    options.update(expand)

    return Status(options)


def unbuildout(status):
    """Unbuildout this installation.
    """
    filters = [
        IgnoreFilter(status),
        PathFilter(status),
        PackageFilter(status),
        VariableDeclarationFilter(status)]
    for installable in status.iter_installables():
        print 'Install %s to %s ...' % (
            installable.get_origin_path(),
            installable.get_staging_path())
        installable.install(filter(lambda f: f.available(installable), filters))

if __name__ == '__main__':
    unbuildout(get_option_status())
