from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read()

setup(
    name="tfc",
    version="0.0.1",
    author="Mitch Anderson",
    author_email="mitch@chilledornaments.com",
    license="MIT",
    description="Manage TFC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="<github url where the tool code will remain>",
    py_modules=["tfc", "tfc_tool"],
    packages=find_packages(),
    install_requires=[requirements],
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
    ],
    entry_points="""
        [console_scripts]
        tfc=tfc:entrypoint
    """,
)
