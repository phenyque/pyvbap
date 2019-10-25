# pyvbap

Vector base amplitude panning (VBAP) implemented in python. Implementation follows the one described in [1]. For now, only two-dimensional speaker setups are supported, i.e., no height.

### Contents
The algorithm is implemented as a package called `pyvbap` (duh!) that can be installed with `pip install .`(when in this directory). Additionally, there is the `example` folder, that contains a small example application that consist of a class `VbapPlayer` and GUI. The player class loops a given mono audio file and renders the panned signals for a given speaker setup based on the (for now only azimuth) panning angle. Angle can be changed during playback. The GUI visualizes the whole thing and offers panning by clicking.
There also is a helper script `spkr_setup.py` that offers a dialog for creating a json file for your custom speaker setup.

### References
[1]Pulkki, V.: _Virtual Sound Source Positioning Using Vector Base Amplitude Panning_. In: _Journal of the Audio Engineering Society_, Vol. 45 No. 6, 1997