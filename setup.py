import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sflkit",
    version="0.0.1",
    author="cispa.de",
    author_email="marius.smytzek@cispa.de",
    description="Library for statistical fault localization and omniscient debugging.",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/uds-se/sflkit",
    install_requires=[
        'astor',
        'numpy'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Testing"
    ],
    python_requires='>=3.5.3',
    packages=setuptools.find_packages('.', exclude=('out', 'tests', 'resources', 'events'))
)
