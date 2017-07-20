from setuptools import find_packages, setup

requires = [
    open('requirements.txt').read()
]

setup(
    name='thunderstorm-auth',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
)
