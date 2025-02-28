from setuptools import setup, find_packages

setup(
    name="openai_image_generator",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "Pillow>=10.0.0",
        "python-dotenv>=1.0.0",
        "requests>=2.27.0",
        "python-dateutil>=2.8.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-mock>=3.10.0",
            "pytest-cov>=4.1.0",
        ],
        "ui": [
            "ttkthemes>=3.2.0",
            "pyperclip>=1.8.2",
        ],
        "image": [
            "opencv-python>=4.5.0",
            "numpy>=1.20.0",
        ],
        "export": [
            "matplotlib>=3.5.0",
            "pdfkit>=1.0.0",
        ],
        "voice": [
            "SpeechRecognition>=3.8.0",
        ],
    },
    entry_points={
        'console_scripts': [
            'openai-image-generator=src.main:main',
        ],
    },
    python_requires='>=3.7',
    description="A GUI application for generating images using OpenAI's DALL-E models",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/openai-image-generator",
) 
