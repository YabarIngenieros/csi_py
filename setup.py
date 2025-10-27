from setuptools import setup, find_packages
import os

# Leer el README para la descripción larga
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "CSI Python Library - Automatización de ETABS, SAP2000 y SAFE"

setup(
    name="csi_py",
    version="0.1.0",
    author="YabarIngenieros",
    author_email="",
    description="Biblioteca Python para automatizar software CSI (ETABS, SAP2000, SAFE)",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/YabarIngenieros/csi_py",
    
    # Paquetes a incluir
    packages=find_packages(),
    
    # Módulos Python principales
    py_modules=["handler", "constants", "extractor", "builder"],
    
    # Clasificadores
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
    ],
    
    # Palabras clave
    keywords="etabs sap2000 safe csi structural-analysis automation api",
    
    # Requisitos de Python
    python_requires=">=3.7",
    
    # Dependencias
    install_requires=[
        "comtypes>=1.1.0",
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "psutil>=5.8.0",
    ],
    
    # Dependencias opcionales
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=21.0',
            'flake8>=3.9',
        ],
        'docs': [
            'sphinx>=4.0',
            'sphinx-rtd-theme>=0.5',
        ],
    },
    
    # Scripts de entrada (opcional, para CLI en el futuro)
    # entry_points={
    #     'console_scripts': [
    #         'csi-py=csi_py.cli:main',
    #     ],
    # },
    
    # Incluir archivos adicionales
    include_package_data=True,
    
    # Archivos de datos
    package_data={
        'csi_py': ['*.md', 'examples/*.py'],
    },
    
    # Licencia
    license="MIT",
    
    # Plataformas
    platforms=['Windows'],
    
    # Información del proyecto
    project_urls={
        'Bug Reports': 'https://github.com/YabarIngenieros/csi_py/issues',
        'Source': 'https://github.com/YabarIngenieros/csi_py',
        'Documentation': 'https://github.com/YabarIngenieros/csi_py/blob/main/README.md',
    },
)