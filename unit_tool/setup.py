from setuptools import setup, find_packages

setup(
    name="unit_tools",
    version="0.1",
    description="Unit Tools",
    author="JNoha",
    py_modules=["unit_tools","config"],
    install_requires=[
        "comtypes",
        "pandas",
        "numpy",
    ]
        
)