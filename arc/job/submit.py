#!/usr/bin/env python3
# encoding: utf-8

"""
Submit scripts
sorted in a dictionary with server names as keys
"""


submit_scripts = {
    'local': {
        # Gaussian 16
        'gaussian': """#!/bin/bash -l

#$ -N {name}
#$ -l long{architecture}
#$ -l h_rt={t_max}
#$ -l h_vmem={memory}M
#$ -pe singlenode 8
#$ -cwd
#$ -o out.txt
#$ -e err.txt
#$ -l h="node01|node02|node04|node08|node09|node10|node11|node13|node18|node19|node25|node26|node27|node28|node31|node37|node42|node45|node46|node49|node50|node52|node56|node60|node61|node62|node63|node67|node68|node69|node70|node71|node72|node75|node81|node82|node83|node84|node98"

echo "Running on node:"
hostname

g16root=/opt
GAUSS_SCRDIR=/scratch/{un}/{name}
export g16root GAUSS_SCRDIR
. $g16root/g16/bsd/g16.profile
mkdir -p /scratch/{un}/{name}

g16 input.gjf

rm -r /scratch/{un}/{name}

""",
        # QChem 5.2
        'qchem': """#!/bin/bash -l

#$ -N {name}
#$ -l long{architecture}
#$ -l h_rt={t_max}
#$ -pe singlenode {cpus}
#$ -l h=!node60.cluster
#$ -cwd
#$ -o out.txt
#$ -e err.txt

echo "Running on node:"
hostname

source /opt/qchem/qcenv.sh

export QC=/opt/qchem
export QCSCRATCH=/scratch/{un}/{name}
export QCLOCALSCR=/scratch/{un}/{name}/qlscratch
. $QC/qcenv.sh

mkdir -p /scratch/{un}/{name}/qlscratch

qchem -nt {cpus} input.in output.out

rm -r /scratch/{un}/{name}

""",
        # Molpro 2012
        'molpro': """#! /bin/bash -l

#$ -N {name}
#$ -l long{architecture}
#$ -l h_rt={t_max}
#$ -pe singlenode {cpus}
#$ -l h=!node60.cluster
#$ -cwd
#$ -o out.txt
#$ -e err.txt

export PATH=/opt/molpro2012/molprop_2012_1_Linux_x86_64_i8/bin:$PATH

sdir=/scratch/{un}
mkdir -p /scratch/{un}/qlscratch

molpro -d $sdir -n {cpus} input.in

""",
        # OneDMin
        'onedmin': """#! /bin/bash -l

#$ -N {name}
#$ -l long{architecture}
#$ -l h_rt={t_max}
#$ -pe singlenode {cpus}
#$ -l h=!node60.cluster
#$ -cwd
#$ -o out.txt
#$ -e err.txt

WorkDir=`pwd`
cd
sdir=/scratch/{un}
mkdir -p /scratch/{un}/onedmin
cd $WorkDir

~/auto1dmin/exe/auto1dmin.x < input.in > output.out

""",
        # Orca
        'orca': """#!/bin/bash -l

#$ -N {name}
#$ -l long{architecture}
#$ -l h_rt={t_max}
#$ -l h_vmem={memory}M
#$ -pe singlenode {cpus}
#$ -cwd
#$ -o out.txt
#$ -e err.txt

echo "Running on node:"
hostname

export PATH=/opt/orca/:$PATH
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/:/usr/local/etc

WorkDir=/scratch/{un}/{name}
SubmitDir=`pwd`

mkdir -p $WorkDir
cd $WorkDir

cp $SubmitDir/input.in .

/opt/orca/orca input.in > input.log
cp * $SubmitDir/

rm -rf $WorkDir

""",
    }
}
