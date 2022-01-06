import setuptools
import re

def load_requirements_from_file(file_name):
    # get the dependencies and installs
    requires = []
    with open(file_name, "r", encoding="utf-8") as f:
        # Make sure we strip all comments and options (e.g "--extra-index-url")
        for line in f:
            req = line.split("#", 1)[0].strip()
            if req and not req.startswith("--"):
                requires.append(req)
    return requires

long_description = ""
# with open("README.md", "r") as fh:
#     long_description = fh.read()

version = re.search(
    r"^__version__\s*?=\s*?'(.*)'",
    open('safe_env/version.py').read(),
    re.M
    ).group(1)

requires_base = load_requirements_from_file("requirements-base.txt")
requires_local = load_requirements_from_file("requirements-local.txt")
requires_build = load_requirements_from_file("requirements-build.txt")

setuptools.setup(
    name="safe-env",
    version=version,
    author="Antons Mislevics",
    author_email="antonsm@outlook.com",
    description="Safe Environment Manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/antonsmislevics/safe-env",
    packages=setuptools.find_packages(),
    entry_points = {
        'console_scripts': [
            'se=safe_env.cli:app'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires = requires_base,
    extras_require={
        'all': requires_local + requires_build,
        'local': requires_local
    }
)