from setuptools import setup

setup(
    name="csi_py",
    version="0.1",
    description="CSI Python Library",
    py_modules=["csi_py"],
    install_requires=[
        "comtypes",
        "pandas",
        "numpy",
    ]
        
)