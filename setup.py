from pathlib import Path

from setuptools import setup, find_packages

# Should be one of:
# 'Development Status :: 3 - Alpha'
# 'Development Status :: 4 - Beta'
# 'Development Status :: 5 - Production/Stable'
release_status = "Development Status :: 3 - Alpha"
version = '1.0.0-alpha'

with open("README.md", "r") as fh:
    long_description = fh.read()


def get_requirements():
    """Build the requirements list for this project"""
    requirements_list = []

    with Path("requirements.txt").open() as reqs:
        for install in reqs:
            if install.startswith("#"):
                continue
            requirements_list.append(install.strip())

    return requirements_list


setup(
    name='python-upbit-api',
    version=version,
    description='Python Upbit API Wrapper',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/designmeme/python-upbit-api',
    project_urls={
        'Source': 'https://github.com/designmeme/python-upbit-api',
        'Tracker': 'https://github.com/designmeme/python-upbit-api/issues',
    },
    author='이지혜 Lee Jihye',
    author_email='ghe.lee19@gmail.com',
    python_requires='>=3.8',
    packages=find_packages(),
    install_requires=get_requirements(),
    # 참고: https://pypi.org/classifiers/
    classifiers=[
        release_status,
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
