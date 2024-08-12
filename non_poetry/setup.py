from setuptools import setup

setup(
    name='cmusic',
    version='1.2.0',
    description='the CLI music player',
    author='Kokonico',
    author_email='kokonico@duck.com',
    packages=['cmusic'],
    install_requires=['objlog', 'pygame', 'tinytag', 'mutagen', 'inquirer'],
    scripts=["cmusic/cmusic.py"]
)
