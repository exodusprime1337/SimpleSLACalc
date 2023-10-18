import pathlib

import setuptools

setuptools.setup(
    name="SimpleSLACalc",
    version="0.0.1",
    description="Simple SLA Calculator",
    long_description=pathlib.Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    url="https://github.com/exodusprime1337/SimpleSLACalc",
    author="Kenny Sambrook",
    author_email="kenny@krstek.com",
    license="The Unlicense",
    # packages=["SimpleSLACalc"],
    zip_safe=False,
    urls={"Source": "https://github.com/exodusprime1337/SimpleSLACalc"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: Freely Distributable",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development",
        "Topic :: Utilities",
    ],
    python_requires=">=3.10,<3.12",
    install_requires=[
        "holidays==0.35",
        "pendulum==3.0.0b1",
    ],
    packages=setuptools.find_packages(),
    include_package_data=True,
)
