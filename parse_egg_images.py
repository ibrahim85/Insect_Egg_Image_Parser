### functions_for_parser.py
### Created by Seth Donoughe in September 2016.
### Last updated June 2018.

# This work was a component of a project on the evolution of insect
# eggs. For more details, please see these two references:

# 	"Insect egg size and shape evolve with ecology, not developmental rate"
# 	Church, Donoughe, de Medeiros, Extavour; submitted 2018

# 	"A database of egg size and shape from more than 6,700 insect species"
# 	Church, Donoughe, de Medeiros, Extavour; submitted 2018

# This is a simple script for measuring images of eggs from sources
# that had been initially parsed by this tool:

# https://github.com/shchurch/Insect_Egg_Evolution

# It required two inputs: 1) a dictionary of parsed egg description entries,
# 2) a directory of single-page PNGs of the pages that contain the egg image
# for each entry.

# Key commands are used to switch between "modes" that correspond to the type
# of data that the script is collecting:

# 'b' - Box mode. User left-clicks on two opposing corners to define a box to crop.

# '8' - 8-point mode. For when the egg is oriented laterally.
# User left-clicks on the two poles of the egg, then on 6 additional points that
# correspond to the endpoints of the quartile-width-segments, as illustracted in
# the acticles listed above. Guidelines are drawn automatically, and the text
# notifications guide the user.

# '4' - 4-point mode. For when the egg is oriented with dorsal or ventral side up.
# Text prompts user to left-click poles and midline width.

# 's' - Scale bar mode. User is prompted to click both ends of the scale bar, then
# enter its length as text entry.

# User can right click to zoom in, and press '-' to zoom out.
# Press 'n' to save clicks and move on to additional text entry questions. This
# automatically leads to the next image. Press 'ESC' to quit.

import cv2
import numpy as np
import os.path
from numpy import arccos
from functions_for_parser import notify
import argparse
import pyperclip

# Get arguments from user
parser = argparse.ArgumentParser()
parser.add_argument('-o', '--overview_output_dir', help = 'path to directory where overview images will be saved')
parser.add_argument('-c','--cropped_output_dir', help = 'path to directory where cropped images will be saved')
parser.add_argument('-i','--input_image_dir', help = 'path to directory where single-page images are stored')
parser.add_argument('-d', '--dict_file', help = 'path to text file of single-entry dictionaries')
args = parser.parse_args()

# Hard code the maximum allowable height and width for an image in pixels
# Change these to suit your monitor / tastes
screen_max_w = 1400.0
screen_max_h = 800.0

# Colors for the document
color_pts = (0,255,0) 		# pure green
color_sb = (0,200,255) 		# orange
color_box = (130,0,230)		# magenta
color_guide = (255,50,50)	# royal blue

def draw_dot(x, y, im, text, color, size):
	# PURPOSE: Draws a dot and adjacent text onto an image

	# ARGUMENTS
	# x, y, : integers - Coordinates where the annotation should go
	# im : image array - The dots will be drawn here
	# text : string - The text to show with the dot
	# color : 3-element tuple - Stores an RGB color
	# size : integer - The approximate height of what the text label will be

	# RETURNS - nothing

	# Set constants for text and image display on images.
	# For text and dots, 'outline' is the thickness, in pixels, of the black outline
	text_size = size/10.0
	if text_size < 1:
		text_size = 1
	text_thickness = int(text_size)
	text_outline = 1+int(text_size*0.5)

	dot_radius = int(size*0.2)
	if dot_radius < 1:
		dot_radius = 1
	dot_outline = int(dot_radius*0.3)

	# Draw a slightly larger black circle in the background
	cv2.circle(img=im, center=(x,y), radius=dot_radius+dot_outline, color=(0,0,0), thickness=-1)
	# Draw the colored circle
	cv2.circle(img=im, center=(x,y), radius=dot_radius, color=color, thickness=-1)
	# Add slightly larger black text in the background
	cv2.putText(img=im, text=text, org=(x+text_thickness*5, y+text_thickness*6), color=(0,0,0), \
		fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=text_size, thickness=text_thickness+text_outline)
	# Add the colored text of interest
	cv2.putText(img=im, text=text, org=(x+text_thickness*5, y+text_thickness*6), color=color, \
		fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=text_size, thickness=text_thickness)

def calc_new_view(h_min, h_max, w_min, w_max, res_height, res_width, click_h, click_w):
	# PURPOSE
	# Takes mouse click coordinates and dimensions of an open image
	# and calculates the bounds of an updated, zoomed in view.

	# ARGUMENTS
	# h_min, h_max, w_min, w_max : integers
	#	The portion of the original image visible in existing window

	# res_height, res_width : integers
	#	The height and width of the existing image

	# click_h, click_w : integers
	#	The coordinates of the mouse-click in the existing window

	# im : array
	#	The original full-resolution image

	# RETURNS
	# new_h_min, new_h_max, new_w_min, new_w_max : integers
	#	The updated limits of the original image in the resized view

	# Define the default zoom factor
	zoom_scale = 1.3	

	# Convert the mouse click coordinates to the original dimensions
	orig_click_h = h_min + int((float(click_h)/res_height) * (h_max - h_min))
	orig_click_w = w_min + int((float(click_w)/res_width) * (w_max - w_min))

	# Define the limits of the new box
	# 	We rescale so that the new window width = (width of current window) / zoom_scale
	# 	This is measured in the pixels of the original image
	new_window_width = int((w_max - w_min) / zoom_scale)
	# 	Then we determine the corresponding height by filling the available screen
	new_window_height = int(screen_max_h * new_window_width / screen_max_w)

	# Now we determine the new limits of the scaled view
	# 	If the click coordinates are too close to the edge of the image, 
	# 	we want the limits to be translated toward the center so that 
	# 	the resized image isn't sampling from empty space.

	# Set the limits, defaulting to a centered view
	new_h_min = orig_click_h - new_window_height/2
	new_h_max = orig_click_h + new_window_height/2
	new_w_min = orig_click_w - new_window_width/2
	new_w_max = orig_click_w + new_window_width/2

	# If the coordinates exceed the bounds of the original image,
	# shift the window so that we only magnify existing pixels:
	if new_h_min < h_min:
		shift_h = abs(new_h_min - h_min)
		new_h_min += shift_h
		new_h_max += shift_h
	if new_h_max > h_max:
		shift_h = abs(h_max - new_h_max)
		new_h_min -= shift_h
		new_h_max -= shift_h
	if new_w_min < w_min:
		shift_w = abs(new_w_min - w_min)
		new_w_min += shift_w
		new_w_max += shift_w
	if new_w_max > w_max:
		shift_w = abs(w_max - new_w_max)
		new_w_min -= shift_w
		new_w_max -= shift_w

	return new_h_min, new_h_max, new_w_min, new_w_max

def make_new_view(h_min, h_max, w_min, w_max, im):
	# PURPOSE: Take new bounds to make an image that can be displayed
	# neatly within the max screen dimensions.

	# ARGUMENTS
	# h_min, h_max, w_min, w_max : integers
	#	The bounds of the image that should be displayed
	# im : 2D image array
	#	The original full-resolution image

	# RETURNS
	# im_res : 2D image array
	#	The cropped and resized image

	# Crop down to the desired section of the original image
	tmp_im = im[h_min:h_max, w_min:w_max]

	# Define base_factor, a float that is the scale factor needed to re-size
	# the image to fit within the specified max window dimensions. First
	# we define it to scale image to screen_max_w.
	resize_factor = screen_max_w / (w_max - w_min)

	# But if the resized window's height is too large, we re-calculate
	# the image scaling to match the screen_max_h:
	if (h_max - h_min) * resize_factor > screen_max_h:
		resize_factor = screen_max_h / (h_max - h_min)

	# Make a resized image
	im_res = cv2.resize(tmp_im, dsize=None, fx=resize_factor, fy=resize_factor)

	return im_res

def get_circle_center(pt1, pt2, pt3):
	# PURPOSE: Calculate the coordinates of the center and the radius
	# of the circle that is defined by three points.
	# Check algebra here: http://paulbourke.net/geometry/circlesphere/

	# ARGUMENTS
	# pt1, pt2, pt3 : 2-element tuples
	#	(x,y) coordinates in the window

	# RETURNS
	# If the three points are not collinear:
	# 	(x_center, y_center) : 2-element tuple - (x,y) center of the circle
	#	radius : float - length of the radius
	# If the three points are collinear, returns two strings: 'DNE', 'DNE'

	# Check whether the three points from a collinear vertical line
	if pt1[0] == pt2[0] and pt1[0] == pt3[0]:
		return 'DNE', 'DNE'

	# Make sure that neither of the two selected line segments is vertical
	if pt1[0] == pt2[0]:
		x1, y1 = pt2
		x2, y2 = pt3
		x3, y3 = pt1
	elif pt2[0] == pt3[0]:
		x1, y1 = pt3
		x2, y2 = pt1
		x3, y3 = pt2
	else:
		x1, y1 = pt1
		x2, y2 = pt2
		x3, y3 = pt3

	# Calculate the slope of the line connecting pt1 and pt2
	slope_a = (y2-y1)/(x2-float(x1))
	# Calculate the slope of the line connecting pt2 and pt3
	slope_b = (y3-y2)/(x3-float(x2))

	if slope_a == slope_b:
		return 'DNE', 'DNE' 

	x_center = (slope_a*slope_b*(y1-y3)+slope_b*(x1+x2)-slope_a*(x2+x3))/(2*(slope_b-slope_a))
	y_center = (-1/slope_a)*(x_center-(x1+x2)/2.0)+(y1+y2)/2.0
	radius = distance((x_center, y_center),pt1)

	return (x_center, y_center), radius

def distance(pt1, pt2):
	# PURPOSE: calculate distance between two points in a plane.
	# ARGUMENTS:
	# pt1, pt2 : 2-element tuples
	#	(x,y) coordinates in the window
	# RETURNS: the Euclidean distance between the points as a float.
	return ((pt2[0]-pt1[0])**2 + (pt2[1]-pt1[1])**2)**0.5

def midpoint(pt1, pt2):
	# PURPOSE: calculate midpoint of two points
	# ARGUMENTS:
	# pt1, pt2 : 2-element tuples
	#	(x,y) coordinates in the window
	# RETURNS: A 2-element tuple for the coordinates of the midpoint.
	# A non-integer coordinate is rounded down.
	mid_x = (pt1[0]+pt2[0])/2
	mid_y = (pt1[1]+pt2[1])/2
	return (mid_x, mid_y)

def calc_bisector_ends(pt1, pt2):
	# PURPOSE: Take two points and rotate them 90 degrees about
	# their midpoint, and extend them away from midpoint by a 
	# factor of 'factor'.

	# Controls how long the guide line is, as a factor of egg length
	factor = 4

	# The midpoint of the line segment connecting pt1 and pt2:
	mid_x, mid_y = midpoint(pt1, pt2)

	# The bisector should be perpendicular to the connecting segment
	# Rotate each endpoint around the line's midpoint.
	pt1_rot = (mid_x-pt1[1]+mid_y, mid_y+pt1[0]-mid_x)
	pt2_rot = (mid_x-pt2[1]+mid_y, mid_y+pt2[0]-mid_x)

	# Extend endpoint 1
	d_pt1_x = pt1_rot[0]-mid_x
	d_pt1_y = pt1_rot[1]-mid_y
	pt1_ext = (mid_x+factor*d_pt1_x, mid_y+factor*d_pt1_y)

	# Extend endpoint 2
	d_pt2_x = pt2_rot[0]-mid_x
	d_pt2_y = pt2_rot[1]-mid_y
	pt2_ext = (mid_x+factor*d_pt2_x, mid_y+factor*d_pt2_y)

	return pt1_ext, pt2_ext

def annotate_image(event,x,y,flags,param):
	# This is a mouse callback function: it executes when a mouse event takes place

	# It always has this specific format. It is based these tutorials:
	# http://docs.opencv.org/3.0-rc1/db/d5b/tutorial_py_mouse_handling.html
	# http://opencv24-python-tutorials.readthedocs.io/en/stable/py_tutorials/py_gui/py_mouse_handling/py_mouse_handling.html

	# ARGUMENTS
	# 	event : a cv2 mouse event, e.g. the left mouse button going up:
	# 		cv2.EVENT_LBUTTONUP
	# 	x,y : integers - the coordinates of the mouse at the time of the event
	#	flags, param : additional mouse callback parameters that we don't use

	# RETURNS: nothing

	global cx,cy,px,py,mode,points,sb_ends,h_min,h_max,w_min,w_max,res_h,res_w,image_data


	# When the left mouse button is released ...
	if event == cv2.EVENT_LBUTTONUP:
		# Convert the mouse click coordinates to the original dimensions
		raw_h = h_min + int((float(y)/res_h) * (h_max - h_min))
		raw_w = w_min + int((float(x)/res_w) * (w_max - w_min))

		# Determine the size of dots and text
		window_width = w_max-w_min	# Pixels displayed across width of current window
		dot_text_size_px = window_width/50

		if mode == 'box':
			# Click on opposite corners of the drawing / micrograph
			if px != -1:
				# Convert the mouse click coordinates to the original dimensions
				raw_box_h1 = h_min + int((float(y)/res_h) * (h_max - h_min))
				raw_box_w1 = w_min + int((float(x)/res_w) * (w_max - w_min))
				raw_box_h2 = h_min + int((float(py)/res_h) * (h_max - h_min))
				raw_box_w2 = w_min + int((float(px)/res_w) * (w_max - w_min))
				# Draw rectangle on original image
				cv2.rectangle(img=img, pt1=(raw_box_w1,raw_box_h1), \
					pt2=(raw_box_w2,raw_box_h2), color=color_box, thickness=5)
				# Store these locations in the dictionary
				if raw_box_h1 < raw_box_h2:
					image_data['im_box_h1'] = raw_box_h1
					image_data['im_box_h2'] = raw_box_h2
				else:
					image_data['im_box_h1'] = raw_box_h2
					image_data['im_box_h2'] = raw_box_h1
				if raw_box_w1 < raw_box_w2:
					image_data['im_box_w1'] = raw_box_w1
					image_data['im_box_w2'] = raw_box_w2
				else:
					image_data['im_box_w1'] = raw_box_w2
					image_data['im_box_w2'] = raw_box_w1

		elif mode == '8points' or mode == '4points':
			# Here we take either 4 of 8 mouse clicks to broadly define the shape of the egg
			if points == 1:
				notify('Points mode: click 2', 'Click on other end of egg', '')
				# Draw dot on the original image
				draw_dot(raw_w, raw_h, img, 'L1', color_pts, dot_text_size_px)
				# Store this location in the dictionary
				image_data['im_p_length_1'] = (raw_w, raw_h)
				points += 1 	# Increment to move to next step

			elif points == 2:
				notify('Points mode: click 3', 'Click where bisector meets edge of egg', '')
				# Draw dot on the original image
				draw_dot(raw_w, raw_h, img, 'L2', color_pts, dot_text_size_px)
				# Store this location in the dictionary
				image_data['im_p_length_2'] = (raw_w, raw_h)
				# Draw line to connect length points
				cv2.line(img, (raw_w, raw_h), image_data['im_p_length_1'], color=color_box, thickness=3)
				# Get endpoints for the mid-line bisector: m1 and m2
				m1, m2 = calc_bisector_ends((raw_w, raw_h), image_data['im_p_length_1'])
				# Draw line mid-line bisector line
				cv2.line(img, m1, m2, color=color_guide, thickness=3)
				points += 1 	# Increment to move to next step

			elif points == 3:
				notify('Points mode: click 4', 'Click where bisector meets opposite edge', '')
				# Draw dot on the original image
				draw_dot(raw_w, raw_h, img, 'M1', color_pts, dot_text_size_px)
				# Store this location in the dictionary
				image_data['im_p_midpoint_1'] = (raw_w, raw_h)
				points += 1 	# Increment to move to next step

			elif points == 4:
				# Draw dot on the original image
				draw_dot(raw_w, raw_h, img, 'M2', color_pts, dot_text_size_px)
				# Store this location in the dictionary
				image_data['im_p_midpoint_2'] = (raw_w, raw_h)
				points += 1 	# Increment to move to next step

				if mode == '8points':
					notify('Points mode: click 5', 'Click where quartile line meets edge', '')
					# Calculate egg's middle
					egg_middle = midpoint((raw_w, raw_h), image_data['im_p_midpoint_1'])
					image_data['im_p_egg_middle'] = egg_middle

					# Find center and radius of center defined by the points at
					# each of the ends at and egg_middle.
					circle_center, radius = get_circle_center(egg_middle, \
						image_data['im_p_length_1'], image_data['im_p_length_2'])
					image_data['im_p_circle_center'] = circle_center
					image_data['im_radius_px'] = radius

					# Draw dot at the egg's middle
					draw_dot(egg_middle[0], egg_middle[1], img, 'M', color_box, dot_text_size_px)

					# Draw a line segment from the egg's middle to each tip
					cv2.line(img, egg_middle, image_data['im_p_length_1'], color=color_guide, thickness=3)
					cv2.line(img, egg_middle, image_data['im_p_length_2'], color=color_guide, thickness=3)
					# Draw a perpendicular line segment at one quartile
					q1a, q1b = calc_bisector_ends(egg_middle, image_data['im_p_length_1'])
					cv2.line(img, q1a, q1b, color=color_guide, thickness=3)

			elif points == 5 and mode == '8points':
				notify('Points mode: click 6', 'Click where line meets opposite edge', '')
				# Draw dot on the original image
				draw_dot(raw_w, raw_h, img, '1Q1', color_pts, dot_text_size_px)
				# Store this location in the dictionary
				image_data['im_p_1st_quart_1'] = (raw_w, raw_h)
				points += 1 	# Increment to move to next step

			elif points == 6 and mode == '8points':
				notify('Points mode: click 7', 'Click where quartile line meets edge', '')
				# Draw dot on the original image
				draw_dot(raw_w, raw_h, img, '1Q2', color_pts, dot_text_size_px)
				# Store this location in the dictionary
				image_data['im_p_1st_quart_2'] = (raw_w, raw_h)
				# Draw a perpendicular line segment at the other quartile
				q3a, q3b = calc_bisector_ends(image_data['im_p_egg_middle'], image_data['im_p_length_2'])
				cv2.line(img, q3a, q3b, color=color_guide, thickness=3)

				points += 1 	# Increment to move to next step

			elif points == 7 and mode == '8points':
				notify('Points mode: click 8', 'Click where line meets opposite edge', '')
				# Draw dot on the original image
				draw_dot(raw_w, raw_h, img, '3Q1', color_pts, dot_text_size_px)
				# Store this location in the dictionary
				image_data['im_p_3rd_quart_1'] = (raw_w, raw_h)
				points += 1 	# Increment to move to next step

			elif points == 8 and mode == '8points':
				notify('All outline points collected!', '', '')
				# Draw dot on the original image
				draw_dot(raw_w, raw_h, img, '3Q2', color_pts, dot_text_size_px)
				# Store this location in the dictionary
				image_data['im_p_3rd_quart_2'] = (raw_w, raw_h)
				points += 1 	# Increment to move to next step

		elif mode == 'scale_bar':
			if sb_ends == 1:
				notify('Click other end of scale bar', '', '')
				# Draw dot on the original image
				draw_dot(raw_w, raw_h, img, 'S1', color_sb, dot_text_size_px)
				# Store these locations in the dictionary
				image_data['im_p_scale_bar_1'] = (raw_w, raw_h)
				sb_ends += 1 	# Increment to move to next step
			elif sb_ends == 2:
				notify('Both scale bar ends recorded', '', '')
				# Draw dot on the original image
				draw_dot(raw_w, raw_h, img, 'S2', color_sb, dot_text_size_px)
				# Store these locations in the dictionary
				image_data['im_p_scale_bar_2'] = (raw_w, raw_h)

		# Store mouse coordinates at last click
		px,py = x,y

	# When the right mouse button is released ...
	elif event == cv2.EVENT_RBUTTONUP:
		# Right click somewhere to indicate where you'd like to zoom.
		# Store mouse coordinates
		cx, cy = x, y
		mode = 'zoom_in'

def process_one_image(img_path, cropped_out_path, overview_out_path):
	# PURPOSE: Opens an image, gets info from the user in the form of
	# mouseclicks and keystrokes, and then saves this to a dictionary of
	# other info for that entry. Also saves two new images: 1) A high res
	# cropped image of just the egg. 2) An "overview" image that shows the full
	# PDF page with all the mouse clicks. This a lower-res image just for our
	# reference.

	# ARGUMENTS:
	# img_path : string - Path to the PNG/TIF/JPEG made from a PDF page
	# cropped_out_path : string - directory to store cropped egg images
	# overview_out_path : string - directory to store whole-page overviews

	# RETURNS:
	# image_data : dictionary - It contains all the morphological parameters.

	# GLOBAL VARIABLES:
	# These need to be global because the mouse callback function (annotate_image)
	# runs many times sequentially and refers to variables defined in previous iterations.
	# These will be continuously updated by keystrokes and mouse clicks.
	# 	cx, cy : integers - current x and y coordinates (set by mouse callback function)
	# 	px, py : integers - previous x and y coordinates (set by mouse callback function)
	# 	mode : string - determines what user input will be collected
	#	points : integer - counter for number of clicks recorded for egg outline
	#	sb_ends : integer - counter for number of scalebar ends so far recorded
	#	h_min, h_max, w_min, w_max : integers - the min and max coordinates
	#		of the image that are visible in the open window
	#	res_h, res_w : the resolution of the portion of the image that is visible
	global cx,cy,px,py,mode,points,sb_ends,h_min,h_max,w_min,w_max,res_h,res_w,image_data

	# Attempt to open image, and quit if image can't be opened
	image_data = {}		# Dict to hold measurements
	if os.path.isfile(img_path) and img_path[-4:].lower() == '.png':
		global img
		img = cv2.imread(img_path)
	else:
		print '##### Image not found or wrong file type #####\n'
		mode = 'next'
		image_data['im_status'] = 'missing'
		return image_data

	img_h, img_w = img.shape[:2] 	# Get original image height and width

	# Here we initialize most of them to their defaults:
	px,py = -1, -1		# integers: the x and y coords of previous click
	mode = 'box'		# string: sets mode for taking user input
	points = 1			# integer: counter for next egg outline point needed
	sb_ends = 1			# integer: counter for next scale bar endpoint needed
	h_min, w_min, h_max, w_max = 0, 0, img_h, img_w		# Define visible image limits
	res_h, res_w = img_h, img_w							# Set initial image resolution

	# TWO NESTED WHILE LOOPS
	# 	The outer loop makes a image window (zoomed in or out) when requested
	# 	and then restarts the setMouseCallback.
	# 		The inner loop gets clicks and keystrokes from the user
	# 		for the window that is currently open.
	while(1):
		cv2.namedWindow('image')	# Initialize a window for the image
		# setMouseCallback initializes a mouse handler for a specified window
		# 	NOTE: Mouse callback function will continue to run
		# 	until the callback window is destroyed.
		cv2.setMouseCallback('image',annotate_image)
		while(1):
			# Resize the image and get its dimensions
			im_res = make_new_view(h_min, h_max, w_min, w_max, img)
			res_h, res_w = im_res.shape[:2]
			# Display the image
			cv2.imshow('image',im_res)

			# Right mouse click in window switches mode to 'zoom_in'.
			# View is updated zoomed where there user clicks.
			if mode == 'zoom_in':
				break
			# Key strokes switch to other modes
			k = cv2.waitKey(1)
			if k==27:    # Esc key to quit
				mode = 'quit'
				break
			if k== ord('n'):    # 'n' key to move to next entry
				mode = 'next'
				break
			elif k == 45:	# '-' key zooms out image
				mode = 'zoom_out'
				break
			elif k == 127:	# Delete key resets image
				mode = 'reset'
				notify('All measurements cleared', '', '')
				break
			elif k == ord('b'):	# Box mode for getting image dimensions
				mode = 'box'
				notify('Box mode', 'Click opposite diagonal corners', '')
			elif k == ord('8'): # Get points to define egg outline
				mode = '8points'
				points = 1
				notify('Points mode: click 1', 'Click on one end of the egg', \
					'Any previous points will be overwritten')
			elif k == ord('4'): # Get points to define egg outline
				mode = '4points'
				points = 1
				notify('Points mode: click 1', 'Click on one end of the egg', \
					'Any previous points will be overwritten')
			elif k == ord('s'): # Get two points for scale bar
				mode = 'scale_bar'
				notify('Click one end of scale bar', '', '')
		if mode == 'quit' or mode == 'next':
			break
		elif mode == 'zoom_in':
			cv2.destroyAllWindows()
			# Calculate dimensions of a new, zoomed in image
			h_min, h_max, w_min, w_max = calc_new_view(h_min, h_max, w_min, w_max, res_h, res_w, cy, cx)
			px,py = -1, -1
			mode = 'box'
		elif mode == 'zoom_out':
			cv2.destroyAllWindows()
			# Make a new image with original scaling
			h_min, h_max, w_min, w_max = 0, img_h, 0, img_w
			px,py = -1, -1
			mode = 'box'
		elif mode == 'reset':
			cv2.destroyAllWindows()
			# Reload the original image and remove all annotations
			img = cv2.imread(img_path)
			# Reset global variables
			h_min, h_max, w_min, w_max = 0, img_h, 0, img_w
			px,py = -1, -1
			mode = 'box'
			points = 1
			image_data = {}		# Clear the dictionary

	if 'im_box_h1' in image_data:
		image_data['im_status'] = 'box'

	# CALCULATE SCALING
	# Get scalebar length from the user
	if 'im_p_scale_bar_1' in image_data:
		if 'im_p_scale_bar_2' in image_data:
			# If both ends of the scale bar have been recorded, then
			# get user input for the reported scale bar length.
			notify('Enter reported scale bar length', '', '')
			while(True):
				print 'What are the units of the scale bar?'
				units = raw_input("Type 'u' for microns and 'm' for millimeters: ")
				if units == 'u' or units == 'm':
					break
				else:
					print "Enter either 'u' or 'm' to continue"
			reported_sb_length = float(input('How long is the scale bar in '+str(units)+'m? '))
			if units == 'u':
				adjusted_sb_length = reported_sb_length / 1000.0 	# Convert to mm
			else:
				adjusted_sb_length = reported_sb_length
			image_data['im_sb_length_mm'] = adjusted_sb_length
			mm_per_px = adjusted_sb_length / distance(image_data['im_p_scale_bar_1'], \
				image_data['im_p_scale_bar_2'])
			image_data['im_mm_per_px'] = mm_per_px
			image_data['im_sb_length_px'] = distance(image_data['im_p_scale_bar_1'], \
				image_data['im_p_scale_bar_2'])
		else:
			print '##### Only one scale bar endpoint was recorded #####'

	# CALCULATE RELATIVE SHAPE PARAMETERS
	# ASYMMETRY: Defined as the ratio of the larger quartile width to the shorter one.
	if points == 5 or points == 9:
		# If 4 or 8 points could be dropped on the egg image, im_status is set to 'relative'
		image_data['im_status'] = 'relative'
		image_data['im_length_straight_px'] = distance(image_data['im_p_length_1'], image_data['im_p_length_2'])
		image_data['im_width_px'] = distance(image_data['im_p_midpoint_1'], image_data['im_p_midpoint_2'])
		if points == 9:
			quartile_len_1 = distance(image_data['im_p_1st_quart_1'], image_data['im_p_1st_quart_2'])
			quartile_len_3 = distance(image_data['im_p_3rd_quart_1'], image_data['im_p_3rd_quart_2'])
			if quartile_len_3 > quartile_len_1:
				longer_quartile = quartile_len_3
				shorter_quartile = quartile_len_1
			else:
				longer_quartile = quartile_len_1
				shorter_quartile = quartile_len_3
			image_data['im_asym'] = longer_quartile / shorter_quartile

			# CURVATURE: Recall that the cosine of the angle between two vectors (in radians)
			# equals their dot product divided by the product of their magnitudes
			if image_data['im_radius_px'] == 'DNE':
				image_data['im_curvature_deg'], image_data['im_curvature_rad'] = 0, 0
			else:
				x_v1 = image_data['im_p_length_1'][0] - image_data['im_p_circle_center'][0]
				y_v1 = image_data['im_p_length_1'][1] - image_data['im_p_circle_center'][1]
				x_v2 = image_data['im_p_length_2'][0] - image_data['im_p_circle_center'][0]
				y_v2 = image_data['im_p_length_2'][1] - image_data['im_p_circle_center'][1]
				curvature_rad = arccos((x_v1*x_v2 + y_v1*y_v2) / (image_data['im_radius_px'])**2)
				center_displacement_px = distance(image_data['im_p_egg_middle'],\
					midpoint(image_data['im_p_length_1'],image_data['im_p_length_2']))
				# Check to see whether the egg curves through more than 180 degrees,
				# correct the recorded curvature if so.
				if center_displacement_px > image_data['im_radius_px']:
					curvature_rad = 2*3.1415-curvature_rad

				curvature_deg = curvature_rad*180/3.1415
				image_data['im_curvature_deg'] = curvature_deg
				image_data['im_curvature_rad'] = curvature_rad
				image_data['im_length_curved_px'] = curvature_rad*image_data['im_radius_px']

		# CALCULATE ABSOLUTE SHAPE PARAMETERS
		# (if a scale has been recorded)
		if 'im_mm_per_px' in image_data:
			# If 8 points were placed and a scale is recorded, im_status is set to 'absolute'
			image_data['im_status'] = 'absolute'
			image_data['im_length_straight'] = mm_per_px*distance(image_data['im_p_length_1'], image_data['im_p_length_2'])
			image_data['im_width'] = mm_per_px*distance(image_data['im_p_midpoint_1'], image_data['im_p_midpoint_2'])

			if points == 9:
				# Check whether egg has a finite radius
				if image_data['im_radius_px'] == 'DNE':
					image_data['im_radius_mm'] = 'DNE'
					image_data['im_length_curved'] = image_data['im_length_straight']
				else:
					image_data['im_radius_mm'] = mm_per_px*image_data['im_radius_px']
					# Length along arc that is described by ends and middle of egg
					image_data['im_length_curved'] = curvature_rad*image_data['im_radius_mm']

	cv2.destroyAllWindows()		# Close the image window

	# If nothing has been recorded on the image, then set im_status to 'none'.
	if image_data == {}:
		# The key 'im_status' records the image parsing status of the entry.
		# If no information is recorded at all, but the entry has been opened
		# and completed, im_status is set to 'none'
		image_data['im_status'] = 'none'
	else:
		# If at least a cropping box has been recorded, do three things: 
		#  1) Get user answers for qualitative description questions.
		#  2) Display what the user recorded and ask for confirmation.

		# (1) Get qualitative egg attributes
		print '\n##### Enter qualitative egg attributes #####'
		print '----------------------------------------------'

		# Select one of the image type options
		while True:
			print 'What is the IMAGE TYPE?'
			print ' s = SEM'
			print ' t = transmitted light'
			print ' r = reflected light'
			print ' d = drawing'
			print ' o = other'
			image_type_options = ['s','t','r','d','o']
			q_image_type = raw_input('Select one and press ENTER: ')
			if q_image_type in image_type_options:
				break
			else:
				print 'Not a valid option'

		# Answer three qualitative questions about the egg image
		yn_options = ['y','n']
		while True:
			q_development = raw_input('Is embryo DEVELOPMENT shown on the page? y/n: ')
			if q_development in yn_options:
				break
			else:
				print 'Not a valid option'
		while True:
			q_operculum = raw_input('Is an OPERCULUM visible? y/n: ')
			if q_operculum in yn_options:
				break
			else:
				print 'Not a valid option'
		while True:
			q_geo_pattern = raw_input('Does the chorion have a visible GEOMETRIC PATTERN? y/n: ')
			if q_geo_pattern in yn_options:
				break
			else:
				print 'Not a valid option'
		
		# Ask whether the author reports a magnification instead of a scale bar
		mag_response = raw_input('MAGNIFICATION: Enter number if present; press "n" to continue: ')
		try:
			image_data['im_magnification'] = float(mag_response)
		except ValueError:
			pass

		# Store answers in image_data
		image_data['im_q_image_type'] = q_image_type
		image_data['im_q_development'] = q_development
		image_data['im_q_operculum'] = q_operculum
		image_data['im_q_geo_pattern'] = q_geo_pattern

		# (2) Display what the user recorded 
		print '\n##### All image info recorded for this entry #####'
		print '---------------------------------------------------'
		print image_data
		print '\n##### Check that the measurements look reasonable #####'
		print '-------------------------------------------------------'
		if points >= 5 and 'im_mm_per_px' in image_data:
			print 'Egg length (straight):', image_data['im_length_straight'], 'mm'
			print 'Egg width:', image_data['im_width'], 'mm'
		elif points >= 5 and 'im_mm_per_px' not in image_data:
			print 'Egg length (straight):', image_data['im_length_straight_px'], 'px'
			print 'Egg width:', image_data['im_width_px'], 'px'
		if 'im_sb_length_mm' in image_data:
			print 'Scale bar length', image_data['im_sb_length_mm'], 'mm'
		if 'im_length_curved' in image_data:
			print 'Egg length (curved):', image_data['im_length_curved'], 'mm'
		if 'im_asym' in image_data:
			print 'Asymmetry:', image_data['im_asym']
		if 'im_curvature_deg' in image_data:
			print 'Curvature:', image_data['im_curvature_deg'], 'degrees'
		print 'Image type:', image_data['im_q_image_type']
		print 'Development on page?', image_data['im_q_development']
		print 'Operculum visible?', image_data['im_q_operculum']
		print 'Geometric pattern visible?', image_data['im_q_geo_pattern']
		if 'im_magnificiation' in image_data:
			print 'Micrograph magnification:', image_data['im_magnificiation']
	
		# Ask for user confirmation that this is correct.
		# If not, return an empty dictionary.

		while True:
			q_confirm = raw_input('Is this correct? y/n: ')
			if q_confirm in yn_options:
				break
			else:
				print 'Not a valid option'
		
		# If does not confirm the data, an empty dict is returned.
		if q_confirm == 'n':
			image_data = {}
			return image_data
		else:
			#  1) Save an overview image that has annotations on it.
			#  2) Save a cropped image using the given cropping box.
			#  3) Finally, return the image_data.

			# Save annotated overview
			cv2.imwrite(overview_out_path,img)

			# Save the cropped image
			img = cv2.imread(img_path)
			cropped_img = img[image_data['im_box_h1']:image_data['im_box_h2'], \
				image_data['im_box_w1']:image_data['im_box_w2']]
			cv2.imwrite(cropped_out_path,cropped_img)

	return image_data

def main():
	# Initialize the global variable mode, set to 'box'.
	# mode = 'box'

	# If there is already a tmp_out_file in the directory, warn user and quit.
	if 'tmp_out_file.txt' in os.listdir('.'):
		print 'WARNING: Cannot over-write existing output database'
		return

	with open(args.dict_file, 'rb') as f:
		# First turn file into a list of dictionaries and count the total number of lines
		file_list = []
		number_of_entries = 0
		for line in f:
			# Attempts to turn each line back into a dictionary.
			# Syntax error is raised here if the line is not a dictionary.
			try:
				file_list.append(eval(line))
			except SyntaxError:
				print '\nWARNING! Line will not neatly turn into a dict.\n'
				print 'Problem file:', args.dict_file, '\n'
				print 'Problem line:', line
			number_of_entries += 1

		# Iterate over entries, dictionaries in a list
		for j in xrange(number_of_entries):
			# Define base_file_name
			if 'cs' in file_list[j]:
				base_img_name = file_list[j]['b']+'_'+file_list[j]['cg']+'_'+ file_list[j]['cs']+'_ID'+file_list[j]['ID']
			else:
				if 'cg' in file_list[j]:
					base_img_name = file_list[j]['b']+'_'+file_list[j]['cg']+'_ID'+file_list[j]['ID']
				else:
					base_img_name = file_list[j]['b']+'_'+file_list[j]['g']+'_ID'+file_list[j]['ID']
			if 'im_status' in file_list[j]:
				print file_list[j]['im_status']+':', base_img_name
			# If an entry has an image page recorded for it:
			if 'im_status' not in file_list[j] or file_list[j]['im_status'] == 'missing':
				if 'problem' not in file_list[j] or file_list[j]['problem'] not in ['no_taxonomy', 'no_name', 'order']:
					if 'i' in file_list[j]:
						print '\n##### Starting a new entry #####'
						print '----------------------------------'
						print 'bibid: ', file_list[j]['b']
						if 's' in file_list[j]:
							print 'Target species:', file_list[j]['g'], file_list[j]['s']
						else:
							print 'Target species:', file_list[j]['g']
						print 'Entry ID:', file_list[j]['ID']
						print 'Base name:', base_img_name

						# Copy the bibid to the clipboard to make it easier to find the current PDF.
						pyperclip.copy(file_list[j]['b']+'.pdf')

						# Define the file paths for saving images from the current entry
						img_path = os.path.join(args.input_image_dir,base_img_name+'.png')
						cropped_out_path = os.path.join(args.cropped_output_dir,base_img_name+'_cropped.png')
						overview_out_path = os.path.join(args.overview_output_dir,base_img_name+'_overview.png')

						# Process the image
						image_dict = process_one_image(img_path, cropped_out_path, overview_out_path)

						if image_dict == {}:
							print '\nNo data recorded for this entry.'
						if mode == 'quit':
							print '\n##### Quitting from image parsing #####'
							break

						# Add new the new items to the dictionary		
						# Update the the current line file_list[i]
						file_list[j].update(image_dict)
							
						# Write the full file_list to 'tmp_out_file.txt'
						with open('tmp_out_file.txt', 'w') as file:
							for entry in file_list:
								file.write("{}\n".format(entry))
	if mode != 'quit':
		print '\nAll images examined.'
		return

if __name__=='__main__':
	main()

