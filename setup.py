from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
import os

NODEWOX_HOME = "/var/lib/nodewox"

class NXInstallCommand(install):

    def run(self):
        # make NODEWOX_HOME
        if not os.path.exists(NODEWOX_HOME):
            print("make dir %s" % NODEWOX_HOME)
            os.mkdir(NODEWOX_HOME, 0o755)

        for x in ("trust", "profiles"):
            p = os.path.join(NODEWOX_HOME, x)
            if not os.path.exists(p):
                print("make dir %s" % p)
                os.mkdir(p, 0o755)

        # copy default cacerts
        subprocess.check_output([
            'cp', 'data/cacert.pem', os.path.join(NODEWOX_HOME, "trust/default.pem")
        ])

        install.run(self)


setup(
	name="nodewox-pything",
	version="0.1",

	packages=find_packages(),
        cmdclass={'install': NXInstallCommand},

	author="johnray",
	author_email="996351336@qq.com",
	description="a python framework to write things that connect to nodewox.org",

        entry_points = """
        [console_scripts]
        nx_thing = nodewox.thing.cmd_thing:commands
        """,
)

