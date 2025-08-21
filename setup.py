"""Setup script for the noise cancellation application."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="noise-cancellation-app",
    version="1.0.0",
    description="Professional desktop application for removing background noise from audio and video files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Noise Cancellation Team",
    author_email="support@example.com",
    url="https://github.com/your-username/noise-cancellation",
    license="MIT",
    
    # Package configuration
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'ui': ['*.ui', 'resources/*'],
        'models': ['*.rnnn'],
        'docs': ['*.md', '*.png'],
    },
    
    # Dependencies
    python_requires=">=3.10",
    install_requires=requirements,
    
    # Optional dependencies
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-qt>=4.2.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.5.0',
        ],
        'demucs': ['demucs>=4.0.0'],
    },
    
    # Entry points
    entry_points={
        'console_scripts': [
            'noise-cancellation=app:main',
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Video",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    
    # Keywords
    keywords="audio video noise reduction rnnoise spectral gating demucs gui desktop",
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/your-username/noise-cancellation/issues",
        "Source": "https://github.com/your-username/noise-cancellation",
        "Documentation": "https://github.com/your-username/noise-cancellation#readme",
    },
)