#!/usr/bin/env python3

'''
Programmer:     Fernando Rodriguez
Program Name:   Lab 2
File Name:      reader.py
Description:    Program reads user input and executes commands
'''

import sys
from methods import getVolumeInformation, readFAT, recoverFiles

# Print help file
def help():
    print("\n<flag>\t<option>\tdescription")
    print("-h\t\t\t:help file")
    print("-i\t<file>\t\t:input file")
    print("-v\t\t\t:volumn information")
    print("-f\t\t\t:export contents of the FAT table")
    print("-r\t\t\t:recover all files")

# Check for correct command line usage
if len(sys.argv) < 2:
	print("\nUsage: python3 reader.py <flag> <option>")
	help()
	sys.exit(0)

# init/declare variables for later use
file_name = ""
file_submitted = False
print_volume_info = False
print_fat_contents = False
extract_files = False

# Loop through command line arguments and store valid information
# Flags: -h, -t, -f
i = 1
while i < len(sys.argv):
	if sys.argv[i] == "-h":
		help()
		i += 1
	elif sys.argv[i] == "-v":
		print_volume_info = True
		i += 1
	elif sys.argv[i] == "-i":
		try:
			file_name = sys.argv[i+1]
			print("\nFile to inspect:", file_name)
			file_submitted = True
		except IndexError:
			print("File name expected after -i flag")
			sys.exit(0)
		i += 2
	elif sys.argv[i] == "-f":
		print_fat_contents = True
		i += 1
	elif sys.argv[i] == "-r":
		extract_files = True
		i += 1
	else:
		print("Flag not recognized")
		sys.exit(0)

if file_submitted:
	# open file
	try:
		in_file = open(file_name, "rb")
	except IOError:
		print("File", file_name, " was not found")
		sys.exit(0)

	if print_volume_info:
		print("\n----Volume Information----")
		volume = getVolumeInformation(in_file)
		for x in volume:
			print(x + ":", volume[x])

	if print_fat_contents:
		print("\n----Contents of the FAT table----")
		readFAT(in_file, "w")

	if extract_files:
		print("\n----Exported Files----")
		recoverFiles(in_file)

	# cleanup
	in_file.close()