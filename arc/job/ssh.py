#!/usr/bin/env python3
# encoding: utf-8

"""
A module for SSHing into servers.
Used for giving commands, uploading, and downloading files.

Todo:
    * delete scratch files of a failed job: ssh nodeXX; rm scratch/dhdhdhd/job_number
"""

import datetime
import logging
import os
import re
import time

import paramiko

from arc.common import get_logger
from arc.exceptions import InputError, ServerError
from arc.settings import servers, check_status_command, submit_command, submit_filename, delete_command


logger = get_logger()


class SSHClient(object):
    """
    This is a class for communicating with remote servers via SSH.

    Args:
        server (str): The server name as specified in ARCs's settings file under ``servers`` as a key.

    Attributes:
        server (str): The server name as specified in ARCs's settings file under ``servers`` as a key.
        address (str): The server's address.
        un (str): The username to use on the server.
        key (str): A path to a file containing the RSA SSH private key to the server.
    """
    def __init__(self, server=''):
        if server == '':
            raise ValueError('A server name must be specified')
        if server not in servers.keys():
            raise ValueError('Server name invalid. Currently defined servers are: {0}'.format(servers.keys()))
        self.server = server
        self.address = servers[server]['address']
        self.un = servers[server]['un']
        self.key = servers[server]['key']
        logging.getLogger("paramiko").setLevel(logging.WARNING)

    def send_command_to_server(self, command, remote_path=''):
        """
        Send commands to server. `command` is either a sting or an array of string commands to send.
        If remote_path is not an empty string, the command will be executed in the directory path it points to.
        Returns lists of stdout, stderr corresponding to the commands sent.
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.load_system_host_keys(filename=self.key)
        try:
            ssh.connect(hostname=self.address, username=self.un)
        except:
            return '', 'paramiko failed to connect'
        if isinstance(command, list):
            command = '; '.join(command)
        if remote_path != '':
            # execute command in remote_path directory.
            # Since each `.exec_command()` is a single session, `cd` has to be added to all commands.
            command = 'cd {0}'.format(remote_path) + '; ' + command
        try:
            _, stdout, stderr = ssh.exec_command(command)
        except:  # SSHException: Timeout opening channel.
            try:  # try again
                _, stdout, stderr = ssh.exec_command(command)
            except:
                return '', 'ssh timed-out after two trials'
        stdout = stdout.readlines()
        stderr = stderr.readlines()
        ssh.close()
        return stdout, stderr

    def upload_file(self, remote_file_path, local_file_path='', file_string=''):
        """
        Upload `local_file_path` or the contents of `file_string` to `remote_file_path`.
        Either `file_string` or `local_file_path` must be given.
        """
        if local_file_path and not os.path.isfile(local_file_path):
            raise InputError('Cannot upload a non-existing file.'
                             ' Check why file in path {0} is missing.'.format(local_file_path))
        sftp, ssh = self.connect()
        i, max_times_to_try = 1, 30
        success = False
        sleep_time = 10  # seconds
        while i < 30:
            try:
                write_file(sftp, remote_file_path, local_file_path, file_string)
            except IOError:
                logger.error('Could not upload file {0} to {1}!'.format(local_file_path, self.server))
                logger.error('ARC is sleeping for {0} seconds before re-trying,'
                             ' please check your connectivity.'.format(sleep_time * i))
                logger.info('ZZZZZ..... ZZZZZ.....')
                time.sleep(sleep_time * i)  # in seconds
            else:
                success = True
                i = 1000
            i += 1
        if not success:
            raise ServerError('Could not write file {0} on {1}. Tried {2} times.'.format(
                remote_file_path, self.server, max_times_to_try))
        sftp.close()
        ssh.close()

    def download_file(self, remote_file_path, local_file_path):
        """
        Download a file from `remote_file_path` to `local_file_path`.
        """
        i, max_times_to_try = 1, 30
        success = False
        sleep_time = 10  # seconds
        while i < 30:
            self._download_file(remote_file_path, local_file_path)
            if os.path.isfile(local_file_path):
                success = True
                i = 1000
            else:
                logger.error('Could not download file {0} from {1}!'.format(remote_file_path, self.server))
                logger.error('ARC is sleeping for {0} seconds before re-trying,'
                             ' please check your connectivity.'.format(sleep_time * i))
                logger.info('ZZZZZ..... ZZZZZ.....')
                time.sleep(sleep_time * i)  # in seconds
            i += 1
        if not success:
            raise ServerError('Could not download file {0} from {1}. Tried {2} times.'.format(
                remote_file_path, self.server, max_times_to_try))

    def _download_file(self, remote_file_path, local_file_path):
        """
        Download a file from `remote_file_path` to `local_file_path`.
        """
        sftp, ssh = self.connect()
        try:
            sftp.get(remotepath=remote_file_path, localpath=local_file_path)
        except IOError:
            logger.debug('Got an IOError when trying to download file {0} from {1}'.format(remote_file_path,
                                                                                           self.server))
        sftp.close()
        ssh.close()

    def read_remote_file(self, remote_path, filename):
        """
        Read a remote file. `remote_path` is the remote path (required), a `filename` is also required.
        Returns the file's content.
        """
        sftp, ssh = self.connect()
        full_path = os.path.join(remote_path, filename)
        with sftp.open(full_path, 'r') as f_remote:
            content = f_remote.readlines()
        sftp.close()
        ssh.close()
        return content

    def check_job_status(self, job_id):
        """
        A modulator method of _check_job_status()
        """
        i = 1
        sleep_time = 1  # minutes
        while i < 30:
            result = self._check_job_status(job_id)
            if result == 'connection error':
                logger.error('ARC is sleeping for {0} min before re-trying,'
                             ' please check your connectivity.'.format(sleep_time * i))
                logger.info('ZZZZZ..... ZZZZZ.....')
                time.sleep(sleep_time * i * 60)  # in seconds
            else:
                i = 1000
            i += 1
        return result

    def _check_job_status(self, job_id):
        """
        Possible statuses: `before_submission`, `running`, `errored on node xx`, `done`
        Status line formats:
        pharos: '540420 0.45326 xq1340b    user_name       r     10/26/2018 11:08:30 long1@node18.cluster'
        rmg: '14428     debug xq1371m2   user_name  R 50-04:04:46      1 node06'
        """
        cmd = check_status_command[servers[self.server]['cluster_soft']] + ' -u ' + servers[self.server]['un']
        stdout, stderr = self.send_command_to_server(cmd)
        if stderr:
            logger.info('\n\n')
            logger.error('Could not check status of job {0} due to {1}'.format(job_id, stderr))
            return 'connection error'
        return check_job_status_in_stdout(job_id=job_id, stdout=stdout, server=self.server)

    def delete_job(self, job_id):
        """
        Deletes a running job
        """
        cmd = delete_command[servers[self.server]['cluster_soft']] + ' ' + str(job_id)
        self.send_command_to_server(cmd)

    def check_running_jobs_ids(self):
        """
        Return a list of ``int`` representing job IDs of all jobs submitted by the user on a server
        """
        running_jobs_ids = list()
        cmd = check_status_command[servers[self.server]['cluster_soft']] + ' -u ' + servers[self.server]['un']
        stdout = self.send_command_to_server(cmd)[0]
        for i, status_line in enumerate(stdout):
            if (servers[self.server]['cluster_soft'].lower() == 'slurm' and i > 0)\
                    or (servers[self.server]['cluster_soft'].lower() == 'oge' and i > 1):
                running_jobs_ids.append(int(status_line.split()[0]))
        return running_jobs_ids

    def submit_job(self, remote_path):
        """Submit a job"""
        job_status = ''
        job_id = 0
        cmd = submit_command[servers[self.server]['cluster_soft']] + ' '\
            + submit_filename[servers[self.server]['cluster_soft']]
        stdout, stderr = self.send_command_to_server(cmd, remote_path)
        if len(stderr) > 0 or len(stdout) == 0:
            logger.warning('Got stderr when submitting job:\n{0}'.format(stderr))
            job_status = 'errored'
        elif 'submitted' in stdout[0].lower():
            job_status = 'running'
            if servers[self.server]['cluster_soft'].lower() == 'oge':
                job_id = int(stdout[0].split()[2])
            elif servers[self.server]['cluster_soft'].lower() == 'slurm':
                job_id = int(stdout[0].split()[3])
            else:
                raise ValueError('Unrecognized cluster software {0}'.format(servers[self.server]['cluster_soft']))
        return job_status, job_id

    def connect(self):
        """A helper function for calling self.try_connecting until successful"""
        times_tried = 0
        max_times_to_try = 1440  # continue trying for 24 hrs...
        interval = 60  # wait 60 sec between trials
        while times_tried < max_times_to_try:
            times_tried += 1
            try:
                sftp, ssh = self.try_connecting()
            except:
                pass
            else:
                logger.debug('Successfully connected to {0} at the {1} trial.'.format(self.server, times_tried))
                return sftp, ssh
            if not times_tried % 10:
                logger.info('Tried connecting to {0} {1} times with no success....'.format(self.server, times_tried))
            else:
                print('Tried connecting to {0} {1} times with no success....'.format(self.server, times_tried))
            time.sleep(interval)
        raise ServerError('Could not connect to server {0} even after {1} trials.'.format(self.server, times_tried))

    def try_connecting(self):
        """A helper function for connecting via paramiko, returns the `sftp` and `ssh` objects"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.load_system_host_keys(filename=self.key)
        try:
            ssh.connect(hostname=self.address, username=self.un)
        except:
            # This sometimes gives "SSHException: Error reading SSH protocol banner[Error 104] Connection reset by peer"
            # Try again:
            ssh.connect(hostname=self.address, username=self.un)
        sftp = ssh.open_sftp()
        return sftp, ssh

    def get_last_modified_time(self, remote_file_path):
        """returns the last modified time of `remote_file_path` in a datetime format"""
        sftp, ssh = self.connect()
        try:
            timestamp = sftp.stat(remote_file_path).st_mtime
        except IOError:
            return None
        sftp.close()
        ssh.close()
        return datetime.datetime.fromtimestamp(timestamp)


def write_file(sftp, remote_file_path, local_file_path='', file_string=''):
    """
    Write a file. If `file_string` is given, write it as the content of the file.
    Else, if `local_file_path` is given, copy it to `remote_file_path`.

    Args:
        sftp (paramiko's SFTP): The SFTP object.
        remote_file_path (str): The path to write into on the remote server.
        local_file_path (str, optional): A local file path to be copied into the remote location.
        file_string (str): The file content to be copied and saved as the remote file.
    """
    with sftp.open(remote_file_path, 'w') as f_remote:
        if file_string:
            f_remote.write(file_string)
        elif local_file_path:
            # with open(local_file_path, 'r') as f_local:
            #     f_remote.write(f_local.readlines())
            sftp.put(localpath=local_file_path, remotepath=remote_file_path)
        else:
            raise ValueError('Could not upload file to server. Either `file_string` or `local_file_path`'
                             ' must be specified')


def check_job_status_in_stdout(job_id, stdout, server):
    """
    A helper function for checking job status.

    Args:
        job_id (int): the job ID recognized by the server.
        stdout (list, str): The output of a queue status check.
        server (str): The server name.

    Returns:
        str: The job status on the server ('running', 'done', or 'errored').
    """
    if not isinstance(stdout, list):
        stdout = stdout.splitlines()
    for status_line in stdout:
        if str(job_id) in status_line:
            break
    else:
        return 'done'
    status = status_line.split()[4]
    if status.lower() in ['r', 'qw', 't']:
        return 'running'
    else:
        if servers[server]['cluster_soft'].lower() == 'oge':
            if '.cluster' in status_line:
                try:
                    return 'errored on node ' + status_line.split()[-1].split('@')[1].split('.')[0][-2:]
                except IndexError:
                    return 'errored'
            else:
                return 'errored'
        elif servers[server]['cluster_soft'].lower() == 'slurm':
            return 'errored on node ' + status_line.split()[-1][-2:]
        else:
            raise ValueError('Unknown cluster software {0}'.format(servers[server]['cluster_soft']))


def delete_all_arc_jobs(server_list):
    """
    Delete all ARC-spawned jobs (with job name starting with `a` and a digit) from :list:servers
    (`servers` could also be a string of one server name)
    Make sure you know what you're doing, so unrelated jobs won't be deleted...
    Useful when terminating ARC while some (ghost) jobs are still running.

    Args:
        server_list (list): List of servers to delete ARC jobs from.
    """
    if isinstance(server_list, str):
        server_list = [server_list]
    for server in server_list:
        print('\nDeleting all ARC jobs from {0}...'.format(server))
        cmd = check_status_command[servers[server]['cluster_soft']] + ' -u ' + servers[server]['un']
        ssh = SSHClient(server)
        stdout = ssh.send_command_to_server(cmd)[0]
        for status_line in stdout:
            s = re.search(r' a\d+', status_line)
            if s is not None:
                if servers[server]['cluster_soft'].lower() == 'slurm':
                    job_id = s.group()[1:]
                    server_job_id = status_line.split()[0]
                    ssh.delete_job(server_job_id)
                    print('deleted job {0} ({1} on server)'.format(job_id, server_job_id))
                elif servers[server]['cluster_soft'].lower() == 'oge':
                    job_id = s.group()[1:]
                    ssh.delete_job(job_id)
                    print('deleted job {0}'.format(job_id))
    if server_list:
        print('\ndone.')
