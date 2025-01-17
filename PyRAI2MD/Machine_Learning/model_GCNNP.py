#####################################################
#
# PyRAI2MD 2 module for interfacing to E2N2 (GCNNP)
#
# Author Jingbai Li
# Sep 1 2022
#
######################################################

import os
import time
import numpy as np

from PyRAI2MD.Machine_Learning.hyper_gcnnp import set_e2n2_hyper_eg
from PyRAI2MD.Machine_Learning.hyper_gcnnp import set_e2n2_hyper_nac
from PyRAI2MD.Machine_Learning.hyper_gcnnp import set_e2n2_hyper_soc
from PyRAI2MD.Machine_Learning.model_helper import Multiregions
from PyRAI2MD.Utils.coordinates import numerize_xyz
from PyRAI2MD.Utils.timing import what_is_time
from PyRAI2MD.Utils.timing import how_long

from GCNNP.gcnnp import GCNNP
from GCNNP.gcnnp import SetupTools

class E2N2:
    """ pyNNsMD interface

        Parameters:          Type:
            keywords         dict        keywords dict
            id               int         calculation index

        Attribute:           Type:
            hyp_eg           dict        Hyperparameters of energy gradient NN
       	    hyp_nac          dict        Hyperparameters of nonadiabatic coupling NN
       	    hyp_soc          dict     	 Hyperparameters of spin-orbit coupling NN
            energy           ndarray     energy array
            grad             ndarray     gradient array
            nac              ndarray     nonadiabatic coupling array
            soc              ndarray     spin-orbit coupling array
            atoms            list        atom list
            geos             ndarray     training set coordinates
            pred_atoms       list        atom list
            pred_geos        ndarray     prediction set coordinates
            pred_energy      ndarray     prediction set target energy
            pred_grad        ndarray     prediction set target grad
            pred_nac         ndarray     prediction set target nac
            pred_soc         ndarray     prediction set target soc
            atomic_numbers   list        atomic number list
            multiscale       list        atom indices in multiscale regions

        Functions:           Returns:
            train            self        train NN for a given training set
            load             self        load trained NN for prediction
            appendix         self        fake function
            evaluate         self        run prediction

    """

    def __init__(self, keywords=None, job_id=None):

        title = keywords['control']['title']
        variables = keywords['e2n2'].copy()
        modeldir = variables['modeldir']
        data = variables['data']
        nn_eg_type = variables['nn_eg_type']
        nn_nac_type = variables['nn_nac_type']
        nn_soc_type = variables['nn_soc_type']
        multiscale = variables['multiscale']
        hyp_eg = variables['e2n2_eg'].copy()
        hyp_nac = variables['e2n2_nac'].copy()
        hyp_soc = variables['e2n2_soc'].copy()
        eg_unit = variables['eg_unit']
        nac_unit = variables['nac_unit']
        soc_unit = variables['soc_unit']
        self.jobtype = keywords['control']['jobtype']
        self.version = keywords['version']
        self.ncpu = keywords['control']['ml_ncpu']
        self.train_mode = variables['train_mode']
        self.shuffle = variables['shuffle']
        self.splits = variables['nsplits']
        self.natom = data.natom
        self.nstate = data.nstate
        self.nnac = data.nnac
        self.nsoc = data.nsoc

        ## set hyperparameters
        hyp_dict_eg = set_e2n2_hyper_eg(hyp_eg, eg_unit, data.info, self.splits)
        hyp_dict_eg2 = set_e2n2_hyper_eg(hyp_eg, eg_unit, data.info, self.splits)
        hyp_dict_nac = set_e2n2_hyper_nac(hyp_nac, nac_unit, data.info, self.splits)
        hyp_dict_nac2 = set_e2n2_hyper_nac(hyp_nac, nac_unit, data.info, self.splits)
        hyp_dict_soc = set_e2n2_hyper_soc(hyp_soc, soc_unit, data.info, self.splits)
        hyp_dict_soc2 = set_e2n2_hyper_soc(hyp_soc, soc_unit, data.info, self.splits)

        ## retraining has some bug at the moment, do not use
        if self.train_mode not in ['training', 'retraining', 'resample']:
            self.train_mode = 'training'

        if job_id is None or job_id == 1:
            self.name = f"NN-{title}"
        else:
            self.name = f"NN-{title}-{job_id}"

        self.silent = variables['silent']

        ## prepare unit conversion for energy and force. au or si. The data units are in au.
        h_to_ev = 27.211396132
        h_bohr_to_ev_a = 27.211396132 / 0.529177249

        if eg_unit == 'si':
            self.f_e = h_to_ev
            self.f_g = h_bohr_to_ev_a
            self.k_e = 1
            self.k_g = 1
        else:
            self.f_e = 1
            self.f_g = 1
            self.k_e = h_to_ev
            self.k_g = h_bohr_to_ev_a

        if nac_unit == 'si':
            self.f_n = h_bohr_to_ev_a  # convert to eV/A
            self.k_n = 1
        else:
            self.f_n = 1  # convert to Eh/B
            self.k_n = h_bohr_to_ev_a

        ## unpack data
        self.xyz = data.xyz
        self.energy = data.energy * self.f_e
        self.grad = data.grad * self.f_g
        self.nac = data.nac * self.f_n
        self.soc = data.soc
        self.pred_xyz = data.pred_atoms
        self.pred_energy = data.pred_energy
        self.pred_grad = data.pred_grad
        self.pred_nac = data.pred_nac
        self.pred_soc = data.pred_soc

        if len(multiscale) > 0:
            self.mr = Multiregions(data.atoms[0], multiscale)
        else:
            self.mr = None

        ## initialize model path
        if modeldir is None or job_id not in [None, 1]:
            self.model_path = self.name
        else:
            self.model_path = modeldir

        self.model_register = {
            'energy_grad': False,
            'nac': False,
            'soc': False
        }

        ## initialize hypers and train data
        self.y_dict = {
            'energy_grad': [],
            'nac': [],
            'soc': []
        }

        if nn_eg_type > 0:
            self.y_dict['energy_grad'] = [self.energy.tolist(), self.grad.tolist()]
            self.model_register['energy_grad'] = True
            hyper_eg = [hyp_dict_eg, hyp_dict_eg2]
        else:
            self.model_register['energy_grad'] = False
            hyper_eg = []

        if nn_nac_type > 0:
            self.y_dict['nac'] = [None, self.nac.tolist()]
            self.model_register['nac'] = True
            hyper_nac = [hyp_dict_nac, hyp_dict_nac2]
        else:
            self.model_register['nac'] = False
            hyper_nac = []

        if nn_soc_type > 0:
            self.y_dict['soc'] = [self.soc.tolist(), None]
            self.model_register['soc'] = True
            hyper_soc = [hyp_dict_soc, hyp_dict_soc2]
        else:
            self.model_register['soc'] = False
            hyper_soc = []

        self.hypers = hyper_eg + hyper_nac + hyper_soc

        # initialize a model to load a trained method
        self.model = GCNNP(self.model_path, self.hypers)

    def _heading(self):

        headline = """
%s
 *---------------------------------------------------*
 |                                                   |
 |                     Schnet                        |
 | A continuous-filter convolutional neural network  |
 |                                                   |
 |              powered by pyNNsMD                   |
 |                                                   |
 *---------------------------------------------------*

 Number of atoms:  %s
 Number of state:  %s
 Number of NAC:    %s
 Number of SOC:    %s

""" % (
            self.version,
            self.natom,
            self.nstate,
            self.nnac,
            self.nsoc
        )

        return headline

    def train(self):
        start = time.time()
        topline = 'Neural Networks Start: %20s\n%s' % (what_is_time(), self._heading())
        runinfo = """\n  &nn fitting \n"""

        if self.silent == 0:
            print(topline)
            print(runinfo)

        with open('%s.log' % self.name, 'w') as log:
            log.write(topline)
            log.write(runinfo)

        xyz = numerize_xyz(self.xyz)

        if self.mr:
            node_type, xyz = self.mr.update_xyz(xyz)
        else:
            node_type = np.unique(np.array(xyz)[:, :, 0]).astype(int).tolist()

        for n, _ in enumerate(self.hypers):
            cutoff = self.hypers[n]['model']['config']['maxradius']
            nedges = self.hypers[n]['model']['config']['nedges']

            edge_list = SetupTools.edge_from_radius(
                xyz,
                cutoff=cutoff,
                nedges=nedges
            )

            self.hypers[n]['model']['config']['node_info'] = node_type
            self.hypers[n]['model']['config']['edge_list'] = edge_list

        model = GCNNP(self.model_path, self.hypers)
        model.build()
        errors = model.train(xyz, self.y_dict)[0]

        if self.model_register['energy_grad']:
            eg_error = errors['energy_grad']
            err_e1 = eg_error[0][0][0]
            err_e2 = eg_error[1][0][0]
            err_g1 = eg_error[0][0][1]
            err_g2 = eg_error[1][0][1]
        else:
            err_e1 = 0
            err_e2 = 0
            err_g1 = 0
            err_g2 = 0

        if self.model_register['nac']:
            nac_error = errors['nac']
            err_n1 = nac_error[0][0][0]
            err_n2 = nac_error[1][0][0]
        else:
            err_n1 = 0
            err_n2 = 0

        if self.model_register['soc']:
            soc_error = errors['soc']
            err_s1 = soc_error[0][0][0]
            err_s2 = soc_error[1][0][0]
        else:
            err_s1 = 0
            err_s2 = 0

        metrics = {
            'e1': err_e1 * self.k_e,
            'g1': err_g1 * self.k_g,
            'n1': err_n1 / self.k_n,
            's1': err_s1,
            'e2': err_e2 * self.k_e,
            'g2': err_g2 * self.k_g,
            'n2': err_n2 / self.k_n,
            's2': err_s2
        }

        train_info = """
  &nn validation mean absolute error
-------------------------------------------------------
      energy       gradient       nac          soc
        eV           eV/A         eV/A         cm-1
  %12.8f %12.8f %12.8f %12.8f
  %12.8f %12.8f %12.8f %12.8f

""" % (
            metrics['e1'], metrics['g1'], metrics['n1'], metrics['s1'],
            metrics['e2'], metrics['g2'], metrics['n2'], metrics['s2']
        )

        end = time.time()
        walltime = how_long(start, end)
        endline = 'Neural Networks End: %20s Total: %20s\n' % (what_is_time(), walltime)

        if self.silent == 0:
            print(train_info)
            print(endline)

        with open('%s.log' % self.name, 'a') as log:
            log.write(train_info)
            log.write(endline)

        metrics['time'] = end - start
        metrics['walltime'] = walltime
        metrics['path'] = os.getcwd()
        metrics['status'] = 1

        return metrics

    def load(self):
        self.model.load()

        return self

    def appendix(self, _):
        ## fake	function does nothing

        return self

    def _qm(self, traj):
        ## run psnnsmd for QM calculation
        atoms = traj.atoms.reshape((1, self.natom, 1))
        coord = traj.coord.reshape((1, self.natom, 3))
        x = np.concatenate((atoms, coord), axis=2)
        x = numerize_xyz(x)

        if self.mr:
            _, x = self.mr.update_xyz(x)

        results = self.model.predict(x)
        if self.model_register['energy_grad']:
            pred = results['energy_grad']
            energy = np.mean([pred[0][0], pred[1][0]], axis=0) / self.f_e
            e_std = np.std([pred[0][0], pred[1][0]], axis=0, ddof=1) / self.f_e
            gradient = np.mean([pred[0][1], pred[1][1]], axis=0) / self.f_g
            g_std = np.std([pred[0][0], pred[1][0]], axis=0, ddof=1) / self.f_g
            err_e = np.amax(e_std)
            err_g = np.amax(g_std)
        else:
            energy = []
            gradient = []
            err_e = 0
            err_g = 0

        if self.model_register['nac']:
            pred = results['nac']
            nac = np.mean([pred[0][1], pred[1][1]], axis=0) / self.f_n
            n_std = np.std([pred[0][1], pred[1][1]], axis=0, ddof=1) / self.f_n
            err_n = np.amax(n_std)
        else:
            nac = []
            err_n = 0

        if self.model_register['soc']:
            pred = results['soc']
            soc = np.mean([pred[0][0], pred[1][0]], axis=0)
            s_std = np.std([pred[0][0], pred[1][0]], axis=0, ddof=1)
            err_s = np.amax(s_std)
        else:
            soc = []
            err_s = 0

        return energy, gradient, nac, soc, err_e, err_g, err_n, err_s

    def _predict(self, x):
        ## run psnnsmd for model testing

        batch = len(x)

        x = numerize_xyz(x)

        if self.mr:
            _, x = self.mr.update_xyz(x)

        results = self.model.predict(x)

        if self.model_register['energy_grad']:
            pred = results['energy_grad']
            e_pred = np.mean([pred[0][0], pred[1][0]], axis=0) / self.f_e
            e_std = np.std([pred[0][0], pred[1][0]], axis=0, ddof=1) / self.f_e
            g_pred = np.mean([pred[0][1], pred[1][1]], axis=0) / self.f_g
            g_std = np.std([pred[0][0], pred[1][0]], axis=0, ddof=1) / self.f_g

            de = np.abs(self.pred_energy - e_pred)
            dg = np.abs(self.pred_grad - g_pred)
            de_max = np.amax(de.reshape((batch, -1)), axis=1)
            dg_max = np.amax(dg.reshape((batch, -1)), axis=1)
            val_out = np.concatenate((self.pred_energy.reshape((batch, -1)), e_pred.reshape((batch, -1))), axis=1)
            std_out = np.concatenate((de.reshape((batch, -1)), e_std.reshape((batch, -1))), axis=1)
            np.savetxt('%s-e.pred.txt' % self.name, np.concatenate((val_out, std_out), axis=1))

            val_out = np.concatenate((self.pred_grad.reshape((batch, -1)), g_pred.reshape((batch, -1))), axis=1)
            std_out = np.concatenate((dg.reshape((batch, -1)), g_std.reshape((batch, -1))), axis=1)
            np.savetxt('%s-g.pred.txt' % self.name, np.concatenate((val_out, std_out), axis=1))
        else:
            de_max = np.zeros(batch)
            dg_max = np.zeros(batch)

        if self.model_register['nac']:
            pred = results['nac']
            n_pred = np.mean([pred[0][1], pred[1][1]], axis=0) / self.f_n
            n_std = np.std([pred[0][1], pred[1][1]], axis=0, ddof=1) / self.f_n

            dn = np.abs(self.pred_nac - n_pred)
            dn_max = np.amax(dn.reshape((batch, -1)), axis=1)

            val_out = np.concatenate((self.pred_nac.reshape((batch, -1)), n_pred.reshape((batch, -1))), axis=1)
            std_out = np.concatenate((dn.reshape((batch, -1)), n_std.reshape((batch, -1))), axis=1)
            np.savetxt('%s-n.pred.txt' % self.name, np.concatenate((val_out, std_out), axis=1))
        else:
            dn_max = np.zeros(batch)

        if self.model_register['soc']:
            pred = results['soc']
            s_pred = np.mean([pred[0][0], pred[1][0]], axis=0)
            s_std = np.std([pred[0][0], pred[1][0]], axis=0, ddof=1)

            ds = np.abs(self.pred_soc - s_pred)
            ds_max = np.amax(ds.reshape((batch, -1)), axis=1)

            val_out = np.concatenate((self.pred_soc.reshape((batch, -1)), s_pred.reshape((batch, -1))), axis=1)
            std_out = np.concatenate((ds.reshape((batch, -1)), s_std.reshape((batch, -1))), axis=1)
            np.savetxt('%s-s.pred.txt' % self.name, np.concatenate((val_out, std_out), axis=1))
        else:
            ds_max = np.zeros(batch)

        output = ''
        for i in range(batch):
            output += '%5s %8.4f %8.4f %8.4f %8.4f\n' % (i + 1, de_max[i], dg_max[i], dn_max[i], ds_max[i])

        with open('max_abs_dev.txt', 'w') as out:
            out.write(output)

        return self

    def evaluate(self, traj):
        ## main function to run pyNNsMD and communicate with other PyRAI2MD modules

        if self.jobtype == 'prediction' or self.jobtype == 'predict':
            self._predict(self.pred_xyz)
        else:
            energy, gradient, nac, soc, err_energy, err_grad, err_nac, err_soc = self._qm(traj)
            traj.energy = np.copy(energy)
            traj.grad = np.copy(gradient)
            traj.nac = np.copy(nac)
            traj.soc = np.copy(soc)
            traj.err_energy = err_energy
            traj.err_grad = err_grad
            traj.err_nac = err_nac
            traj.err_soc = err_soc
            traj.status = 1

            return traj
