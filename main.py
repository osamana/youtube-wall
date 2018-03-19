#!/usr/bin/python
# script by Alex Eames http://RasPi.tv  
# http://RasPi.tv/how-to-use-interrupts-with-python-on-the-raspberry-pi-and-rpi-gpio-part-3  
from __future__ import print_function

import RPi.GPIO as GPIO  
import time
import subprocess
import signal
import os
import errno
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  

debug = False

def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e: # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occurred

def detect_msg(state, pin):
	# state = [rising|falling], pin is an integer number
	if debug: print("- " + state + " edge detected on " + str(pin))  
	pass

	
 
lights = True

BTN_1 = 18
BTN_2 = 17
BTN_3 = 27
BTN_4 = 23
BTN_5 = 22
BTN_6 = 24

BUZZER_PIN = 20
RELAY_PIN = 21

BTN_BOUNCETIME = 100

FIFO_FILE_PATH = "/home/pi/Desktop/fifo"
# YOUTUBE_PLAYLIST_URL = "https://www.youtube.com/watch?v=OPf0YbXqDm0&list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj"
YOUTUBE_PLAYLIST_1_URL = "https://www.youtube.com/playlist?list=FLE9DGydzCtOabgaPsNH5bFw" # Favorites
YOUTUBE_PLAYLIST_2_URL = "https://www.youtube.com/playlist?list=PLifMAqbFQjxO6LyySU8oKNuxPHXyrvoc6" # Workout
YOUTUBE_PLAYLIST_3_URL = "https://www.youtube.com/playlist?list=PLWRJVI4Oj4IaYIWIpFlnRJ_v_fIaIl6Ey" # vivo's very best

ENABLE_VIDEO = False
ENABLE_SHUFFLE = True
LOG_FILE_PATH = "/home/pi/Desktop/log.txt"

# inputs
GPIO.setup(BTN_1, GPIO.IN)
GPIO.setup(BTN_2, GPIO.IN) 
GPIO.setup(BTN_3, GPIO.IN) 
GPIO.setup(BTN_4, GPIO.IN)
GPIO.setup(BTN_5, GPIO.IN)
GPIO.setup(BTN_6, GPIO.IN)

# outputs
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(RELAY_PIN, GPIO.OUT)

# initial state
GPIO.output(BUZZER_PIN, GPIO.LOW) # buzzer off
GPIO.output(BUZZER_PIN, GPIO.LOW) # lights on
# setup fifo file
# subprocess.Popen(["rm","-f", FIFO_FILE_PATH])
silentremove(FIFO_FILE_PATH)
subprocess.Popen(["mkfifo", FIFO_FILE_PATH])

# use this to store the process id of mpv
# mpv_process = None

# construct mpv command
def get_mpv_run_command(url):
	cmd = ""+\
	"nohup "+\
	"mpv "+\
	"\'"+ url +"\' " + \
	"--input-file=" + FIFO_FILE_PATH+ " "
	if not ENABLE_VIDEO:
		cmd += "--no-video "
	if ENABLE_SHUFFLE:
		cmd += "--shuffle "
	cmd += "> /dev/null 2>&1"
	cmd += " &"
	return cmd
	
print("Initialization Complete")


# control relay (lights)
def btn_4_cb(channel):  
	if GPIO.input(BTN_4):
		detect_msg("rising", BTN_4)
		global lights
		lights = not lights
		if lights:
			GPIO.output(RELAY_PIN, GPIO.LOW)
		else:
			GPIO.output(RELAY_PIN, GPIO.HIGH)
	else:
		detect_msg("falling" ,BTN_4)

# Playlist 1
# starts playing the music (starts MPV)
# if pressed again, MPV will exit
mpv_playing = False

MPV_QUIT_CMD = "echo \'quit\' >> " + FIFO_FILE_PATH

def exec_playlist(btn, playlist):
	global mpv_playing
	global mpv_process
	if GPIO.input(btn):
		detect_msg("rising", btn)
		if not mpv_playing:
			if debug: print("Running music...")
			# start mpv process
			# info: no need to store the process information anymore, i just send the quit comand using fifo
			run_comand = get_mpv_run_command(playlist)
			
			# todo: fix this, music stops after about 40 secs. maybe this has a timeout
			# mpv_process = subprocess.Popen(run_comand, shell=True, stdout=subprocess.PIPE, preexec_fn=os.setsid)
			if debug: print("# RUN CMD #")
			if debug: print(run_comand)
			status = subprocess.call(run_comand, shell=True) # returns immediately because we are using nohup
			if status == 0:
				mpv_playing = True
			else:
				if debug: print("subprocess.CalledProcessError: returned non-zero exit status 1")
		else:
			# old implementation
			# os.killpg(os.getpgid(mpv_process.pid), signal.SIGTERM)  # Send the signal to all the process groups
			# new way: just send the 'quit' comanad to mpv
			if debug: print("Quitting music.")
			subprocess.Popen(MPV_QUIT_CMD, shell=True)
			# mpv_process = None
			mpv_playing = False
	else:
		detect_msg("falling", btn)


def btn_1_cb(channel):
	exec_playlist(BTN_1, YOUTUBE_PLAYLIST_1_URL)
	

def btn_2_cb(channel):
	exec_playlist(BTN_2, YOUTUBE_PLAYLIST_2_URL)

	
def btn_3_cb(channel):
	exec_playlist(BTN_3, YOUTUBE_PLAYLIST_3_URL)


# shuffle (play next song in current playlist)
MPV_SHUFFLE_CMD = "echo \'playlist-next\' >> " + FIFO_FILE_PATH

def btn_6_cb(channel):
	if GPIO.input(BTN_6):
		detect_msg("rising", BTN_6)
		if mpv_playing:
			subprocess.Popen(MPV_SHUFFLE_CMD, shell=True)
		else:
			pass
			# print("Can't shuffle, MPV is not playing.")
	else:
		detect_msg("falling", BTN_6)

		
# pause/play control
MPV_CYCLE_PAUSE_CMD = "echo \'cycle pause\' >> " + FIFO_FILE_PATH

def btn_5_cb(channel):
	if GPIO.input(BTN_5):
		detect_msg("rising", BTN_5)
		if mpv_playing:
			# cycle pause
			subprocess.Popen(MPV_CYCLE_PAUSE_CMD, shell=True)
		else:
			pass
			# print("Can't pause/play, MPV is not playing.")
	else:
		detect_msg("falling", BTN_5)


# raw_input("Press Enter when ready\n>")  
   
GPIO.add_event_detect(BTN_1, GPIO.BOTH, callback=btn_1_cb, bouncetime=BTN_BOUNCETIME)  
GPIO.add_event_detect(BTN_2, GPIO.BOTH, callback=btn_2_cb, bouncetime=BTN_BOUNCETIME)
GPIO.add_event_detect(BTN_3, GPIO.BOTH, callback=btn_3_cb, bouncetime=BTN_BOUNCETIME)
GPIO.add_event_detect(BTN_4, GPIO.BOTH, callback=btn_4_cb, bouncetime=BTN_BOUNCETIME)
GPIO.add_event_detect(BTN_5, GPIO.BOTH, callback=btn_5_cb, bouncetime=BTN_BOUNCETIME)
GPIO.add_event_detect(BTN_6, GPIO.BOTH, callback=btn_6_cb, bouncetime=BTN_BOUNCETIME)

try:  
	while True:
		time.sleep(60)
except KeyboardInterrupt:  
	GPIO.cleanup()
	if mpv_process:
		os.killpg(os.getpgid(mpv_process.pid), signal.SIGTERM)  # Send the signal to all the process groups
	
GPIO.cleanup()           # clean up GPIO on normal exit  
if mpv_process:
		os.killpg(os.getpgid(mpv_process.pid), signal.SIGTERM)  # Send the signal to all the process groups
print("Leaving")
