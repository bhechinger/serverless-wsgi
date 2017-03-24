#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module loads a `requirements.txt` and uses `virtualenv`/`pip` to
install the required Python packages into the specified directory.

Inspired by: https://github.com/awslabs/chalice

Author: Logan Raarup <logan@logan.dk>
"""
import os
import platform
import shutil
import subprocess
import sys

try:
    import virtualenv
except ImportError:
    sys.exit('Unable to load virtualenv, please install')


def package(req_files, target_dir):
    venv_dir = os.path.join(target_dir, '.venv')
    tmp_dir = os.path.join(target_dir, '.tmp')

    for req_file in req_files:
        if not os.path.isfile(req_file):
            sys.exit('No requirements file found in: {}'.format(req_file))

    if os.path.exists(target_dir):
        if not os.path.isdir(target_dir):
            sys.exit('Existing non-directory found at: {}'.format(target_dir))
    else:
        os.mkdir(target_dir)

    if os.path.exists(venv_dir):
        shutil.rmtree(venv_dir)

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    original = sys.argv
    sys.argv = ['', venv_dir, '--quiet']
    try:
        virtualenv.main()
    finally:
        sys.argv = original

    if platform.system() == 'Windows':
        pip_exe = os.path.join(venv_dir, 'Scripts', 'pip.exe')
        deps_dir = os.path.join(venv_dir, 'Lib', 'site-packages')
    else:
        pip_exe = os.path.join(venv_dir, 'bin', 'pip')
        python_dir = os.listdir(os.path.join(venv_dir, 'lib'))[0]
        deps_dir = os.path.join(venv_dir, 'lib', python_dir, 'site-packages')

    if not os.path.isfile(pip_exe):
        sys.exit('Pip not found in: {}'.format(pip_exe))

    for req_file in req_files:
        p = subprocess.Popen([pip_exe, 'install', '-r', req_file],
                             stdout=subprocess.PIPE)
        p.communicate()
        if p.returncode != 0:
            sys.exit("Failed to install requirements from: {}".format(
                req_file))

    if not os.path.isdir(deps_dir):
        sys.exit('Installed packages not found in: {}'.format(deps_dir))

    blacklist = [
        'pip', 'pip-*', 'wheel', 'wheel-*', 'setuptools',
        'setuptools-*', 'easy_install.*']

    shutil.copytree(deps_dir, tmp_dir, symlinks=False,
                    ignore=shutil.ignore_patterns(*blacklist))
    for f in os.listdir(tmp_dir):
        target = os.path.join(target_dir, f)
        if os.path.isdir(target):
            shutil.rmtree(target)
        elif os.path.exists(target):
            os.remove(target)
        shutil.move(os.path.join(tmp_dir, f), target_dir)
    shutil.rmtree(venv_dir)
    shutil.rmtree(tmp_dir)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit('Usage: {} REQ_FILE... TARGET_DIR'.format(
            os.path.basename(sys.argv[0])))

    package(sys.argv[1:-1], sys.argv[-1])
