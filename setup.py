from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='search-fs',
      version='0.0.1',
      description='Scripts for managing media',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/raydouglass/search-fs',
      author='Ray Douglass',
      author_email='ray@raydouglass.com',
      license='Apache',
      packages=find_packages(),
      zip_safe=True,
      entry_points={
          'console_scripts': [
              'search-fs=search_fs.search:main',
              'create-search-fs=search_fs.create_db:main'
          ],
      },
      install_requires=[],
      python_requires='>=3.6',
      classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: Apache Software License",
          "Operating System :: OS Independent",
      ]
      )
