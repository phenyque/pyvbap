import sounddevice as sd
import soundfile as sf
import numpy as np
from threading import Thread
import pyvbap

CHANNELS = 2

class VbapPlayer():
    """
    Audio player that continuously loops audio from a wav file and pans
    it to a given angle using vbap
    """

    def __init__(self, filename, bufsize):
        assert('.wav' in filename)
        self.bufsize = bufsize
        # TODO: channels have to be derived from a speaker setup
        self.channels = 2
        self._wf = sf.SoundFile(filename)
        assert(self._wf.channels == 1)
        self._stream = sd.Stream(channels=2, blocksize=bufsize,
                                 callback=self._audio_callback)
        self.is_playing = False
        self.volume = 1
        self.angle = 0
        self.bounds = [-30, 30]

        # hardcoded stereo speaker setup TODO: implement passing setups
        self.spkrs = [30, -30]
        self.bases = list()
        self._set_base_vectors(self.spkrs)

    def _set_base_vectors(self, spkr_angles):
        for a in spkr_angles:
            ang = pyvbap.DEG_2_RAD * a
            self.bases.append(pyvbap.comp_vec_for_angle(ang))
        self.bases = np.asarray(self.bases).T

    def _audio_callback(self, indata, outdata, frames, time, status):
        # get new samples from file and loop around at the end of the file
        buf = self._wf.read(self.bufsize)
        if (len(buf) < self.bufsize):
            self._wf.seek(0)
            buf = np.concatenate([buf, self._wf.read(self.bufsize - len(buf))])

        out = pyvbap.pan_2d(self.angle, buf, self.spkrs, self.bases)

        outdata[:] = out * self.volume

    def play(self):
        self.is_playing = True
        self._stream.start()

    def stop(self):
        self.is_playing = False
        self._stream.stop()

    def set_volume(self, vol):
        if vol < 0:
            print('Can not assign negative volume.')
        else:
            self.volume = vol

    def set_angle(self, ang):
        ang = np.clip(ang, self.bounds[0], self.bounds[1])
        self.angle = ang


if __name__ == '__main__':
    import time
    player = VbapPlayer('../noise_pulsed.wav', 1000)
    player.set_volume(0.1)
    player.play()
    time.sleep(1)
    player.set_angle(-30)
    print('angle: -30')
    time.sleep(1)
    player.set_angle(30)
    print('angle: 30')
    time.sleep(1)
    player.stop()
