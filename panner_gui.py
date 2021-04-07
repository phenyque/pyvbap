import tkinter as tk
from tkinter import filedialog
import numpy as np
from os.path import basename
from time import sleep
from threading import Thread
from vbap_player import VbapPlayer
from PIL import Image, ImageTk


RAD_2_DEG = 180 / np.pi
DEG_2_RAD = np.pi / 180
COORD_TEMPLATE = 'x: {:.1f}, y: {:.1f}\nangle: {:.0f}, r: {:.1f}\nx_r: {:.1f}, y_r: {:.1f}'
WIDTH = 600
HEIGHT = 600
R = 289

GUI_CONFIG = {
            'win_width': WIDTH,
            'win_height': HEIGHT,
            'spkr_radius': R,
            'control_height': 100,

            'line_colour_out': 'red',
            'line_colour_in': 'green',
    
            # dict containing graphic path and scaling size for all widgets
            'widgets': {
                    'ls': ['graphics/loudspeaker_small.png', None],
                    'ls_highlight': ['graphics/loudspeaker_small_highlight.png', None],
                    'bg': ['graphics/bg.png', (WIDTH, HEIGHT)],
                    'sound_active': ['graphics/sound_active.png', (50, 50)],
                    'sound_inactive': ['graphics/sound_inactive.png', (50, 50)],
                    'play': ['graphics/play_but.png', (50, 50)],
                    'stop': ['graphics/stop_but.png', (50, 50)],
                },

            'audio_bufsize': 1024,
            'error_duration': 3,
        }


def screen_to_polar(x, y, width, height):
    x_t = x - width // 2
    y_t = y - height // 2
    angle = (-np.arctan2(y_t, x_t) * RAD_2_DEG - 90) % 360
    radius = np.sqrt(x_t**2 + y_t**2)
    return angle, radius


def polar_to_screen(angle, radius, width, height):
    angle = angle * DEG_2_RAD
    x = -radius * np.sin(angle)
    y = radius * np.cos(angle)
    return x + width // 2, -y + height // 2

def convert_angle(angle):
    return int(angle - 360 if angle > 180 else angle)

class PannerGui():

    def __init__(self, ls_az):
        
        # set up player
        self.ls_az = ls_az
        ls_el = [0] * len(self.ls_az)
        self.player = VbapPlayer(ls_az, ls_el, bufsize=GUI_CONFIG["audio_bufsize"])

        self.file = None
        self.bounds = (-180, 180)

        # set up gui window
        self.root = tk.Tk()
        self.root.title('VBAP Panner')
        self.root.geometry('{}x{}'.format(GUI_CONFIG['win_width'],
                           GUI_CONFIG['win_height']+GUI_CONFIG['control_height']))
        self.root.resizable(width=False, height=False)
        self.root.config(background='white')
        self.root.protocol('WM_DELETE_WINDOW', self.on_closing)

        self.x_mid, self.y_mid = polar_to_screen(0, 0, GUI_CONFIG['win_width'],
                                                  GUI_CONFIG['win_height'])

        # load widgets
        self.widgets = dict()
        for widget in GUI_CONFIG['widgets']:
            path, resize = GUI_CONFIG['widgets'][widget]
            self.add_widget(path, widget, resize)

        # set window background
        self.bg = tk.Canvas(self.root, width=GUI_CONFIG['win_width'],
                            height=GUI_CONFIG['win_height'])
        self.bg.grid(row=0, column=0)
        self.bg.create_image(0, 0, anchor=tk.NW, image=self.widgets['bg'])

        # setup loudspeaker widgets
        self.ls_widgets = dict()
        self.ls_high = None
        self.draw_loudspeakers()

        # draw sound position indicator
        sound_pos_zero = polar_to_screen(0, R, GUI_CONFIG['win_width'],
                                          GUI_CONFIG['win_height'])
        self.sound_widget = self.bg.create_image(sound_pos_zero, anchor=tk.CENTER,
                                                 image=self.widgets['sound_active'])
        self.bg.itemconfigure(self.sound_widget, state=tk.HIDDEN)

        # command buttons
        self.play_but = tk.Button(self.root, image=self.widgets['play'],
                                  command=self.play_pause_callback)
        self.play_but.grid(row=1, column=0, sticky='w')
        # bind space bar to play button
        self.root.bind('<space>', lambda x: self.play_pause_callback())
        self.load_but = tk.Button(self.root, text='Load Sound File',
                                  command=self.load_callback)
        self.load_but.grid(row=1, column=0, sticky='e')
        # self.setup_but = tk.Button(self.root, text='Load Setup File',
                                   # command=self._setup_callback)
        # self.setup_but.grid(row=1, column=0, sticky='es')

        # error display
        self.error_display = tk.Label(self.root, text='', bg='white', fg='red')
        self.error_display.grid(row=1, column=0)

        # file name display
        self.file_display = tk.Label(self.root, text='', bg='white', fg='black')
        self.file_display.grid(row=1, column=0, sticky='n')

        # line to cursor position
        self.cursor_line = None
        self.angle_text = None

        # events on the top-down-view canvas
        self.bg.bind('<Motion>', self.mouse_move)
        self.bg.bind('<Button-1>', self.mouse_click)

        self.root.mainloop()


    def add_widget(self, path, name, resize=None):
        img = Image.open(path)
        if resize is not None:
            img = img.resize(resize)
        self.widgets[name] = ImageTk.PhotoImage(img)

    def on_closing(self):
        self.player.stop()
        self.root.destroy()

    def draw_loudspeakers(self):
        print("draw ls")
        for ang in self.ls_widgets:
            self.bg.delete(self.ls_widgets[ang])

        self.ls_widgets = dict()

        for ang in self.ls_az:
            x, y = polar_to_screen(ang,
                                    GUI_CONFIG['spkr_radius'], 
                                    GUI_CONFIG['win_width'],
                                    GUI_CONFIG['win_height'])
            print(ang, x, y)
            self.ls_widgets[ang] = self.bg.create_image(x, y, anchor=tk.CENTER,
                                                        image=self.widgets['ls'])

    def load_callback(self):
        f = filedialog.askopenfilename(filetypes=(('Wave audio files', '*.wav'),))
        if len(f) != 0:
            self.player.open_file(f)
            self.file = f
            self.file_display.configure(text='Open File: "{}"'.format(basename(f)))

    def play_pause_callback(self):
        if self.player.is_playing:
            self.play_but.configure(image=self.widgets['play'])
            self.player.stop()
            self.bg.itemconfigure(self.sound_widget, state=tk.HIDDEN)
        else:
            if self.file is None:
                msg = 'Open a file first!'
                err_thread = Thread(target=self.display_error_msg, args=(msg,))
                err_thread.start()
            else:
                self.play_but.configure(image=self.widgets['stop'])
                self.player.play()
                self.bg.itemconfigure(self.sound_widget, state=tk.NORMAL)


    def display_error_msg(self, msg):
        msg = 'Error: {}'.format(msg)
        self.error_display.configure(text=msg)
        sleep(GUI_CONFIG['error_duration'])
        self.error_display.configure(text='')

    def move_sound_widget(self, old_angle, new_angle):
        """
        Move the sound position widget to a new place and/or hide/unhide it.
        """
        x_curr, y_curr = polar_to_screen(old_angle, GUI_CONFIG['spkr_radius'],
                                          GUI_CONFIG['win_width'],
                                          GUI_CONFIG['win_height'])
        x_new, y_new = polar_to_screen(new_angle, GUI_CONFIG['spkr_radius'],
                                        GUI_CONFIG['win_width'],
                                        GUI_CONFIG['win_height'])
        print(x_curr, y_curr, x_new, y_new)
        x_rel = x_new - x_curr
        y_rel = y_new - y_curr
        self.bg.move(self.sound_widget, x_rel, y_rel)

    def mouse_click(self, event):
        x, y = event.x, event.y
        new_angle, _ = screen_to_polar(x,  y, GUI_CONFIG['win_width'],
                                        GUI_CONFIG['win_height'])
        if new_angle > 180:
            new_angle -= 360
        new_angle = max(min(int(new_angle), self.bounds[1]), self.bounds[0])

        print("new angle:", new_angle)
        self.move_sound_widget(self.player.az, new_angle)
        self.player.set_position(new_angle, 0)

    def mouse_move(self, event):
        x, y = event.x, event.y
        # compute angle in listener coordinates
        angle, radius = screen_to_polar(x,  y, GUI_CONFIG['win_width'],
                                         GUI_CONFIG['win_height'])
        conv_angle = convert_angle(angle)

        # check if angle is in allowed panning range
        if conv_angle < self.bounds[0] or conv_angle > self.bounds[1]:
            line_colour = GUI_CONFIG['line_colour_out']
        else:
            line_colour = GUI_CONFIG['line_colour_in']

        # draw red line with annotated angle
        if self.cursor_line is not None:
            self.bg.delete(self.cursor_line)
        if self.angle_text is not None:
            self.bg.delete(self.angle_text)
        x_r, y_r = polar_to_screen(angle, GUI_CONFIG['spkr_radius'],
                                    GUI_CONFIG['win_width'], GUI_CONFIG['win_width'])
        self.cursor_line = self.bg.create_line(self.x_mid, self.y_mid, x_r, y_r,
                                               fill=line_colour)
        x_text, y_text = polar_to_screen(angle + 10, GUI_CONFIG['spkr_radius'] / 3,
                                          GUI_CONFIG['win_width'], GUI_CONFIG['win_width'])

        # use converted angle for text display
        angle = conv_angle
        self.angle_text = self.bg.create_text(x_text, y_text, text='{}°'.format(angle),
                                              fill=line_colour)

        # if there is a speaker at the current angle, highlight that speaker
        if angle in self.ls_widgets.keys():
            self.bg.delete(self.ls_widgets[angle])
            x_spkr, y_spkr = polar_to_screen(angle, GUI_CONFIG['spkr_radius'],
                                              GUI_CONFIG['win_width'],
                                              GUI_CONFIG['win_height'])
            self.ls_widgets[angle] = self.bg.create_image(x_spkr, y_spkr, anchor=tk.CENTER,
                                                          image=self.widgets['ls_highlight'])
            self.ls_high = angle
        elif self.ls_high is not None:
            self.bg.delete(self.ls_widgets[self.ls_high])
            x_spkr, y_spkr = polar_to_screen(self.ls_high, GUI_CONFIG['spkr_radius'],
                                              GUI_CONFIG['win_width'], GUI_CONFIG['win_height'])
            self.ls_widgets[self.ls_high] = self.bg.create_image(x_spkr, y_spkr,
                                                                 anchor=tk.CENTER,
                                                                 image=self.widgets['ls'])
            self.ls_high = None


if __name__ == '__main__':
    ls_az = [30, -30, 110, -110]
    gui = PannerGui(ls_az)
