"""
Implementation of the VBAP method for panning a source in (almost) arbitrary
speaker setups.
"""
import numpy as np
from numpy.typing import ArrayLike
from typing import Union
from itertools import combinations
from scipy.spatial import ConvexHull


DEG_2_RAD = np.pi / 180

class VbapPanner:

    def __init__(self, ls_az : ArrayLike, ls_el : ArrayLike):
        self.ls_az = np.asarray(ls_az, dtype=float)
        self.ls_el = np.asarray(ls_el, dtype=float)
        self.ls_vec = ang_to_cart(self.ls_az, self.ls_el)
        self.triangles = ConvexHull(self.ls_vec.T).simplices

    def calc_gains(self, az: float, el: float, triplet_base: np.ndarray) -> np.ndarray:
        """
        Calculate gains for a given loudspeaker triplet to position a source at the 
        given azimuth and elevation.

        az: azimuth angle in degrees
        el: elevation angle in degrees
        triplet_base: 3x3 matrix containing the loudspeaker vectors in its columns (!)
        """
        if (b_shape := triplet_base.shape) != (3, 3):
            msg = f"Base for active triplet has to be 3D, but has shape {b_shape}"
            raise ValueError(msg)

        source_vec = ang_to_cart(az, el)
        gains = np.linalg.inv(triplet_base) @ source_vec

        return gains

    def find_active_triangle(self, az: float, el: float):
        """
        Find active triangle by looping over all possible triangles and choosing
        the triangle with all positive gains.
        """
        active_tri = np.asarray([-1, -1, -1])
        for tri in self.triangles:
            base = self.ls_vec[:, tri]
            gains = self.calc_gains(az, el, base)
            if (np.min(gains) > 0):
                active_tri = tri
                break

        return active_tri


def ang_to_cart(az : Union[float, np.ndarray] , el : Union[float, np.ndarray], unit: str ="DEG") -> np.ndarray:
    """
    Calculate three-dimensional unit vector for given azimuth and elevation angles
    """
    if unit == "DEG":
        az *= DEG_2_RAD
        el *= DEG_2_RAD
    elif unit != "RAD":
        raise ValueError(f"Unit has to be either 'DEG' or 'RAD', but is {unit}")

    x = np.cos(el) * np.cos(az)
    y = np.cos(el) * np.sin(az)
    z = np.sin(el)
    return np.asarray([x, y, z])


def _normalize_gains(gains, vol_norm):
    """
    Normalize gain factors to garantue power conservation.
    """
    return gains * np.sqrt(vol_norm / np.sum(gains ** 2))
