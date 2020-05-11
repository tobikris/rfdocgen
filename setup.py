import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="rfdocgen",
    version="0.0.1",
    author="Tobias Krischer",
    author_email="tobias.krischer@elyxon.de",
    description="Generate and view Robot Framework Documentation live",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tobikris/rfdocgen",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
