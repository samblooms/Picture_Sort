from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name='picture_sort', 
    version='0.1.0',
    description='Recursively sort a directory of photos by date',
    author='Sam Bloomingdale',
    packages=find_packages(),
    install_requires=['wheel', 'bar', 'greek'],
)
