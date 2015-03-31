from setuptools import setup


setup(
    name='interface_monitor',
    description='Monitors interface I/O by sending commands in loop via SSH',
    url='https://github.com/coxley/interface_monitor',
    version=1.0,
    author='Codey Oxley',
    packages=['interface_monitor'],
    py_modules=['interface_monitor'],
    entry_points='''
    [console_scripts]
    interface_monitor=interface_monitor.interface_monitor:main
    '''
)
