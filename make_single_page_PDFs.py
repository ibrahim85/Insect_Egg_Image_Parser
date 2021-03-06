### make_single_page_PDFs.py
### Created by Seth Donoughe in September 2016.
### Last updated April 2018.

# This work was a component of a project on the evolution of insect
# eggs. For more details, please see these two references:

# 	"Insect egg size and shape evolve with ecology, not developmental rate"
# 	Church, Donoughe, de Medeiros, Extavour; submitted 2018

# 	"A database of egg size and shape from more than 6,700 insect species"
# 	Church, Donoughe, de Medeiros, Extavour; submitted 2018

# The purpose of this script is to take a dictionary of egg data,
# generated by the tools described here:

# https://github.com/shchurch/Insect_Egg_Evolution

# Then, for all entries that were scored as having an egg image, 
# it will generate a 1-page PDF of the page containing that image.

import functions_for_parser as ffp
import argparse
import os.path

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output_dir', help = 'path to directory where PDFs will be re-saved')
parser.add_argument('-i','--input_dir', help = 'path to directory that contains sub-directories of all the PDFs in an order')
parser.add_argument('-d', '--dict_file', help = 'path text file containing the single-line dictionaries that parsing_eggs.py generates')
args = parser.parse_args()

input_dir = args.input_dir
dict_file = args.dict_file

if __name__=='__main__':

	# This list collects all the error strings
	total_errors = []

	# Get a list of subdirectories in input_dir
	sub_dirs = [os.path.join(input_dir, name) for name in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, name))]

	# Get a list of everything in those subdirectories
	all_paths = []
	for sub_dir in sub_dirs:
		all_paths += [os.path.join(sub_dir, name) for name in os.listdir(sub_dir)]

	with open(dict_file, 'rb') as f:
		for line in f:
			# turns each line back into a dict
			# will throw an error here if the line is not a dict
			try:
				d = eval(line)
			except SyntaxError:
				print '\nWARNING! Line will not neatly turn into a dict.\n'
				print 'Problem file:', dict_file, '\n'
				print 'Problem line:', line

			# if an entry has an image page recorded for it:
			if 'i' in d and 'cg' in d:
				if 'im_status' not in d or d['im_status']=='missing':
					if 'problem' not in d or d['problem'] not in ['no_taxonomy', 'no_name', 'order']:
						# subtract one to match python's indexing, which starts at 0
						page_list = [int(d['i'])-1]

						# out_path is set to [bibid]_[genus]_[species]_ID[ID] if there is a species recorded
						# otherwise set to [bibid]_[genus]_ID[ID]
						if 'cs' in d:
							out_path = os.path.join(args.output_dir, d['b']+'_'+d['cg']+'_'+d['cs']+'_ID'+d['ID']+'.pdf')
						else:
							out_path = os.path.join(args.output_dir, d['b']+'_'+d['cg']+'_ID'+d['ID']+'.pdf')

						print "Attempting to open:", d['b'], 'ID:', d['ID']

						# is there a path to the input PDF?
						message = 'PDF file not found'
						pdf_path = None
						for path in all_paths:
							if d['b']+'.pdf' in path:
								pdf_path = path
								message = 'success'
								break

						if pdf_path:
							# if the PDF isn't already in the out_dir, make one.
							if not os.path.isfile(out_path):
								# this function resaves a subset of pages as a new PDF, returning None
								# if the process worked smoothly, otherwise it returns an error string
								message = ffp.resave_PDF_subset_with_PyPDF2(pdf_path, page_list, out_path)
						
						# collect error information for current entry in a dictionary:
						errors_in_entry = {}
						if message != 'success':
							errors_in_entry['ID'] = d['ID']
							errors_in_entry['bibid'] = d['b']
							errors_in_entry['Genus'] = d['cg']
							errors_in_entry['Order'] = d['order1']
							if 'cs' in d:
								errors_in_entry['Species'] = d['cs']
							errors_in_entry['Error:'] = message
							total_errors.append([errors_in_entry])
			# Print error messages to an output file
			with open('PDF_saving_errors.txt', 'w') as f:
				for entry in total_errors:
					f.write("{}\n".format(entry))

