from setuptools import setup

setup(name='txsimpleroutes',
        version='0.0.1',
        author='Ben Congleton',
        author_email='ben@olark.com',
        url='http://github.com/jaminben/txsimpleroutes',
        description='Provides routes-like dispatching for twisted.web.server',
        long_description='''Frequently, it's much easier to describe your website layout using routes instead of Resource from twisted.web.resource. This small library lets you dispatch with routes in your twisted.web application.''',
        keywords='twisted, web, routes',
        classifiers=['Programming Language :: Python', 'License :: OSI Approved :: BSD License'],
        license='BSD',
        packages=['txsimpleroutes'],
        package_data={'txsimpleroutes': ['*']},
        install_requires=['routes', 'twisted'],
        )

