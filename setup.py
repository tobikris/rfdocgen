import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="rfdocgen",
    version="0.0.6",
    author="Tobias Krischer",
    author_email="tobias.krischer@elyxon.de",
    description="Generate and view Robot Framework Documentation live",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tobikris/rfdocgen",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'Click==7.0',
        'Flask==1.1.1',
        'itsdangerous==1.1.0',
        'Jinja2==2.10.1',
        'livereload==2.6.1',
        'MarkupSafe==1.1.1',
        'six==1.12.0',
        'tornado==6.0.3',
        'Werkzeug==0.15.4',
    ],
)
