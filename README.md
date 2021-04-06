# pyvbap

Vector base amplitude panning (VBAP) implemented in python. Implementation follows the one described in [1].

The algorithm is implemented in a class `VbapPanner` that can be directly imported from the package.
At object creation, pass the loudspeaker positions of your setup as azimuth and elevation angle lists and calculate panning gains like so:

```python
from pyvbap import VbapPanner

ls_az = [30, 0, -30, 110, 110]
ls_el = [0] * len(ls_az)
panner = VbapPanner(ls_az, ls_el)

pan_az = 15
pan_el = 0
gains = panner.calc_gains(pan_az, pan_el)
```

This way, the gains will be returned as a numpy array of the size of your loudspeaker setup. All inactive speakers will have zero gain, so by the virtue of numpy broadcasting panning a mono signal is simply:

```python
import numpy as np
noise = np.random.random((48000, 1)) # mono signal, of shape (48000, 1)
panned_noise = noise * gains         # panned signal has shape of ls setup, here (48000, 5)
```

## Note on loudspeaker formats

Note that only loudspeaker setups can be used for which the convex hull can be constructed (i.e. whos loudspeaker positions enclose an area (2D formats) or a volume (3D fromats)). If that's not the case, instantiation of the class will fail. Also, I have not tested any setups that allow for convex hull construction, but whos convex hull does not enclose the listener (mid point of the sphere). One example for this would be 2.0 stereo. Here, the panning should be limited to ±30°, but nothing like this is implemented right now and I only used the code with fully enclosing formats like 5.0. A list of possible loudspeaker setups for surround systems can be found at [2].

## Examples and scripts

Under ./examples, there are some example applications using VbapPanner.

### pan_to_file.py

Command line utility that reads a mono signal from a .wav file and pans it to a given position in a given loudspeaker format. Your own loudspeaker positions can be passed using a .toml file, there is an example file "5d0.toml" provided.

```
usage: pan_to_file.py [-h] [-i INFILE] [-o OUTFILE] [-s LS_SETUP] [-az AZIMUTH] [-el ELEVATION] [-l]

Pan mono audio signal to a given loudspeaker setup using Vbap

optional arguments:
  -h, --help            show this help message and exit
  -i INFILE, --infile INFILE
                        Input mono .wav file
  -o OUTFILE, --outfile OUTFILE
                        Output .wav file with panned mono signal
  -s LS_SETUP, --ls_setup LS_SETUP
                        Loudspeaker setup name, either path to .toml file or one of ['5d0', '5d0+4']
  -az AZIMUTH, --azimuth AZIMUTH
                        Azimuth angle for panning
  -el ELEVATION, --elevation ELEVATION
                        Elevation angle for panning
  -l, --list_setups     List available loudspeaker setups and exit
```

### vbap_player.py

Class that plays a mono audio signal in an infinite loop and lets you pan it in the given loudspeaker setup. Uses the `sounddevice` package for playing back audio. So far only tested on my ubuntu machine where it works pretty well. For playing around with it, best use it in an ipython session:

```python
from vbap_player import VbapPlayer
ls_az = [30, -30, 110, -110] # 'centerless' 5.0 setup, the first two speakers are the two speakers from 2.0 stereo
ls_el = [0] * len(ls_az)
filename = "white_noise.wav"
player = VbapPlayer(ls_az, ls_el, filename)

player.play() # starts playing asynchronously -> interpreter session goes on
player.set_position(30, 0) # repeat with different angles to move source
```

### References
[1]Pulkki, V.: _Virtual Sound Source Positioning Using Vector Base Amplitude Panning_. In: _Journal of the Audio Engineering Society_, Vol. 45 No. 6, 1997

[2] ITU: _Recommendation ITU-R BS.2051-2 Advanced sound system for programme production_. https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.2051-2-201807-I!!PDF-E.pdf
