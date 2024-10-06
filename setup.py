from setuptools import setup

setup(
    name="co",
    version="0.0.1",
    py_modules=["co"],
    entry_points={
        "console_scripts": [
            "co=co:main",
        ]
    },
)
