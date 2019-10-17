import numpy as np


DEG_2_RAD = np.pi / 180


def pan_2d(az, s, spkr_pos, base_vecs):
    """
    Pan the given signal to an azimuth angle in a 2d speaker setup

    az - integer azimuth panning angle
    s - signal as numpy array
    spkr_pos - sorted (!) list of the speaker angles
    base_vecs - unit vectors pointing to the speakers in same order as spkr_pos
    """
    # compute unit vector for given angle
    rad = az * DEG_2_RAD
    vec = np.asarray([-np.sin(rad), np.cos(rad)])

    # find active speakers and compute gains
    spkr_pos = np.asarray(spkr_pos)
    distance = np.abs(spkr_pos - az)
    pos_idx = np.arange(len(spkr_pos))
    active_idx = [x for _, x in sorted(zip(distance, pos_idx))][:2]
    if distance[active_idx[0]] == 0:
        active_idx = active_idx[:1]
        gains = np.asarray([1])
    else:
        inv = np.linalg.inv(base_vecs[:, active_idx])
        gains = _normalize_gains(inv @ vec, 1)

    ret = np.zeros((len(s), len(spkr_pos)))
    for i in range(len(active_idx)):
        tmp = s * gains[i]
        ret[:, active_idx[i]] = tmp
    return ret


def _normalize_gains(gains, vol_norm):
    """
    Normalize gain factors to garantue power conservation
    """
    return gains * np.sqrt(vol_norm / np.sum(gains ** 2))


def comp_vec_for_angle(ang):
    return np.asarray([-np.sin(ang), np.cos(ang)])
