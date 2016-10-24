#!/usr/bin/python
import binascii
import os
import sys
from datetime import datetime

# use argparse for python version higher than 2.7
# use optparse for python version lower than 2.7
# argparse was added since 2.7
PYTHON_VERSION = 0x02070000

NVM_TLV_VERSION = b'\x02'
NVM_TLV_DATA_START = 4
NVM_TLV_TAG = 2
NVM_TLV_LEN = 2
NVM_TLV_ZERO_PADDING = 8
NVM_HEADER = 0
NVM_BODY_LEN = 0
TAG_NUM = 0 
# create lists stores whole bin file
list_input = []
list_output = []
input_files = []
output_file = ''
DEFAULT_FILE_OUTPUT = 'merged_nvm_' + datetime.now().strftime('%H%M%S')
#
MERGER_MODE = ''
BIN_MODE = 'bin'
NVM_MODE = 'nvm'

def optParser():
	global input_files, output_file
	py_ver = sys.hexversion
	py_ver_str = str(sys.version_info[0]) + '.' + str(sys.version_info[1]) + '.' + str(sys.version_info[2])
	print '\n*Your python version is ' + py_ver_str
	sDescription = ' nvmMerger merges two NVM text/bin files into one'
	sDescription += ', and file extension will decide merging into bin/text file.'
	sDescription += '\n Note: if tags are duplicated, further right file has precedence'

	#if py_ver <= PYTHON_VERSION:
	if py_ver >= PYTHON_VERSION:
		import argparse
		print '*Use argparse module\n'
		parser = argparse.ArgumentParser(description = sDescription)
		parser.add_argument('input_files', nargs='+', help='NVM bin/text files to merge')
		parser.add_argument('-o', '--output', metavar='output_file', 
				type=str, default=DEFAULT_FILE_OUTPUT, 
				help='NVM bin/text output file name after merger')
		#parser.print_help()
		args = parser.parse_args()
		input_files = args.input_files
		output_file = args.output
	else:
		print '*Use optparse module\n'
		from optparse import OptionParser
		usage = 'nvmMerger.py [-h] [-o output_file] input_files [input_files ...]'
		parser = OptionParser(usage, description = sDescription)
		parser.add_option('-o', '--output', type='string', 
				help='NVM bin/text output file name after merger')
		(options, args) = parser.parse_args()
		input_files = args
		output_file = options.output
		
	
class NVMTag:
	def __init__(self, TIDX, TNL=None, TNB=None, TLL=None, TLM=None, TagNum=0, TagLength=0):
		self.TagIndex = TIDX
		self.TagValue = []
		self.TagNum = TagNum
		self.TagLength = TagLength 
		if TNL is not None and TNB is not None and TLL is not None and TLM is not None:
			# BIN_MODE only attributes
			self.TagNumLSB = TNL  
			self.TagNumMSB = TNB
			self.TagLengthLSB = TLL
			self.TagLengthMSB = TLM

	
	def inputval(self, finput=None, valstr=None):
		if MERGER_MODE == BIN_MODE and finput is not None:
			iLSB = int(binascii.b2a_hex(self.TagLengthLSB), 16)
			iMSB = int(binascii.b2a_hex(self.TagLengthMSB), 16)
			self.TagLength = iLSB + iMSB*16
			nLSB = int(binascii.b2a_hex(self.TagNumLSB), 16)
			nMSB = int(binascii.b2a_hex(self.TagNumMSB), 16)
			self.TagNum = nLSB + nMSB*16
			for i in range(self.TagLength):
				x = finput.read(1)
				self.TagValue.append(x)

		elif MERGER_MODE == NVM_MODE and valstr is not None:
			val = valstr.split('=')
			self.TagValue.append(val[1])
		else:
			print '\n\tNo TagValue inserted\n'
	
	def printall(self):
		if MERGER_MODE == BIN_MODE:
			print binascii.b2a_hex(self.TagNumLSB)
			print binascii.b2a_hex(self.TagNumMSB)
			print binascii.b2a_hex(self.TagLengthLSB)
			print binascii.b2a_hex(self.TagLengthMSB)
			for i in range(self.TagLength):
				print binascii.b2a_hex(self.TagValue[i])
		if MERGER_MODE == NVM_MODE:
			print self.TagNum
			print self.TagLength
			print self.TagValue[0]

# check if: 
#	1) files' extension are bin or nvm
#	2) the NVM file is valid
def nvmChecker(flist):
	# check the file extension
	global MERGER_MODE
	ftlist = []
	for fname in flist:
		#print fname[-3:]
		ftlist.append(fname[-3:])

	if ftlist.count('bin') == len(ftlist):
		MERGER_MODE = BIN_MODE
	elif ftlist.count('nvm') == len(ftlist):
		MERGER_MODE = NVM_MODE
	else:
		print '\n\tInput file extensions not valid, exit...\n'
		return False	

	if MERGER_MODE == BIN_MODE:
		for fname in flist:
			try:
				# extract the NVM header
				with open(fname, 'rb') as f:
					fheader = f.read(NVM_TLV_DATA_START)
					f.close()
				#print binascii.b2a_hex(fheader[0])
				# first type is the TLV type
				if fheader[0] != NVM_TLV_VERSION:
					print '\n\tTwo NVM have different headers, exit...\n'
					return False
			except IOError:
				print '\n\t' + fname + ' not exist, exit...\n'
				return False

	elif MERGER_MODE == NVM_MODE:
		for fname in flist:
			f_tag_num = -1
			try:
				with open(fname, 'r') as f:
					for line in f:
						if '[Tag]' in line:
							f_tag_num = int(f.next().strip('Num ='),10)
							break
					f.close()
					
				if f_tag_num <= 0:
					print '\n\t' + fname + ' has improper NVM text format, exit...\n'
					return False
			except ValueError:
				print '\n\tFiles have improper NVM text format, exit...\n'
				return False
			except IOError:
				print '\n\t' + fname + ' not exist, exit...\n'
				return False
	return True
	

# populate all nvms into the list
def bin2list(flist, nvm_list):
	for fname in flist:
		finfo = os.stat(fname)
		fsize = finfo.st_size
		#print fsize
		# open the file
		with open(fname, 'rb+') as fobj:
			i = 0
			# Move cursor to where data starts
			fobj.seek(NVM_TLV_DATA_START)
			#for i in range(3):
			while (fobj.tell() < fsize) : 
				nvm_list.append(
					NVMTag(i, fobj.read(1), fobj.read(1), fobj.read(1), fobj.read(1))
				)	
				fobj.seek(NVM_TLV_ZERO_PADDING, 1)
				nvm_list[i].inputval(fobj)
				i += 1
			#print fobj.tell()
			fobj.close()

# write the list to BIN file
def list2bin(nvm_list, fobj):
	# fill up the NVM_HEADER
	taglen_sum = 0
	fobj.seek(NVM_TLV_DATA_START)
	for nvm in nvm_list:
		taglen_sum += (NVM_TLV_TAG + NVM_TLV_LEN + NVM_TLV_ZERO_PADDING + nvm.TagLength)
		fobj.write(nvm.TagNumLSB)
		fobj.write(nvm.TagNumMSB)
		fobj.write(nvm.TagLengthLSB)
		fobj.write(nvm.TagLengthMSB)
		for j in range(NVM_TLV_ZERO_PADDING):
			fobj.write(b'\x00')
		for j in range(nvm.TagLength):
			fobj.write(nvm.TagValue[j])

	#print taglen_sum
	tmp = hex(taglen_sum).lstrip('0x').zfill(6)
	NVM_BODY_LEN = binascii.a2b_hex(tmp[4:]) + binascii.a2b_hex(tmp[2:4]) + binascii.a2b_hex(tmp[:2])
	NVM_HEADER = b'\x02' + NVM_BODY_LEN
	#print binascii.b2a_hex(NVM_HEADER)
	fobj.seek(0)
	fobj.write(NVM_HEADER)


# write the header of NVM-text file
def writeHeaderToFile(fobj):
        fobj.write('#\n#\n')
        fobj.write('#    Tag Listfile     \n')
        fobj.write('#\n#\n')
        fobj.write('\n')
        fobj.write('[General]\n')
        fobj.write('Signature = windows\n')
        fobj.write('FormatVersion = 1.0\n')

        s = ' ' 
        dt = datetime.now()
        s += dt.strftime('%A %B %d, %Y   %I:%M:%S %p')  
    
        fobj.write('TimeStamp =' + s)
        fobj.write('\n\n')
        fobj.write('[Tag]\n')
        s = 'Num = ' + str(TAG_NUM) + '\n\n'
        fobj.write(s)

# write the list to NVM-text file
def list2NVMfile(nvm_list, fobj):
	for nvm in nvm_list:
		sHeader = '[Tag' + str(nvm.TagIndex) + ']\n'
		sTagNum = 'TagNum = ' + str(nvm.TagNum) + '\n'
		sTagLength = 'TagLength = ' + str(nvm.TagLength) + '\n'
		sTagValue = 'TagValue =' + nvm.TagValue[0] 
		if nvm.TagIndex != TAG_NUM - 1:
			sTagValue += '\n'
		fobj.write(sHeader)
		fobj.write(sTagNum)
		fobj.write(sTagLength)
		fobj.write(sTagValue)


# populate all nvms into the list
def nvm2list(fname, nvm_list):
	tagIndex = 0
	tagNum = 0
	tagLen = 0
	with open(fname, 'r') as fobj:
		for line in fobj:
			if 'TagNum' in line:
				tagNum = int(line.strip('TagNum ='), 10)
			elif 'TagLength' in line:
				tagLen = int(line.strip('TagLength ='), 10)
			elif 'TagValue' in line:
				nvm_list.append(NVMTag(tagIndex,TagNum=tagNum,TagLength=tagLen))
				nvm_list[tagIndex].inputval(valstr=line)
				#nvm_list[tagIndex].printall()
				tagIndex += 1
			else:
				continue
		fobj.close()


# merge two input lists and sort them based on Tag num
def mergelists(listf, lists):
	global TAG_NUM
	for nvms in reversed(lists):
		for nvmf in listf:
			if nvms.TagNum == nvmf.TagNum:
				#listf[nvmf.TagIndex].printall()
				listf.pop(nvmf.TagIndex)	
	listm = listf + lists
	TAG_NUM = len(listm) 
	# sort the merged list	
	nvm_list = sorted(listm, key=lambda nvm: nvm.TagNum)
	# redefine TagIndex after merging
	for i in range(TAG_NUM):
		nvm_list[i].TagIndex = i

	return nvm_list
	
# main function
def nvmMerger():
	global output_file
	optParser()
	## Check file format and decides MODE
	if not nvmChecker(input_files):
		exit()

	print ' Pass input file checks, starting to '+ MERGER_MODE + ' merger...'
	if MERGER_MODE == BIN_MODE:
		ofname = DEFAULT_FILE_OUTPUT + '.bin'
		if output_file[-3:] == 'bin':
			ofname = output_file

		m = open(ofname, 'w+b')
		bin2list(input_files, list_input)
		print len(list_input)
	#	list_m = mergelists(list_input)	
	#	#
	#	list2bin(list_m, m)
	#	m.close()
	elif MERGER_MODE == NVM_MODE and output_file[-3:] == 'nvm':
		m = open(output_file, 'w+')
	#	nvm2list(input_files, list_input)
	#	list_m = mergelists(list_f, list_s)	
	#	writeHeaderToFile(m)
	#	list2NVMfile(list_m, m)
	#	m.close()
	#else:
	#	print '\n\tOutput file extension is not matched with input files'	
	#	print '\tMerge failed\n'
	#	exit()

	#print '\n\tMerge completes\n'

nvmMerger()
