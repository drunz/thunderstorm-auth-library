from setuptools import find_packages, setup

import thunderstorm_auth


def _read_requirements(requirements_filename):
    with open(requirements_filename) as reqs_file:
        return reqs_file.readlines()


REQUIREMENTS = _read_requirements('requirements.txt')
EXTRA_REQS = {
    'flask': [
        'flask>=0.12.3,<1'
    ],
    'falcon': [
        'falcon>=1.3,<1.4'
    ]
}


setup(
    name=thunderstorm_auth.__title__,
    version=thunderstorm_auth.__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=REQUIREMENTS,
    extras_require=EXTRA_REQS
)
