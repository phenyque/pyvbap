from pyvbap import VbapPanner
import soundfile as sf
import sounddevice as sd
import numpy as np

class VbapPlayer():

    def __init__(self, ls_az, ls_el, filename=None, bufsize=1024):

        self.az = 0
        self.el = 0
        self.is_playing = False
        self._sf = None

        self.filename = filename
        self.bufsize = bufsize

        self._panner = VbapPanner(ls_az, ls_el)
        self._stream = sd.OutputStream(channels=len(ls_az), callback=self._audio_callback, blocksize=self.bufsize)

        if self.filename is not None:
            self.open_file(filename)

    def __del__(self):
        if self._sf is not None:
            self._sf.close()
        if self.is_playing:
            self.stop()

    def open_file(self, filename):

        if self.is_playing:
            self.stop()

        if self._sf is not None:
            self._sf.close()
            self._sf = None

        tmp = sf.SoundFile(filename)

        if not tmp.channels == 1:
            raise ValueError(f"SoundFile has to be mono, but has {tmp.channels} channels.")

        self._sf = tmp

    def play(self):
        if self._sf is not None and not self.is_playing:
            self.is_playing = True
            self._stream.start()

    def stop(self):
        if self.is_playing:
            self.is_playing = False
            self._stream.stop()

    def _audio_callback(self, outdata, frames, time, status):
        buf = self._sf.read(self.bufsize)
        if len(buf) < self.bufsize:
            self._sf.seek(0)
            buf = np.concatenate([buf, self._sf.read(self.bufsize - len(buf))])

        gains = self._panner.calc_gains(self.az, self.el)
        out = buf.reshape((-1, 1)) * gains

        outdata[:] = out

    def set_position(self, azimuth, elevation):
        self.az = azimuth
        self.el = elevation


class CanNotOpenWavFile(Exception):
    pass
