#!/usr/bin/env python3 
import click
from pyvbap import VbapPanner
import soundfile as sf
import numpy as np


@click.command()
@click.argument("infile", type=str)
@click.argument("outfile", type=str)
@click.argument("azimuth", type=int)
@click.argument("elevation", type=int)
def pan_to_file(infile, outfile, azimuth, elevation):

    # 5.0 setup:
    az = [30, 0, -30, 110, -110]
    el = [0] * len(az)
    panner = VbapPanner(az, el)
    gains = panner.calc_gains(azimuth, elevation)

    s, fs = sf.read(infile)
    out = s.reshape((-1, 1)) * gains
    sf.write(outfile, out, fs)


if __name__ == "__main__":
    pan_to_file()
