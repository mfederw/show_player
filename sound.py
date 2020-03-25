import os
import sys
import time
import signal
import pygame

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import RPi.GPIO as GPIO
import ST7789 as ST7789

image_file = "./Screen.png"
music_dir = "/home/pi/Music/"

class Display:
    def __init__(self):
        self.disp = ST7789.ST7789(
            port=0,
            cs=ST7789.BG_SPI_CS_FRONT,  # BG_SPI_CSB_BACK or BG_SPI_CS_FRONT
            dc=9,
            backlight=19,               # 18 for back BG slot, 19 for front BG slot.
            spi_speed_hz=80 * 1000 * 1000
        )

        self.width = self.disp.width
        self.height = self.disp.height

        # Initialize display.
        self.disp.begin()

        # Load an image.
        self.base_image = Image.open(image_file)

        self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        self.font2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 25)

    def update(self, a, b, c, d):
        image = self.base_image.resize((self.width, self.height))
        draw = ImageDraw.Draw(image)

        size_x, size_y = draw.textsize(a, self.font)
        text_x = (self.disp.width/2) - (size_x / 2)
        text_y = 30
        draw.text( (text_x, text_y), a, font=self.font, fill=(255, 255, 255))

        text_y += size_y
        size_x, size_y = draw.textsize(b, self.font2)
        text_x = (self.disp.width/2) - (size_x / 2)
        draw.text( (text_x, text_y), b, font=self.font2, fill=(255, 255, 255))

        text_y = 160
        size_x, size_y = draw.textsize(c, self.font)
        text_x = (self.disp.width/2) - (size_x / 2)
        draw.text( (text_x, text_y), c, font=self.font, fill=(255, 255, 255))

        text_y += size_y
        size_x, size_y = draw.textsize(d, self.font2)
        text_x = (self.disp.width/2) - (size_x / 2)
        draw.text( (text_x, text_y), d, font=self.font2, fill=(255, 255, 255))

        self.disp.display(image)

class Player:
    def __init__(self):
        self.playing = 0
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        pygame.mixer.music.set_volume(1.0)
        print("Initializing Player")
    def play(self, filename):
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        self.playing = 1
        #print("PLAY " + filename)
    def pause(self):
        #self.p.pause()
        print("Pause playing")
    def resume(self):
        #self.p.resume()
        print("resume playing")
    def stop(self):
        #self.p.stop()
        self.playing = 0
        print("Stop playing")
    def fade_out(self):
        if pygame.mixer.music.get_busy():
            #print("Fade out")
            pygame.mixer.music.fadeout(3000)

try:
    category = os.listdir(music_dir)
except:
    raise Exception("Music Directory Not Found: " + music_dir)
    
#print("Categories: ", category)
c = 0
songs = []

if len(category) == 0:
    print("No subdirectories in Music Directory: " + music_dir)
    sys.exit(1)

for dir in category:
    files = os.listdir(music_dir + category[c])
    #print("category: ", c, " ", files, "\n")
    songs.append([])
    if len(files) == 0:
        print("Directory: " + music_dir + dir + " should have at least one mp3 file")
        sys.exit(1)

    songs[c] = files
    c = c + 1

player = Player()

# Set up RPi.GPIO with the "BCM" numbering scheme
GPIO.setmode(GPIO.BCM)

song_playing = 255
playing_category = 0
next_song = 0
next_category = 0

def bump_next_category():
    global next_category
    global next_song
    next_category = next_category + 1
    if next_category == len(category):
        next_category = 0
    next_song = 0

def bump_next_song():
    global next_song
    next_song = next_song + 1
    num_songs = len(songs[next_category])
    if next_song == num_songs:
        next_song = 0

def song_name(fname):
    x = fname.split('.')
    return x[0]

dis = Display()

def show_display():
    c = ""
    ps = ""
    if song_playing != 255:
        ps = song_name(songs[playing_category][song_playing])
        c = category[playing_category]
    nxtsng = song_name(songs[next_category][next_song])
    dis.update(ps, c, nxtsng, category[next_category])

def button_A_callback(channel):
    # PLAY
    global song_playing
    global next_song
    global playing_category

    player.fade_out()
    song_playing = next_song
    playing_category = next_category
    player.play(music_dir + category[next_category] + "/" + songs[next_category][next_song])
    bump_next_song()
    show_display()

def button_B_callback(channel):
    # NEXT CATEGORY
    bump_next_category()
    show_display()

def button_X_callback(channel):
    # STOP
    global song_playing

    player.fade_out()
    song_playing = 255
    show_display()

def button_Y_callback(channel):
    # NEXT SONG
    bump_next_song()
    show_display()

def button_setup():
    BUTTONS = [5, 6, 16, 20]
    # Buttons connect to ground when pressed, so we should set them up
    # with a "PULL UP", which weakly pulls the input signal to 3.3V.
    GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # attach the callback function to each button
    GPIO.add_event_detect(5, GPIO.FALLING, button_A_callback, bouncetime=200)
    GPIO.add_event_detect(6, GPIO.FALLING, button_B_callback, bouncetime=200)
    GPIO.add_event_detect(16, GPIO.FALLING, button_X_callback, bouncetime=200)
    GPIO.add_event_detect(20, GPIO.FALLING, button_Y_callback, bouncetime=200)
    #GPIO.add_event_detect(24, GPIO.FALLING, button_Y_callback, bouncetime=200)

button_setup()
show_display()

# Finally, since button handlers don't require a "while True" loop,
# we pause the script to prevent it exiting immediately.
signal.pause()
