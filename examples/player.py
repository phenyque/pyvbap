import pyaudio
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
        self.channels = 2
        self._wf = sf.SoundFile(filename)
        self._p = pyaudio.PyAudio()
        self._stream = self._p.open(
                format = pyaudio.paFloat32,
                channels = self.channels,
                rate = self._wf.samplerate,
                frames_per_buffer = self.bufsize,
                output = True)

        self._keep_playing = False
        self.volume = 1
        self.angle = 0
        self.bounds = [-30, 30]

        # hardcoded stereo speaker setup
        self.spkrs = [30, -30]
        self.bases = list()
        for a in self.spkrs:
            ang = pyvbap.DEG_2_RAD * a
            self.bases.append(pyvbap.comp_vec_for_angle(ang))
        self.bases = np.asarray(self.bases).T

        # get one initial frame
        self.get_next_frame()

    def get_next_frame(self):
        self._frame = self._wf.read(self.bufsize)
        if len(self._frame) != self.bufsize:
            self._wf.seek(0)
            self._frame = self._wf.read(self.bufsize)
        self._frame *= self.volume

    def _do_play(self):
        while self._keep_playing:
            # apply panning
            frame = self._frame.astype(np.float32)
            data = pyvbap.pan_2d(self.angle, frame, self.spkrs, self.bases)
            print(data[:10])
            interleaved = self._interleave_samples(data)
            print(interleaved[:20])
            self._stream.write(interleaved.tostring())
            self.get_next_frame()

    def _interleave_samples(self, data):
        print(data.shape[0])
        out = np.empty((data.shape[0] * self.channels), dtype=data.dtype)
        for i in range(self.channels):
            out[i::2] = data[:, i]
        return out

    def play(self):
        self._keep_playing = True
        thread = Thread(target=self._do_play)
        thread.start()

    def stop(self):
        self._keep_playing = False

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
