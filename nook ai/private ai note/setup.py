from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="nook-engine",
    version="1.0.0",
    author="Nook AI Team",
    author_email="contact@nook.ai",
    description="Local engine for high-quality speech transcription and diarization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nook-ai/nook-engine",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
    },
    entry_points={
        "console_scripts": [
            "nook-engine=nook_engine.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "nook_engine": ["*.md", "*.txt"],
    },
    keywords="speech recognition transcription diarization whisper local privacy",
    project_urls={
        "Bug Reports": "https://github.com/nook-ai/nook-engine/issues",
        "Source": "https://github.com/nook-ai/nook-engine",
        "Documentation": "https://github.com/nook-ai/nook-engine#readme",
    },
)
