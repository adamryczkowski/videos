import os
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))
PKG_NAME = 'videos'
VERPATH = os.path.join(HERE, PKG_NAME, '_version.py')
exec(open(VERPATH).read())

setup(name=PKG_NAME,
      version=__version__,
      author="Adam Ryczkowski",
      packages=find_packages(),
      include_package_data=True,
      install_requires=[
          'yt-dlp',
          'toml'
      ],
      entry_points={
          "console_scripts": [
              "download_all=videos.threads:main",
              "download_st=videos.main:download",
              "fetch_links=videos.functions:make_links"
          ]
      }
      )
