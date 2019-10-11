import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="py_starchat",
    version="0.0.1",
    author="Michele Boggia",
    author_email="michele.boggia@getjenny.com",
    description="A python client for StarChat",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GetJenny/python-starchat-client",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
