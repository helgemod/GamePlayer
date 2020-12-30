from setuptools import setup

setup(name='GamePlayer',
      version='1.0.1',
      description='Python module that plays games like Tic Tac Toe and Five In A Row.',
      url='http://www.github.com/helgemod',
      author='Helge Modén',
      author_email='helgemod@gmail.com',
      license='MIT',
      packages=['GamePlayer'],
      dependency_links=['https://github.com/helgemod/StrideDimensions/archive/1.0.1.tar.gz',
                        'https://github.com/helgemod/MinMaxAlgorithm/archive/1.0.1.tar.gz'],
      zip_safe=False)