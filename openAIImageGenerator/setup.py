from setuptools import setup, find_packages

setup(
    name="openai_image_generator",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "openai",
        "Pillow",
    ],
    entry_points={
        'console_scripts': [
            'openai-image-generator=src.main:main',
        ],
    }
) 
