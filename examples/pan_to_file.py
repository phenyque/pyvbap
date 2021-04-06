#!/usr/bin/env python3 
import click
from pyvbap import VbapPanner
from pyvbap import CanNotConstructConvexHull
import soundfile as sf
import numpy as np
import json
import os
import sys
import pprint


LS_FORMATS = {
        "5d0": {
                "az": [30, 0, -30, 110, -110],
                "el": [0,  0,   0,   0,    0]
            },
        "5d0+4": {
                "az": [30, 0, -30, 110, -110, 45, -45, 135, -135],
                "el": [ 0, 0,   0,   0,    0,  0,   0,   0,    0 ]
            }
        }


@click.command()
@click.argument("infile", type=click.File('rb'))
@click.argument("outfile", type=click.File('wb'))
@click.argument("ls_setup", type=str)
@click.option("--azimuth", type=int, default=0, help="Azimuth angle for panning")
@click.option("--elevation", type=int, default=0, help="Elevation angle for panning")
def pan_to_file(infile, outfile, azimuth, elevation, ls_setup, list_formats):
    """
    Pan a mono audio signal to a position (azimuth and elevation) in a loudspeaker setup using Vbap.
    """
    # get loudspeaker setup
    if ls_setup in LS_FORMATS.keys():
        ls_pos = LS_FORMATS[ls_setup]
    else:
        click.echo(f"Given loudspeaker setup '{ls_setup}' is not defined. You can add it in the 'LS_FORMATS' dict")
        sys.exit(1)

    panner = VbapPanner(ls_pos["az"], ls_pos["el"])
    gains = panner.calc_gains(azimuth, elevation)

    s, fs = sf.read(infile)
    out = s.reshape((-1, 1)) * gains
    sf.write(outfile, out, fs)


if __name__ == "__main__":
    pan_to_file()
