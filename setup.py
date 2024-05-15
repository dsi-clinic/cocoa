from setuptools import find_packages, setup

setup(
    name="cocoa",
    version="0.4.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
