import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np

from player import VbapPlayer

WIDTH = 600
HEIGHT = 600
COORD_TEMPLATE = 'x: {:.1f}, y: {:.1f}\nangle: {:.0f}, r: {:.1f}\nx_r: {:.1f}, y_r: {:.1f}'

R = 289
RAD_2_DEG = 180 / np.pi
DEG_2_RAD = np.pi / 180

MAX_ANGLE = 30
MIN_ANGLE = -30


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


def resize_image(event):
    new_width = event.width
    new_height = event.height
    image = copy_of_image.resize((new_width, new_height))
    photo = ImageTk.PhotoImage(image)
    label.config(image=photo)
    label.image = photo


def cursor_pos(event):
    x, y = event.x, event.y
    # compute angle in listener coordinates
    angle, radius = _screen_to_polar(x,  y, WIDTH, HEIGHT)
    x_r, y_r = _polar_to_screen(angle, radius, WIDTH, HEIGHT)
    pos_text.set(COORD_TEMPLATE.format(x, y, angle, radius, x_r, y_r))


def _on_closing():
    player.stop()
    root.destroy()

# set up audio player
player = VbapPlayer('noise_pulsed.wav', 1000)
player.set_volume(0.1)

def slider_callback(angle):

    angle = int(angle)

    # move sound indicator image on the canvas
    x_curr, y_curr = _polar_to_screen(player.angle, R, WIDTH, HEIGHT)
    x_new, y_new = _polar_to_screen(angle, R, WIDTH, HEIGHT)
    x_rel = x_new - x_curr
    y_rel = y_new - y_curr

    window.move(sound_image_on_canvas, x_rel, y_rel)

    # set angle for panning
    player.set_angle(angle)

# build GUI
root = tk.Tk()
root.title('VBAP Panner')
root.geometry('{}x{}'.format(WIDTH, HEIGHT+50))
root.resizable(width=False, height=False)
root.config(background='white')
root.protocol('WM_DELETE_WINDOW', _on_closing)

window = tk.Canvas(root, width=WIDTH, height=HEIGHT)
window.grid(row=0, column=0)

# background image
bg_image = Image.open('graphics/bg.png')
bg_image = bg_image.resize((WIDTH, HEIGHT))
bg_photo = ImageTk.PhotoImage(bg_image)
window.create_image(0, 0, anchor=tk.NW, image=bg_photo)

# stereo loudspeakers
ls_image = Image.open('graphics/loudspeaker_small.png')
ls_photo = ImageTk.PhotoImage(ls_image)
ls_angles = [30, 330]

for angle in ls_angles:
    x, y = _polar_to_screen(angle, R, WIDTH, HEIGHT)
    window.create_image(x, y, anchor=tk.CENTER, image=ls_photo)

# sound direction indicator
sound_image = Image.open('graphics/note.png')
sound_image = sound_image.resize((50, 50))
sound_photo = ImageTk.PhotoImage(sound_image)
sound_image_on_canvas = window.create_image(_polar_to_screen(0, R, WIDTH, HEIGHT),
                    anchor=tk.CENTER, image=sound_photo)

# angle control
angle_slider = tk.Scale(root, from_=MIN_ANGLE,
                        to=MAX_ANGLE, orient=tk.HORIZONTAL,
                        command=slider_callback)
angle_slider.config(background='white')
angle_slider.grid(row=1, column=0)

"""
# set background image
bg_image = Image.open('graphics/bg.png')
bg_image = bg_image.resize((WIDTH, HEIGHT))
# copy_of_image = bg_image.copy()
bg_photo = ImageTk.PhotoImage(bg_image)

bg_label = tk.Label(root, image=bg_photo)
# bg_label.bind('<Configure>', resize_image)
bg_label.pack(fill=tk.BOTH, expand=tk.YES)

# add printing coordinates to screen
pos_text = tk.StringVar()
pos_text.set(COORD_TEMPLATE.format(0, 0, 0, 0, 0, 0))
coord_label = tk.Label(root, textvariable=pos_text)
coord_label.place(relx=0, rely=0, anchor=tk.NW)
root.bind('<Motion>', cursor_pos)

# place loudspeaker icons at +/- 30 deg

ls_image = Image.open('graphics/loudspeaker_small.png')
ls_photo = ImageTk.PhotoImage(ls_image)

label_30 = tk.Label(root, image=ls_photo)
x_30, y_30 = _polar_to_screen(30, R, WIDTH, HEIGHT)
label_30['bg'] = label_30.master['bg']
label_30.place(x=x_30, y=y_30, anchor=tk.CENTER)
"""

player.play()
root.mainloop()
