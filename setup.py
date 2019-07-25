import setuptools


with open('README.md', "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="panoply",
    version="0.0.1",
    author="SP Solutions @ Paloaltonetworks",
    author_email="sp-solutions@paloaltonetworks.com",
    description="A small library of tools for working with PAN-OS devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nembery/SkilletLoader",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache License",
        "Operating System :: OS Independent",
    ],
)
