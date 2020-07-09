from setuptools import setup, find_packages


setup(
    name                = 'coman',
    version             = '1.0.2',
    description         = 'A simple coroutine manager',
    author              = 'Alexander Korzun',
    author_email        = 'sahhash33@gmail.com',
    license             = 'GPL',
    packages            = find_packages(),
    package_data        = {'coman': ['py.typed']},
)
