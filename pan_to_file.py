#!/usr/bin/env python3
import argparse
from pyvbap import VbapPanner
import soundfile as sf
import sys
import pprint
import os
import toml


LS_FORMATS = {
    "5d0": {"azimuth": [30, 0, -30, 110, -110], "elevation": [0, 0, 0, 0, 0]},
    "5d0+4": {
        "azimuth": [30, 0, -30, 110, -110, 45, -45, 135, -135],
        "elevation": [0, 0, 0, 0, 0, 45, 45, 45, 45],
    },
}


def pan_to_file(
    infile: str, outfile: str, ls_pos: dict, azimuth: float, elevation: float
):
    """
    Pan a mono audio signal to a position (azimuth and elevation) in a loudspeaker setup using Vbap.
    """
    panner = VbapPanner(ls_pos["azimuth"], ls_pos["elevation"])
    gains = panner.calc_gains(azimuth, elevation)

    s, fs = sf.read(infile)
    out = s.reshape((-1, 1)) * gains
    sf.write(outfile, out, fs)


def load_setup_file(f: str) -> dict:
    """
    Parse a loudspeaker setup from a given toml file
    """
    try:
        setup = toml.load(f)
    except toml.TomlDecodeError as e:
        print("Error when loading ls setup from file:")
        print(e)
        raise CanNotLoadSetupFromFile()

    if (
        "positions" not in setup
        or "azimuth" not in setup["positions"]
        or "elevation" not in setup["positions"]
    ):
        print(
            "Setup file seems to be malformed, please refer to example file and documentation."
        )
        raise CanNotLoadSetupFromFile()

    return setup["positions"]


class CanNotLoadSetupFromFile(Exception):
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pan mono audio signal to a given loudspeaker setup using Vbap"
    )
    parser.add_argument(
        "-i", "--infile", type=str, default="", help="Input mono .wav file"
    )
    parser.add_argument(
        "-o",
        "--outfile",
        type=str,
        default="panned.wav",
        help="Output .wav file with panned mono signal",
    )

    ls_text = f"Loudspeaker setup name, either path to .toml file or one of {list(LS_FORMATS.keys())}"
    parser.add_argument("-s", "--ls_setup", type=str, default="", help=ls_text)

    parser.add_argument(
        "-az", "--azimuth", type=int, default=0, help="Azimuth angle for panning"
    )
    parser.add_argument(
        "-el", "--elevation", type=int, default=0, help="Elevation angle for panning"
    )

    parser.add_argument(
        "-l",
        "--list_setups",
        action="store_true",
        help="List available loudspeaker setups and exit",
    )

    args = parser.parse_args()

    if args.list_setups:
        print("Available loudspeaker setups with ls positions in degrees:")
        pprint.pprint(LS_FORMATS)
        sys.exit(0)

    infile, outfile, ls_setup = args.infile, args.outfile, args.ls_setup

    if infile == "":
        print("No input file given")
        sys.exit(1)

    # get loudspeaker setup
    if ls_setup in LS_FORMATS.keys():
        ls_pos = LS_FORMATS[ls_setup]
    elif os.path.isfile(ls_setup):
        try:
            ls_pos = load_setup_file(ls_setup)
        except CanNotLoadSetupFromFile:
            print("Could not load setup from file '{ls_setup}'")
            sys.exit(1)
    else:
        print(
            f"Given loudspeaker setup '{ls_setup}' is neither a file nor part of the pre-defined formats."
        )
        sys.exit(1)

    pan_to_file(infile, outfile, ls_pos, args.azimuth, args.elevation)
