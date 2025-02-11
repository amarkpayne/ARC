#!/usr/bin/env python3
# encoding: utf-8

"""
A module for running jobs on the local machine.
When transitioning to Python 3, use
`subprocess.run() <https://docs.python.org/3/library/subprocess.html#subprocess.run>`_
"""

import datetime
import os
import re
import shutil
import subprocess
import time

from arc.common import get_logger
from arc.exceptions import SettingsError
from arc.job.ssh import check_job_status_in_stdout
from arc.settings import servers, check_status_command, submit_command, submit_filename, delete_command, output_filename


logger = get_logger()


def execute_command(command, shell=True):
    """
    Execute a command. `command` is an array of string commands to send.
    If path is not an empty string, the command will be executed in the directory path it points to.
    Returns lists of stdin, stdout, stderr corresponding to the commands sent.
    `shell` specifies whether the command should be executed using bash instead of Python
    """
    if not isinstance(command, list) and not shell:
        command = [command]
    i, max_times_to_try = 1, 30
    success = False
    sleep_time = 60  # seconds
    while i < max_times_to_try:
        try:
            stdout = subprocess.check_output(command, shell=shell)
        except subprocess.CalledProcessError as e:
            logger.error('The server command is erroneous.')
            logger.error(f'Tried to submit the following command:\n{command}')
            logger.error('And got the following status (cmd, message, output, return code)')
            logger.error(e.cmd)
            logger.info('\n')
            logger.error(e)
            logger.info('\n')
            logger.error(e.output)
            logger.info('\n')
            logger.error(e.returncode)
            logger.info('\n')
            logger.error(f'ARC is sleeping for {sleep_time * i} seconds before re-trying,'
                         f' please check if this is a server issue by executing the command manually on server.')
            logger.info('ZZZZZ..... ZZZZZ.....')
            time.sleep(sleep_time * i)  # in seconds
            i += 1
        else:
            success = True
            break
    if not success:
        raise SettingsError(f'The command "{command}" is erroneous, got: \n{e}'
                            f'\nThis maybe either a server issue or the command is wrong.'
                            f'\nTo check if this is a server issue, please run the command on server and restart ARC.'
                            f'\nTo correct the command, modify settings.py'
                            f'\nTips: use "which" command to locate cluster software commands on server.'
                            f'\nExample: type "which sbatch" on a server running Slurm to find the correct '
                            f'sbatch path required in the submit_command dictionary.')
    lines, list_of_strs = stdout.splitlines(), list()
    for line in lines:
        list_of_strs.append(line.decode())
    return list_of_strs, ''


def check_job_status(job_id):
    """
    Possible statuses: `before_submission`, `running`, `errored on node xx`, `done`
    Status line formats:

    OGE::

        540420 0.45326 xq1340b    user_name       r     10/26/2018 11:08:30 long1@node18.cluster

    Slurm::

        14428     debug xq1371m2   user_name  R 50-04:04:46      1 node06

    """
    server = 'local'
    cmd = check_status_command[servers[server]['cluster_soft']] + ' -u ' + servers[server]['un']
    stdout = execute_command(cmd)[0]
    return check_job_status_in_stdout(job_id=job_id, stdout=stdout, server=server)


def delete_job(job_id):
    """
    Deletes a running job
    """
    cmd = delete_command[servers['local']['cluster_soft']] + ' ' + str(job_id)
    execute_command(cmd)


def check_running_jobs_ids():
    """
    Return a list of ``int`` representing job IDs of all jobs submitted by the user on a server
    """
    running_jobs_ids = list()
    cmd = check_status_command[servers['local']['cluster_soft']] + ' -u ' + servers['local']['un']
    stdout = execute_command(cmd)[0]
    for i, status_line in enumerate(stdout):
        if (servers['local']['cluster_soft'].lower() == 'slurm' and i > 0)\
                or (servers['local']['cluster_soft'].lower() == 'oge' and i > 1):
            running_jobs_ids.append(int(status_line.split()[0]))
    return running_jobs_ids


def submit_job(path):
    """
    Submit a job
    `path` is the job's folder path, where the submit script is located (without the submit script file name)
    """
    job_status = ''
    job_id = 0
    cmd = 'cd ' + path + '; ' + submit_command[servers['local']['cluster_soft']] + ' '\
        + submit_filename[servers['local']['cluster_soft']]
    stdout = execute_command(cmd)[0]
    if 'submitted' in stdout[0].lower():
        job_status = 'running'
        if servers['local']['cluster_soft'].lower() == 'oge':
            job_id = int(stdout[0].split()[2])
        elif servers['local']['cluster_soft'].lower() == 'slurm':
            job_id = int(stdout[0].split()[3])
        else:
            raise ValueError('Unrecognized cluster software {0}'.format(servers['local']['cluster_soft']))
    return job_status, job_id


def get_last_modified_time(file_path):
    """returns the last modified time of `file_path` in a datetime format"""
    try:
        timestamp = os.stat(file_path).st_mtime
    except (IOError, OSError):
        return None
    return datetime.datetime.fromtimestamp(timestamp)


def write_file(file_path, file_string):
    """
    Write `file_string` as the file's content in `file_path`
    """
    with open(file_path, 'w') as f:
        f.write(file_string)


def rename_output(local_file_path, software):
    """
    Rename the output file to "output.out" for consistency between software
    `local_file_path` is the full path to the output.out file,
    `software` is the software used for the job by which the original output file name is determined
    """
    software = software.lower()
    if os.path.isfile(os.path.join(os.path.dirname(local_file_path), output_filename[software])):
        shutil.move(src=os.path.join(os.path.dirname(local_file_path), output_filename[software]), dst=local_file_path)


def delete_all_local_arc_jobs():
    """
    Delete all ARC-spawned jobs (with job name starting with `a` and a digit) from the local server.
    Make sure you know what you're doing, so unrelated jobs won't be deleted...
    Useful when terminating ARC while some (ghost) jobs are still running.
    """
    server = 'local'
    if server in servers:
        print('\nDeleting all ARC jobs from local server...')
        cmd = check_status_command[servers[server]['cluster_soft']] + ' -u ' + servers[server]['un']
        stdout = execute_command(cmd)[0]
        for status_line in stdout:
            s = re.search(r' a\d+', status_line)
            if s is not None:
                if servers[server]['cluster_soft'].lower() == 'slurm':
                    job_id = s.group()[1:]
                    server_job_id = status_line.split()[0]
                    delete_job(server_job_id)
                    print('deleted job {0} ({1} on server)'.format(job_id, server_job_id))
                elif servers[server]['cluster_soft'].lower() == 'oge':
                    job_id = s.group()[1:]
                    delete_job(job_id)
                    print('deleted job {0}'.format(job_id))
        print('\ndone.')
