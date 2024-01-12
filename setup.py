from setuptools import setup, find_packages

setup(
    name='USBtingoGUI',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        'PySide6',
        'python-can-usbtingo'
    ],
    entry_points={
        'console_scripts': [
            'usbtingogui = USBtingoGUI.__main__:main',
        ],
    },
    author="Thomas Fischl",
    author_email="tfischl@gmx.de",
    description='USBtingoGUI is a graphical tool for sending and receiving CAN(-FD) messages using USBtingo.',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/EmbedME/USBtingoGUI",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)
