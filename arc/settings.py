#!/usr/bin/env python3
# encoding: utf-8

"""
ARC's settings
"""

import os
import string

##################################################################

# If ARC communication with remote servers is desired, complete the following server dictionary.
# Instructions for RSA key generation can be found here:
# https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys--2
# If ARC is being executed on a server, and ESS are available on that server, define a server named 'local',
# for which only the cluster software and user name are required.
# servers = {
#     'pharos': {
#         'cluster_soft': 'OGE',  # Oracle Grid Engine (Sun Grin Engine)
#         'address': 'pharos.mit.edu',
#         'un': '<username>',
#         'key': '/home/<username>/.ssh/known_hosts',
#     },
#     'rmg': {
#         'cluster_soft': 'Slurm',  # Simple Linux Utility for Resource Management
#         'address': 'rmg.mit.edu',
#         'un': '<username>',
#         'key': '/home/<username>/.ssh/id_rsa',
#     },
#    'local': {
#        'cluster_soft': 'OGE',
#        'un': '<username>',
#    },
# }
servers = {
    'local': {
        'cluster_soft': 'OGE',
        'un': 'ampayne',
	'cpus': 8,
	'memory': 5,
    },
}

# List here servers you'd like to associate with specific ESS.
# An ordered list of servers indicates priority
# Keeping this dictionary empty will cause ARC to scan for software on the servers defined above
global_ess_settings = {
    'gaussian': 'local',
    'qchem': 'local',
}

# List here job types to execute by default
default_job_types = {'conformers': False,      # defaults to True if not specified
                     'opt': True,             # defaults to True if not specified
                     'fine_grid': True,       # defaults to True if not specified
                     'freq': True,            # defaults to True if not specified
                     'sp': False,              # defaults to True if not specified
                     'rotors': False,       # defaults to True if not specified
                     'irc': False,             # defaults to True if not specified
                     'orbitals': False,       # defaults to False if not specified
                     'lennard_jones': False,  # defaults to False if not specified
                     'bde': False,            # defaults to False if not specified
                     }

supported_ess = ['gaussian', 'qchem']  # use lowercase when adding new ones

# List here (complete or partial) phrases of methods or basis sets you'd like to associate to specific ESS
# Avoid ascribing the same phrase to more than one software, this may cause undeterministic assignment of software
# Format is levels_ess = {ess: ['phrase1', 'phrase2'], ess2: ['phrase3', 'phrase3']}
levels_ess = {
    'gaussian': ['apfd', 'b3lyp', 'm062x'],
    'molpro': ['ccsd', 'cisd', 'vpz'],
    'qchem': ['m06-2x'],
    'orca': ['dlpno'],
    'terachem': ['pbe'],
}

check_status_command = {'OGE': 'export SGE_ROOT=/opt/sge; /opt/sge/bin/lx24-amd64/qstat',
                        'Slurm': '/usr/bin/squeue'}

submit_command = {'OGE': 'export SGE_ROOT=/opt/sge; /opt/sge/bin/lx24-amd64/qsub',
                  'Slurm': '/usr/bin/sbatch'}

delete_command = {'OGE': 'export SGE_ROOT=/opt/sge; /opt/sge/bin/lx24-amd64/qdel',
                  'Slurm': '/usr/bin/scancel'}

list_available_nodes_command = {'OGE': 'export SGE_ROOT=/opt/sge; /opt/sge/bin/lx24-amd64/qstat -f | grep "/8 " | grep "long" | grep -v "8/8"| grep -v "aAu"',
                                'Slurm': 'sinfo'}

submit_filename = {'OGE': 'submit.sh',
                   'Slurm': 'submit.sl'}

t_max_format = {'OGE': 'hours',
                'Slurm': 'days'}

input_filename = {'gaussian': 'input.gjf',
                  'molpro': 'input.in',
                  'onedmin': 'input.in',
                  'orca': 'input.in',
                  'qchem': 'input.in',
                  'terachem': 'input.in',
                  }

output_filename = {'gaussian': 'input.log',
                   'gromacs': 'output.yml',
                   'molpro': 'input.out',
                   'onedmin': 'output.out',
                   'orca': 'input.log',
                   'qchem': 'output.out',
                   'terachem': 'output.out',
                   }

default_levels_of_theory = {'conformer': 'wb97xd/def2svp',  # it's recommended to choose a method with dispersion
                            'ts_guesses': 'wb97xd/def2svp',
                            'opt': 'wb97xd/def2tzvp',  # good default for Gaussian
                            # 'opt': 'wb97m-v/def2tzvp',  # good default for QChem
                            'freq': 'wb97xd/def2tzvp',  # should be the same level as opt (to calc freq at min E)
                            'scan': 'wb97xd/def2tzvp',  # should be the same level as freq (to project out rotors)
                            'sp': 'ccsd(t)-f12/cc-pvtz-f12',  # This should be a level for which BAC is available
                            # 'sp': 'b3lyp/6-311+g(3df,2p)',
                            'irc': 'wb97xd/def2tzvp',  # should be the same level as opt
                            'orbitals': 'wb97x-d3/def2tzvp',  # save orbitals for visualization
                            'scan_for_composite': 'B3LYP/CBSB7',  # This is the frequency level of CBS-QB3
                            'freq_for_composite': 'B3LYP/CBSB7',  # This is the frequency level of CBS-QB3
                            'irc_for_composite': 'B3LYP/CBSB7',  # This is the frequency level of CBS-QB3
                            'orbitals_for_composite': 'B3LYP/CBSB7',  # This is the frequency level of CBS-QB3
                            }

# Software specific default settings
# Orca
# ARC accepts all the Orca options listed in the dictionary below. For specifying additional Orca options, please see
# documentation and Orca manual.
orca_default_options_dict = {'opt': {'keyword': {'opt_convergence': 'NormalOpt',
                                                 'fine_opt_convergence': 'TightOpt'}},
                             'freq': {'keyword': {'use_num_freq': False}},
                             'global': {'keyword': {'scf_convergence': 'TightSCF',
                                                    'dlpno_threshold': 'normalPNO'}}
                             }

# default_ts_methods = ['QST2', 'DEGSM', 'NEB', 'Kinbot', 'AutoTST']
default_ts_methods = []

arc_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))  # absolute path to the ARC folder

valid_chars = "-_()[]=., %s%s" % (string.ascii_letters, string.digits)

# A scan with better resolution (lower number here) takes more time to compute,
# but the automatically-derived rotor symmetry number is more likely to be correct.
rotor_scan_resolution = 8.0  # degrees. Default: 8.0

# rotor validation parameters
maximum_barrier = 40    # a rotor threshold (kJ/mol) above which the mode will be considered as vibrational if
                        # there's only one well. Default: 40 (~10 kcal/mol)
minimum_barrier = 1.0   # a rotor threshold (kJ/mol) below which it is considered a FreeRotor. Default: 1.0 kJ/mol
inconsistency_az = 5    # maximum allowed inconsistency (kJ/mol) between initial and final rotor scan points. Default: 5
inconsistency_ab = 0.3  # maximum allowed inconsistency between consecutive points in the scan given as a fraction
#  of the maximum scan energy. Default: 30%
