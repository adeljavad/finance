from setuptools import setup, find_packages

setup(
    name="django-financial-ai-core",
    version="0.1.0",
    description="A reusable Django app for AI-powered financial analysis",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Adel",
    author_email="your.email@example.com",
    url="https://github.com/adeljavad/finance",
    license="MIT",
    packages=find_packages(include=["financial_ai_core", "financial_ai_core.*"]),
    include_package_data=True,
    install_requires=[
        "Django>=4.0",
        "langchain>=0.1.0",
        "langchain-core>=0.1.0",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Framework :: Django",
        "Programming Language :: Python :: 3",
    ],
)
