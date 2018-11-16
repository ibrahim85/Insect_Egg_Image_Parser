### make_single_page_PNGs.py
### Created by Seth Donoughe in September 2016.
### Last updated April 2018.

# This work was a component of a project on the evolution of insect
# eggs. For more details, please see these two references:

# 	"Insect egg size and shape evolve with ecology, not developmental rate"
# 	Church, Donoughe, de Medeiros, Extavour; submitted 2018

# 	"A database of egg size and shape from more than 6,700 insect species"
# 	Church, Donoughe, de Medeiros, Extavour; submitted 2018

# PURPOSE:
# To convert a directory of single-page PDFs into PNGs as a specific image resolution.

import argparse
from os.path import isfile, join
from os import listdir
from wand.image import Image, Color

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output_dir', help = 'path to directory where PNGs will be re-saved')
parser.add_argument('-i','--input_dir', help = 'path to directory that contains single-page PDFs')
args = parser.parse_args()

if __name__=='__main__':

	# This list collects all the error strings
	total_errors = []

	# Get the list of files in the input directory
	input_dir_files = [f for f in listdir(args.input_dir) if isfile(join(args.input_dir, f))]

	# Get the list of files in the output directory
	output_dir_files = [f for f in listdir(args.output_dir) if isfile(join(args.output_dir, f))]

	for pdf in input_dir_files:
		if pdf[-4:] == '.pdf':
			pdf_base_name = pdf[:-4]+'.png'
			if pdf_base_name not in output_dir_files:
				print pdf_base_name
				# Converting single page into JPG
				with Image(filename=join(args.input_dir,pdf), resolution=300) as img:
					img.format = 'png'
					img.background_color = Color('white')
					img.alpha_channel = 'remove'
					img.save(filename=join(args.output_dir,pdf[:-4]+'.png'))