#!/usr/bin/env python3
# encoding: utf-8

"""
Submit scripts
sorted in a dictionary with server names as keys
"""


submit_scripts = {
    'local': {
        # QChem 5.2
        'qchem': """#!/bin/bash -l
#SBATCH -q shared
#SBATCH -J {name}
#SBATCH -n {cpus}
#SBATCH --time={t_max}
#SBATCH --mem-per-cpu {memory}
#SBATCH -L cscratch1
#SBATCH -C haswell

module load qchem/5.2
which qchem

echo "============================================================"
echo "Job ID : $SLURM_JOB_ID"
echo "Job Name : $SLURM_JOB_NAME"
echo "Starting on : $(date)"
echo "Running on node : $SLURMD_NODENAME"
echo "Current directory : $(pwd)"
echo "============================================================"

echo "Running on node:"
hostname


# Run the job

qchem -nt {cpus} input.in output.out
""",

        # Orca
        'orca': """#!/bin/bash -l
#SBATCH -p defq
#SBATCH -J {name}
#SBATCH -N 1
#SBATCH -n {cpus}
#SBATCH --time={t_max}
#SBATCH --mem-per-cpu={memory}

module add c3ddb/orca/4.1.2
module add c3ddb/openmpi/3.1.3
which orca

export ORCA_DIR=/cm/shared/modulefiles/c3ddb/orca/4.1.2/
export OMPI_DIR=/cm/shared/modulefiles/c3ddb/openmpi/3.1.3/
export PATH=$PATH:$ORCA_DIR
export PATH=$PATH:$OMPI_DIR

echo "============================================================"
echo "Job ID : $SLURM_JOB_ID"
echo "Job Name : $SLURM_JOB_NAME"
echo "Starting on : $(date)"
echo "Running on node : $SLURMD_NODENAME"
echo "Current directory : $(pwd)"
echo "============================================================"


WorkDir=/scratch/users/{un}/$SLURM_JOB_NAME-$SLURM_JOB_ID
SubmitDir=`pwd`

mkdir -p $WorkDir
cd $WorkDir

cp $SubmitDir/input.inp .

${ORCA_DIR}/orca input.inp > input.log
cp * $SubmitDir/

rm -rf $WorkDir

""",

    }
}
