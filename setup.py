from setuptools import find_packages, setup

setup(
    name='afml',
    packages=find_packages(include=['afml', 'afml.utils']),
    version='0.1.0.dev0',
    description='Automation Framework for Machine Learning',
    author='AlbertWDev',
    license='MIT',
    install_requires=[
        'pyyaml',
        'termcolor',
        'munch'
    ],
    entry_points={
        'console_scripts': [
            'afml=afml.afml:main'
        ]
    }
)
