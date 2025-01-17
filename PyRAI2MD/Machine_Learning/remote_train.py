######################################################
#
# PyRAI2MD 2 module for distributing NN training
#
# Author Jingbai Li
# Sep 29 2021
#
######################################################

import os
import sys
import subprocess
import json
import time

from PyRAI2MD.Utils.timing import how_long

class RemoteTrain:
    """ NN remote training class

        Parameters:          Type:
            keywords         dict        keyword dictionary
            id               str         training id string

        Attribute:           Type:
            keywords         dict        keyword dictionary
            title            str         calculation title
            calcdir          str         calculation directory
            pyrai2mddir      str         PyRAI2MD directory
            use_hpc          int         use HPC (1) for calculation or not(0), like SLURM.

        Functions:           Returns:
            train            dict        training metrics
    """

    def __init__(self, keywords=None, id=None):
        ## get keywords info
        self.keywords = keywords.copy()
        self.title = keywords['control']['title']
        self.keywords['control']['jobtype'] = 'train'
        self.use_hpc = keywords['nn']['search']['use_hpc']
        self.retrieve = keywords['nn']['search']['retrieve']

        self.calcdir = '%s/grid-search/NN-%s-%s' % (os.getcwd(), self.title, id)

        self.runscript = """export INPUT=input.json
export WORKDIR=%s

cd $WORKDIR
pyrai2md.py $INPUT
""" % self.calcdir

    def _setup_hpc(self):
        ## setup HPC
        ## read slurm template from .slurm files
        if os.path.exists('%s.slurm' % self.title):
            with open('%s.slurm' % self.title) as template:
                submission = template.read()
        else:
            sys.exit('\n  FileNotFoundError\n  PyRAI2MD: looking for submission file %s.slurm' % self.title)

        submission += self.runscript

        with open('%s/%s.sbatch' % (self.calcdir, self.title), 'w') as out:
            out.write(submission)

        return self

    def _setup_training(self):
        ## write PyRAI2MD input
        if not os.path.exists(self.calcdir):
            os.makedirs(self.calcdir)

        with open('%s/input.json' % self.calcdir, 'w') as out:
            json.dump(self.keywords, out, indent=2)

        ## write run script
        with open('%s/%s.sh' % (self.calcdir, self.title), 'w') as out:
            out.write(self.runscript)

        ## setup HPC setting
        if self.use_hpc == 1:
            self._setup_hpc()

        return self

    def _start_training(self):
        ## distribute NN training
        maindir = os.getcwd()
        os.chdir(self.calcdir)
        if self.use_hpc == 1:
            subprocess.run(['sbatch', '-W', '%s/%s.sbatch' % (self.calcdir, self.title)])
        else:
            subprocess.run(['bash', '%s/%s.sh' % (self.calcdir, self.title)])
        os.chdir(maindir)

        return self

    def _read_training(self):
        ## read training metrics
        if not os.path.exists('%s/NN-%s.log' % (self.calcdir, self.title)):
            return {'path': self.calcdir, 'status': 0}

        with open('%s/NN-%s.log' % (self.calcdir, self.title), 'r') as out:
            log = out.read().splitlines()

        nn1 = None
        nn2 = None
        log = log[-10:]
        for n, line in enumerate(log):
            if """&nn validation mean absolute error""" in line:
                nn1 = log[n + 4]
                nn2 = log[n + 5]

        if nn1 and nn2:
            nn1 = [float(x) for x in nn1.split()]
            nn2 = [float(x) for x in nn2.split()]
        else:
            sys.exit('\n  RuntimeError\n  PyRAI2MD: looking for training log but not found')

        metrics = {
            'path': self.calcdir,
            'status': 1,
            'e1': nn1[0],
            'g1': nn1[1],
            'n1': nn1[2],
            's1': nn1[3],
            'e2': nn2[0],
            'g2': nn2[1],
            'n2': nn2[2],
            's2': nn2[3],
        }

        return metrics

    def train(self):
        start = time.time()

        if self.retrieve == 0:
            self._setup_training()
            self._start_training()

        metrics: dict
        metrics = self._read_training()

        end = time.time()
        walltime = how_long(start, end)

        metrics['time'] = end - start
        metrics['walltime'] = walltime

        return metrics
