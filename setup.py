from setuptools import find_packages, setup

import thunderstorm_auth

requires = [
    open('requirements.txt').read()
]

setup(
    name=thunderstorm_auth.__title__,
    version=thunderstorm_auth.__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
)
