import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np
from threading import Thread
from time import sleep
from os.path import basename

from player import VbapPlayer

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

            'line_colour': 'red',
    
            # dict containing graphic path and scaling size for all widgets
            'widgets': {
                    'ls': ['graphics/loudspeaker_small.png', None],
                    'ls_highlight': ['graphics/loudspeaker_small_highlight.png', None],
                    'bg': ['graphics/bg.png', (WIDTH, HEIGHT)],
                    'sound': ['graphics/note.png', (30, 30)],
                    'play': ['graphics/play.png', (50, 50)],
                    'stop': ['graphics/stop.png', (50, 50)],
                },

            'audio_bufsize': 1024,
            'error_duration': 3,
        }


def _screen_to_polar(x, y, width, height):
    x_t = x - width // 2
    y_t = y - height // 2
    angle = (-np.arctan2(y_t, x_t) * RAD_2_DEG - 90) % 360
    radius = np.sqrt(x_t**2 + y_t**2)
    return angle, radius


def _polar_to_screen(angle, radius, width, height):
    angle = angle * DEG_2_RAD
    x = -radius * np.sin(angle)
    y = radius * np.cos(angle)
    return x + width // 2, -y + height // 2


class PannerGui():

    def __init__(self):
        # set up audio player
        self.player = VbapPlayer(setup_file='Stereo_test.json', bufsize=GUI_CONFIG['audio_bufsize'])
        self.player.set_volume(0.1)
        self.open_file = None

        # set up gui window
        self.root = tk.Tk()
        self.root.title('VBAP Panner')
        self.root.geometry('{}x{}'.format(GUI_CONFIG['win_width'], GUI_CONFIG['win_height']+GUI_CONFIG['control_height']))
        self.root.resizable(width=False, height=False)
        self.root.config(background='white')
        self.root.protocol('WM_DELETE_WINDOW', self._on_closing)

        self.x_mid, self.y_mid = _polar_to_screen(0, 0, GUI_CONFIG['win_width'], GUI_CONFIG['win_height'])

        # load widgets
        self._widgets = dict()
        for widget in GUI_CONFIG['widgets']:
            path, resize = GUI_CONFIG['widgets'][widget]
            self.add_widget(path, widget, resize)

        # set window background
        self.bg = tk.Canvas(self.root, width=GUI_CONFIG['win_width'], height=GUI_CONFIG['win_height'])
        self.bg.grid(row=0, column=0)
        self.bg.create_image(0, 0, anchor=tk.NW, image=self._widgets['bg'])

        # parse ls setup
        self.ls_pos = self.player.spkrs
        self.min_angle = self.player.bounds[0]
        self.max_angle = self.player.bounds[1]
        self.ls_widgets = dict()
        self.ls_high = None
        self._draw_loudspeakers()

        # draw sound position indicator
        sound_pos_zero = _polar_to_screen(0, R, GUI_CONFIG['win_width'], GUI_CONFIG['win_height'])
        self.sound_widget = self.bg.create_image(sound_pos_zero, anchor=tk.CENTER, image=self._widgets['sound'])

        # command buttons
        self.play_but = tk.Button(self.root, image=self._widgets['play'], command=self._play_pause_callback)
        self.play_but.grid(row=1, column=0, sticky='w')
        # bind space bar to play button
        space_bar_button_binding = lambda x: self._play_pause_callback()
        self.root.bind('<space>', space_bar_button_binding)
        self.load_but = tk.Button(self.root, text='Load File',
                                  command=self._load_callback)
        self.load_but.grid(row=1, column=0, sticky='e')

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
        self.bg.bind('<Motion>', self._mouse_move)
        self.bg.bind('<Button-1>', self._mouse_click)

        self.root.mainloop()


    def add_widget(self, path, name, resize=None):
        img = Image.open(path)
        if resize is not None:
            img = img.resize(resize)
        self._widgets[name] = ImageTk.PhotoImage(img)


    def _on_closing(self):
        self.player.stop()
        self.root.destroy()


    def _draw_loudspeakers(self):
        for angle in self.ls_pos:
            x, y = _polar_to_screen(angle,
                                    GUI_CONFIG['spkr_radius'], 
                                    GUI_CONFIG['win_width'],
                                    GUI_CONFIG['win_height'])
            self.ls_widgets[angle] = self.bg.create_image(x, y, anchor=tk.CENTER, image=self._widgets['ls'])


    def _load_callback(self):
        f = filedialog.askopenfilename(filetypes=(('Wave audio files', '*.wav'),))
        self.player.open_file(f)
        self.open_file = f
        self.file_display.configure(text='Open File: "{}"'.format(basename(f)))


    def _play_pause_callback(self):
        if self.player.is_playing:
            self.play_but.configure(image=self._widgets['play'])
            self.player.stop()
        else:
            if self.open_file is None:
                msg = 'Open a file first!'
                err_thread = Thread(target=self._display_error_msg, args=(msg,))
                err_thread.start()
            else:
                self.play_but.configure(image=self._widgets['stop'])
                self.player.play()


    def _display_error_msg(self, msg):
        msg = 'Error: {}'.format(msg)
        self.error_display.configure(text=msg)
        sleep(GUI_CONFIG['error_duration'])
        self.error_display.configure(text='')


    def _slider_callback(self, angle):
        angle = int(angle)

        # move sound indicator image on the canvas
        x_curr, y_curr = _polar_to_screen(self.player.angle, GUI_CONFIG['spkr_radius'], GUI_CONFIG['win_width'], GUI_CONFIG['win_height'])
        x_new, y_new = _polar_to_screen(angle, GUI_CONFIG['spkr_radius'], GUI_CONFIG['win_width'], GUI_CONFIG['win_height'])
        x_rel = x_new - x_curr
        y_rel = y_new - y_curr

        self.bg.move(self.sound_widget, x_rel, y_rel)

        # set angle for panning
        self.player.set_angle(angle)


    def _mouse_click(self, event):
        x, y = event.x, event.y
        angle, _ = _screen_to_polar(x,  y, GUI_CONFIG['win_width'], GUI_CONFIG['win_height'])
        if angle > 180:
            angle -= 360
        angle = max(min(int(angle), self.max_angle), self.min_angle)

        # move sound indicator image on the canvas
        x_curr, y_curr = _polar_to_screen(self.player.angle, GUI_CONFIG['spkr_radius'], GUI_CONFIG['win_width'], GUI_CONFIG['win_height'])
        x_new, y_new = _polar_to_screen(angle, GUI_CONFIG['spkr_radius'], GUI_CONFIG['win_width'], GUI_CONFIG['win_height'])
        x_rel = x_new - x_curr
        y_rel = y_new - y_curr
        self.bg.move(self.sound_widget, x_rel, y_rel)

        self.player.set_angle(angle)


    def _mouse_move(self, event):
        x, y = event.x, event.y
        # compute angle in listener coordinates
        angle, radius = _screen_to_polar(x,  y, GUI_CONFIG['win_width'], GUI_CONFIG['win_height'])

        # draw red line with annotated angle 
        if self.cursor_line is not None:
            self.bg.delete(self.cursor_line)
        if self.angle_text is not None:
            self.bg.delete(self.angle_text)
        x_r, y_r = _polar_to_screen(angle, GUI_CONFIG['spkr_radius'], GUI_CONFIG['win_width'], GUI_CONFIG['win_width'])
        self.cursor_line = self.bg.create_line(self.x_mid, self.y_mid, x_r, y_r, fill=GUI_CONFIG['line_colour'])
        x_text, y_text = _polar_to_screen(angle + 10, GUI_CONFIG['spkr_radius'] / 3, GUI_CONFIG['win_width'], GUI_CONFIG['win_width'])
        if angle > 180:
            angle -= 360
        angle = int(angle)
        self.angle_text = self.bg.create_text(x_text, y_text, text='{}°'.format(angle), fill=GUI_CONFIG['line_colour'])

        # if there is a speaker at the current angle, highlight that speaker
        if angle in self.ls_widgets.keys():
            self.bg.delete(self.ls_widgets[angle])
            x_spkr, y_spkr = _polar_to_screen(angle, GUI_CONFIG['spkr_radius'], GUI_CONFIG['win_width'], GUI_CONFIG['win_height'])
            self.ls_widgets[angle] = self.bg.create_image(x_spkr, y_spkr, anchor=tk.CENTER, image=self._widgets['ls_highlight'])
            self.ls_high = angle
        elif self.ls_high is not None:
            self.bg.delete(self.ls_widgets[self.ls_high])
            x_spkr, y_spkr = _polar_to_screen(self.ls_high, GUI_CONFIG['spkr_radius'], GUI_CONFIG['win_width'], GUI_CONFIG['win_height'])
            self.ls_widgets[self.ls_high] = self.bg.create_image(x_spkr, y_spkr, anchor=tk.CENTER, image=self._widgets['ls'])
            self.ls_high = None

        # set angle in player
        # angle = max(min(angle, self.max_angle), self.min_angle)
        # self.player.set_angle(angle)


gui = PannerGui()

# # set up audio player
# player = VbapPlayer('noise_pulsed.wav', 1000)
# player.set_volume(0.1)


# # build GUI
# root = tk.Tk()
# root.title('VBAP Panner')
# root.geometry('{}x{}'.format(GUI_CONFIG['win_width'], GUI_CONFIG['win_height']+50))
# root.resizable(width=False, height=False)
# root.config(background='white')
# root.protocol('WM_DELETE_WINDOW', _on_closing)

# window = tk.Canvas(root, width=GUI_CONFIG['win_width'], height=GUI_CONFIG['win_height'])
# window.grid(row=0, column=0)

# # background image
# bg_image = Image.open('graphics/bg.png')
# bg_image = bg_image.resize((GUI_CONFIG['win_width'], GUI_CONFIG['win_height']))
# bg_photo = ImageTk.PhotoImage(bg_image)
# window.create_image(0, 0, anchor=tk.NW, image=bg_photo)

# # stereo loudspeakers
# ls_angles = [30, -30]
# ls_image = Image.open(GUI_CONFIG['ls_image_path'])
# ls_photo = ImageTk.PhotoImage(ls_image)
# for angle in ls_angles:
    # x, y = _polar_to_screen(angle, GUI_CONFIG['spkr_radius'], GUI_CONFIG['win_width'], GUI_CONFIG['win_height'])
    # tmp = window.create_image(x, y, anchor=tk.CENTER, image=ls_photo)

# # sound direction indicator
# sound_image = Image.open('graphics/note.png')
# sound_image = sound_image.resize((50, 50))
# sound_photo = ImageTk.PhotoImage(sound_image)
# sound_image_on_canvas = window.create_image(_polar_to_screen(0, R, WIDTH, HEIGHT),
                    # anchor=tk.CENTER, image=sound_photo)

# # angle control
# angle_slider = tk.Scale(root, from_=MIN_ANGLE,
                        # to=MAX_ANGLE, orient=tk.HORIZONTAL,
                        # command=slider_callback)
# angle_slider.config(background='white')
# angle_slider.grid(row=1, column=0)

# """
# # set background image
# bg_image = Image.open('graphics/bg.png')
# bg_image = bg_image.resize((WIDTH, HEIGHT))
# # copy_of_image = bg_image.copy()
# bg_photo = ImageTk.PhotoImage(bg_image)

# bg_label = tk.Label(root, image=bg_photo)
# # bg_label.bind('<Configure>', resize_image)
# bg_label.pack(fill=tk.BOTH, expand=tk.YES)
# """

# # add printing coordinates to screen
# pos_text = tk.StringVar()
# pos_text.set(COORD_TEMPLATE.format(0, 0, 0, 0, 0, 0))
# coord_label = tk.Label(window, textvariable=pos_text)
# coord_label.place(relx=0, rely=0, anchor=tk.NW)
# window.bind('<Motion>', cursor_pos)

# """
# # place loudspeaker icons at +/- 30 deg

# ls_image = Image.open('graphics/loudspeaker_small.png')
# ls_photo = ImageTk.PhotoImage(ls_image)

# label_30 = tk.Label(root, image=ls_photo)
# x_30, y_30 = _polar_to_screen(30, R, WIDTH, HEIGHT)
# label_30['bg'] = label_30.master['bg']
# label_30.place(x=x_30, y=y_30, anchor=tk.CENTER)
# """

# player.play()
# root.mainloop()
