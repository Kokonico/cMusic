from setuptools import setup

setup(
    name='cmusic',
    version='1.1.0',
    description='the CLI music player',
    author='Kokonico',
    author_email='kokonico@duck.com',
    packages=['cmusic'],  #same as name
    install_requires=['objlog', 'pygame', 'tinytag', 'mutagen', 'inquirer'],
    scripts=["cmusic/__main__.py"]
)
