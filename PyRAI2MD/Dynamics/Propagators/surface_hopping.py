######################################################
#
# PyRAI2MD 2 module for computing surface hopping
#
# Author Jingbai Li
# Sep 7 2021
#
######################################################

import numpy as np
from PyRAI2MD.Dynamics.Propagators.fssh import FSSH
from PyRAI2MD.Dynamics.Propagators.gsh import gsh

def surfhop(traj):
    """ Computing surface hopping 

        Parameters:          Type:
            traj             class	 trajectory class

        Attribute:           Type:
            sfhp             str         surface hopping method

        Return:              Type:
            traj             class	 molecule class

    """

    sfhp = traj.sfhp
    if sfhp.lower() == 'fssh':
        traj_dict = {key: getattr(traj, key) for key in traj.attr}
        at, ht, dt, v, hoped, old_state, state, info = FSSH(traj_dict)

    elif sfhp.lower() == 'gsh':
        at, ht, dt, v, hoped, old_state, state, info = gsh(traj)

    elif sfhp.lower() == 'nosh':
        traj.shinfo = 'no surface hopping is performed'
        return traj

    else:
        traj.shinfo = 'no surface hopping is performed'
        return traj

    traj.a = np.copy(at)
    traj.h = np.copy(ht)
    traj.d = np.copy(dt)
    traj.velo = np.copy(v)
    traj.hoped = hoped
    traj.last_state = old_state
    traj.state = state
    traj.shinfo = info

    return traj
