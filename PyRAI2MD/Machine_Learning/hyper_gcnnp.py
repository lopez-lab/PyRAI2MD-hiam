#####################################################
#
# PyRAI2MD 2 module for GCNNP hyperparameter
#
# Author Jingbai Li
# Sep 1 2022
#
######################################################

def set_e2n2_hyper_eg(hyp, unit, info, splits):
    """ Generating hyperparameter dict for energy+gradient NN

        Parameters:          Type:
            hyp              dict     hyperparameter input
            unit             str      unit scheme
            info             dict     training data information

        Return:              Type:
            hyp_ditc         dict     hyperparameter dict for NN

    """

    ## setup regularization dict
    penalty = 'use_reg_loss'
    penalty_key = '%s_dict' % penalty
    if hyp[penalty] == 'l1':
        hyp[penalty_key] = {'class_name': 'l1', 'config': {'l1': hyp['reg_l1']}}
    elif hyp[penalty] == 'l2':
        hyp[penalty_key] = {'class_name': 'l2', 'config': {'l2': hyp['reg_l2']}}
    elif hyp[penalty] == 'l1_l2':
        hyp[penalty_key] = {'class_name': 'l1_l2', 'config': {'l1': hyp['reg_l1'], 'l2': hyp['reg_l2']}}
    else:
        hyp[penalty_key] = None

    ## setup callbacks
    if hyp['use_step_callback']:
        hyp['callbacks'] = {
            'stepwise': True,
            'epoch_step_reduction': hyp['epoch_step_reduction'],
            'learning_rate_step': hyp['learning_rate_step'],
            }
    else:
        hyp['callbacks'] = []

    ## setup unit scheme
    if unit == 'si':
        hyp['unit'] = ['eV', 'eV/A']
    else:
        hyp['unit'] = ['Eh', 'Eh/Bohr']

    ## setup hypers
    hyp_dict = {
        'model': {
            'class_name': 'energy_grad',  # name of the class
            'class_module': 'scalar_grad',  # name of the model
            'config': {
                # Properties
                'states': info['nstate'],  # number of electronic states
                'node_info': None,  # a list of unique atom numbers
                'nedges': hyp['n_edges'],  # number of edges
                'edge_list': None,  # a list of pairwise atom indices in edges
                # NN architecture
                'maxradius': hyp['maxradius'],  # maximum atom-centered radius in Angstrom
                'n_features': hyp['n_features'],  # number of node features
                'n_blocks': hyp['n_blocks'],  # number of interaction blocks
                'l_max': hyp['l_max'],  # the largest rotation order
                'parity': hyp['parity'],  # use parity or not in o3 irreps
                # Radial net
                'n_rbf': hyp['n_rbf'],  # number of radial basis function
                'trainable_rbf': hyp['trainable_rbf'],  # trainable radial basis function
                'rbf_cutoff': hyp['rbf_cutoff'],  # rbf envelop function cutoff
                'rbf_layers': hyp['rbf_layer'],  # number of rbf layers
                'rbf_neurons': hyp['rbf_neurons'],  # number of rbf neuron per layer
                'rbf_act': hyp['rfb_act'],  # activation in rbf net
                'rbf_act_a': hyp['rfb_act_a'],  # parameter for leakysoftplus function
                'normalization_y': hyp['normalization_y'],  # normalization scheme in spherical harmonics
                'normalize_y': hyp['normalize_y'],  # normalize edge vectors when projecting to spherical harmonics
                # Convolution
                'resnet': hyp['resnet'],  # use resnet feature update
                'self_connection': hyp['self_connection'],  # compute self connection in feature convolution
                # Convolutional layer activation
                'gate': hyp['gate'],  # use gated activation or norm activation
                'act_scalars': {
                    'e': hyp['act_scalars_e'],
                    'o': hyp['act_scalars_o']
                },  # activation for scalars
                'act_gates': {
                    'e': hyp['act_gates_e'],
                    'o': hyp['act_gates_o']
                },  # activation for gated tensors
            },
        },
        'scaling': {
            'mean': 0,  # shifting factor for energy
            'std': 1,   # scaling factor for energy
        },
        'training': {
            'device': 'cpu',  # training device
            'val_split': 1 / splits,  # validation training set ratio
            'initialize_weights': hyp['initialize_weights'],  # initialize weight to retrain
            'loss_weights': hyp['loss_weights'],  # weight between scalar and grad loss
            'learning_rate': hyp['learning_rate'],  # learning rate
            'epo': hyp['epo'],  # number of epoch
            'subset': 0.1,  # ratio of train data used for training
            'batch_size': hyp['batch_size'],  # batch size
            'epo_step': hyp['epo_step'],  # steps of epochs for validation
            'callbacks': hyp['callbacks'],
            'use_reg_loss': hyp['use_reg_loss_dict'],
            'unit_scalar': hyp['unit'][0],  # unit of scalar
            'unit_grad': hyp['unit'][1],  # unit of grad
            'grad_type': hyp['grad_type'], # type of grad or force
        }
    }

    return hyp_dict

def set_e2n2_hyper_nac(hyp, unit, info, splits):
    """ Generating hyperparameter dict for soc NN

        Parameters:          Type:
            hyp              dict     hyperparameter input
            unit             str      unit scheme
            info             dict     training data information

        Return:              Type:
            hyp_ditc         dict     hyperparameter dict for NN

    """

    ## setup regularization dict
    penalty = 'use_reg_loss'
    penalty_key = '%s_dict' % penalty
    if hyp[penalty] == 'l1':
        hyp[penalty_key] = {'class_name': 'l1', 'config': {'l1': hyp['reg_l1']}}
    elif hyp[penalty] == 'l2':
        hyp[penalty_key] = {'class_name': 'l2', 'config': {'l2': hyp['reg_l2']}}
    elif hyp[penalty] == 'l1_l2':
        hyp[penalty_key] = {'class_name': 'l1_l2', 'config': {'l1': hyp['reg_l1'], 'l2': hyp['reg_l2']}}
    else:
        hyp[penalty_key] = None

    ## setup callbacks
    if hyp['use_step_callback']:
        hyp['callbacks'] = {
            'stepwise': True,
            'epoch_step_reduction': hyp['epoch_step_reduction'],
            'learning_rate_step': hyp['learning_rate_step'],
            }
    else:
        hyp['callbacks'] = []

    ## setup unit scheme
    if unit == 'si':
        hyp['unit'] = 'eV/A'
    else:
        hyp['unit'] = 'Eh/Bohr'

    ## setup hypers
    hyp_dict = {
        'model': {
            'class_name': 'nac',  # name of the class
            'class_module': 'grad',  # name of the model
            'config': {
                # Properties
                'states': info['nstate'],  # number of electronic states
                'node_info': None,  # a list of unique atom numbers
                'nedges': hyp['n_edges'],  # number of edges
                'edge_list': None,  # a list of pairwise atom indices in edges
                # NN architecture
                'maxradius': hyp['maxradius'],  # maximum atom-centered radius in Angstrom
                'n_features': hyp['n_features'],  # number of node features
                'n_blocks': hyp['n_blocks'],  # number of interaction blocks
                'l_max': hyp['l_max'],  # the largest rotation order
                'parity': hyp['parity'],  # use parity or not in o3 irreps
                # Radial net
                'n_rbf': hyp['n_rbf'],  # number of radial basis function
                'trainable_rbf': hyp['trainable_rbf'],  # trainable radial basis function
                'rbf_cutoff': hyp['rbf_cutoff'],  # rbf envelop function cutoff
                'rbf_layers': hyp['rbf_layer'],  # number of rbf layers
                'rbf_neurons': hyp['rbf_neurons'],  # number of rbf neuron per layer
                'rbf_act': hyp['rfb_act'],  # activation in rbf net
                'rbf_act_a': hyp['rfb_act_a'],  # parameter for leakysoftplus function
                'normalization_y': hyp['normalization_y'],  # normalization scheme in spherical harmonics
                'normalize_y': hyp['normalize_y'],  # normalize edge vectors when projecting to spherical harmonics
                # Convolution
                'resnet': hyp['resnet'],  # use resnet feature update
                'self_connection': hyp['self_connection'],  # compute self connection in feature convolution
                # Convolutional layer activation
                'gate': hyp['gate'],  # use gated activation or norm activation
                'act_scalars': {
                    'e': hyp['act_scalars_e'],
                    'o': hyp['act_scalars_o']
                },  # activation for scalars
                'act_gates': {
                    'e': hyp['act_gates_e'],
                    'o': hyp['act_gates_o']
                },  # activation for gated tensors
            },
        },
        'scaling': {
            'mean': 0,  # shifting factor for energy
            'std': 1,   # scaling factor for energy
        },
        'training': {
            'device': 'cpu',  # training device
            'val_split': 1 / splits,  # validation training set ratio
            'initialize_weights': hyp['initialize_weights'],  # initialize weight to retrain
            'loss_weights': hyp['loss_weights'],  # weight between scalar and grad loss
            'learning_rate': hyp['learning_rate'],  # learning rate
            'epo': hyp['epo'],  # number of epoch
            'subset': 0.1,  # ratio of train data used for training
            'batch_size': hyp['batch_size'],  # batch size
            'epo_step': hyp['epo_step'],  # steps of epochs for validation
            'callbacks': hyp['callbacks'],
            'use_reg_loss': hyp['use_reg_loss_dict'],
            'unit_scalar': '',  # unit of scalar
            'unit_grad': hyp['unit'],  # unit of grad
            'grad_type': hyp['grad_type'],  # type of grad or force
        }
    }

    return hyp_dict

def set_e2n2_hyper_soc(hyp, unit, info, splits):
    """ Generating hyperparameter dict for soc NN

        Parameters:          Type:
            hyp              dict     hyperparameter input
            unit             str      unit scheme
            info             dict     training data information

        Return:              Type:
            hyp_ditc         dict     hyperparameter dict for NN

    """

    ## setup regularization dict
    penalty = 'use_reg_loss'
    penalty_key = '%s_dict' % penalty
    if hyp[penalty] == 'l1':
        hyp[penalty_key] = {'class_name': 'l1', 'config': {'l1': hyp['reg_l1']}}
    elif hyp[penalty] == 'l2':
        hyp[penalty_key] = {'class_name': 'l2', 'config': {'l2': hyp['reg_l2']}}
    elif hyp[penalty] == 'l1_l2':
        hyp[penalty_key] = {'class_name': 'l1_l2', 'config': {'l1': hyp['reg_l1'], 'l2': hyp['reg_l2']}}
    else:
        hyp[penalty_key] = None

    ## setup callbacks
    if hyp['use_step_callback']:
        hyp['callbacks'] = {
            'stepwise': True,
            'epoch_step_reduction': hyp['epoch_step_reduction'],
            'learning_rate_step': hyp['learning_rate_step'],
            }
    else:
        hyp['callbacks'] = []

    ## setup unit scheme
    if unit == 'si':
        hyp['unit'] = 'cm-1'
    else:
        hyp['unit'] = 'cm-1'

    ## setup hypers
    hyp_dict = {
        'model': {
            'class_name': 'soc',  # name of the class
            'class_module': 'scalar',  # name of the model
            'config': {
                # Properties
                'states': info['nstate'],  # number of electronic states
                'node_info': None,  # a list of unique atom numbers
                'nedges': hyp['n_edges'],  # number of edges
                'edge_list': None,  # a list of pairwise atom indices in edges
                # NN architecture
                'maxradius': hyp['maxradius'],  # maximum atom-centered radius in Angstrom
                'n_features': hyp['n_features'],  # number of node features
                'n_blocks': hyp['n_blocks'],  # number of interaction blocks
                'l_max': hyp['l_max'],  # the largest rotation order
                'parity': hyp['parity'],  # use parity or not in o3 irreps
                # Radial net
                'n_rbf': hyp['n_rbf'],  # number of radial basis function
                'trainable_rbf': hyp['trainable_rbf'],  # trainable radial basis function
                'rbf_cutoff': hyp['rbf_cutoff'],  # rbf envelop function cutoff
                'rbf_layers': hyp['rbf_layer'],  # number of rbf layers
                'rbf_neurons': hyp['rbf_neurons'],  # number of rbf neuron per layer
                'rbf_act': hyp['rfb_act'],  # activation in rbf net
                'rbf_act_a': hyp['rfb_act_a'],  # parameter for leakysoftplus function
                'normalization_y': hyp['normalization_y'],  # normalization scheme in spherical harmonics
                'normalize_y': hyp['normalize_y'],  # normalize edge vectors when projecting to spherical harmonics
                # Convolution
                'resnet': hyp['resnet'],  # use resnet feature update
                'self_connection': hyp['self_connection'],  # compute self connection in feature convolution
                # Convolutional layer activation
                'gate': hyp['gate'],  # use gated activation or norm activation
                'act_scalars': {
                    'e': hyp['act_scalars_e'],
                    'o': hyp['act_scalars_o']
                },  # activation for scalars
                'act_gates': {
                    'e': hyp['act_gates_e'],
                    'o': hyp['act_gates_o']
                },  # activation for gated tensors
            },
        },
        'scaling': {
            'mean': 0,  # shifting factor for energy
            'std': 1,   # scaling factor for energy
        },
        'training': {
            'device': 'cpu',  # training device
            'val_split': 1 / splits,  # validation training set ratio
            'initialize_weights': hyp['initialize_weights'],  # initialize weight to retrain
            'loss_weights': hyp['loss_weights'],  # weight between scalar and grad loss
            'learning_rate': hyp['learning_rate'],  # learning rate
            'epo': hyp['epo'],  # number of epoch
            'subset': 0.1,  # ratio of train data used for training
            'batch_size': hyp['batch_size'],  # batch size
            'epo_step': hyp['epo_step'],  # steps of epochs for validation
            'callbacks': hyp['callbacks'],
            'use_reg_loss': hyp['use_reg_loss_dict'],
            'unit_scalar': hyp['unit'],  # unit of scalar
            'unit_grad': '',  # unit of grad
            'grad_type': hyp['grad_type'],  # type of grad or force
        }
    }

    return hyp_dict
