"""
Implementation of the VBAP method for panning a source in (almost) arbitrary
speaker setups.
"""
import numpy as np
from numpy.typing import ArrayLike
from typing import Union, Optional
from itertools import combinations
from scipy.spatial import ConvexHull
from scipy.spatial.qhull import QhullError


DEG_2_RAD = np.pi / 180

class VbapPanner:

    def __init__(self, ls_az : ArrayLike, ls_el : Optional[ArrayLike] = None):

        self.ls_az = np.asarray(ls_az, dtype=float)
        if ls_el is None or np.all( (el_arr := np.asarray(ls_el, dtype=float) == 0) ):
            self.is_2d = True
            self.ls_el = np.zeros(self.ls_az.shape)
        else:
            self.is_2d = False
            self.ls_el = el_arr

        self.ls_vec = ang_to_cart(self.ls_az, self.ls_el, self.is_2d)

        try:
            self.triangles = ConvexHull(self.ls_vec.T).simplices
        except QhullError:
            raise CanNotConstructConvexHull("Error at complex hull construction. Your loudspeaker setup might be invalid!")

    def calc_gains(self, az: float, el: float, base: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Calculate gains for all loudspeakers to position a source at the 
        given azimuth and elevation. Inacitve triplets will have zero gain.

        az: azimuth angle in degrees
        el: elevation angle in degrees
        base: optional base amtrix to use for gain calculation, if given, only
              the active gains will be returned
        """
        if self.is_2d and el != 0:
            raise ValueError(f"Elevation has to be zero for 2-D case, but is {el}.")

        source_vec = ang_to_cart(az, el, self.is_2d)

        if base is None:
            act_idx = self.find_active_triangle(az, el)
            base = self.ls_vec[:, act_idx]
            gains = np.zeros(self.ls_vec.shape[1])
        else:
            gains = np.empty(len(source_vec))
            act_idx = np.arange(len(source_vec))

        if base.ndim > 1:
            act_gains = np.linalg.inv(base) @ source_vec
        else:
            act_gains = 1
        gains[act_idx] = act_gains

        return gains

    def find_active_triangle(self, az: float, el: float) -> ArrayLike:
        """
        Find active triangle by looping over all possible triangles and choosing
        the triangle with all positive gains.

        az: azimuth angle
        el: elevation angle

        returns: index of active loudspeakers in the stored setup, can be integer or numpy array
        """
        if self.is_2d and el != 0:
            raise ValueError(f"Elevation has to be zero for 2-D case, but is {el}.")

        # If given angles correspond to a loudspeaker position, directly reuturn
        # that index. Otherwise find active triangle/pair by calculating gains with
        # all possible triangles/pairs and choosing the one with all-positive gains
        try:
            active_tri = list(zip(self.ls_az, self.ls_el)).index((az, el))
        except ValueError:
            active_tri = np.asarray([-1, -1, -1])
            for tri in self.triangles:
                base = self.ls_vec[:, tri]
                gains = self.calc_gains(az, el, base)
                if (np.min(gains) > 0):
                    active_tri = tri
                    break

        return active_tri


def ang_to_cart(az : Union[float, np.ndarray] , el : Union[float, np.ndarray] = 0, is_2d: bool = False, unit: str ="DEG") -> np.ndarray:
    """
    Calculate unit vector for given azimuth and elevation angles.

    az: azimuth angle
    el: elevation angle
    is_2d: flag, if true, result is returned as 2-D vector
    unit: either "DEG" or "RAD", indicates how to interpret angle values
    """
    azi = np.asarray(az, dtype=float).copy()
    ele = np.asarray(el, dtype=float).copy()

    if unit == "DEG":
        azi *= DEG_2_RAD
        ele *= DEG_2_RAD
    elif unit != "RAD":
        raise ValueError(f"Unit has to be either 'DEG' or 'RAD', but is {unit}")

    x = np.cos(ele) * np.cos(azi)
    y = np.cos(ele) * np.sin(azi)

    if is_2d:
        result = np.asarray([x, y])
    else:
        z = np.sin(ele)
        result = np.asarray([x, y, z])

    return result


def _normalize_gains(gains, vol_norm):
    """
    Normalize gain factors to garantue power conservation.
    """
    return gains * np.sqrt(vol_norm / np.sum(gains ** 2))


class CanNotConstructConvexHull(Exception):
    pass
