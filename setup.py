import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pytion",
    version="1.2.2",
    author="Yegor Gomzin",
    author_email="slezycmex@mail.ru",
    description="Unofficial Python client for official Notion API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lastorel/pytion",
    project_urls={
        "Bug Tracker": "https://github.com/lastorel/pytion/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.26.0"
    ]
)
