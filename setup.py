from setuptools import setup

setup(
    name="co",
    version="0.1.0",
    py_modules=["co"],
    entry_points={
        "console_scripts": [
            "co=co:main",
        ]
    },
)
