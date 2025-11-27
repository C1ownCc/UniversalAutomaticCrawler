from setuptools import setup, find_packages

setup(
    name='universal-automatic-crawler',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        # Add your package dependencies here
    ],
    entry_points={
        'console_scripts': [
            # Define console scripts here if any
        ],
    },
    author='C1ownCc',
    author_email='your_email@example.com',
    description='A universal automatic web crawler.',
    url='https://github.com/C1ownCc/UniversalAutomaticCrawler',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)