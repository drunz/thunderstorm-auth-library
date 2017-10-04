from setuptools import find_packages, setup

import thunderstorm_auth


EXTENSIONS = (
    'flask',
    'falcon'
)


def _install_requirements():
    return _read_requirements('requirements.txt')


def _extras_requirements():
    return {
        extension: _read_requirements('requirements-{}.txt'.format(extension))
        for extension in EXTENSIONS
    }


def _read_requirements(requirements_filename):
    with open(requirements_filename) as reqs_file:
        return reqs_file.readlines()


setup(
    name=thunderstorm_auth.__title__,
    version=thunderstorm_auth.__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=_install_requirements(),
    extras_require=_extras_requirements()
)
