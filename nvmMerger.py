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
MIX_MODE = False
BIN_MODE = 'bin'
NVM_MODE = 'nvm'

# command-line input processor
def optParser():
	global input_files, output_file
	py_ver = sys.hexversion
	py_ver_str = str(sys.version_info[0]) + '.' + str(sys.version_info[1]) + '.' + str(sys.version_info[2])
	#print '\n*Your python version is ' + py_ver_str
	sDescription = ' nvmMerger merges two NVM text/bin files into one'
	sDescription += ', and file extension will decide merging into bin/text file.'
	sDescription += '\n Note: if tags are duplicated, further right file has precedence'

	if py_ver >= PYTHON_VERSION:
		import argparse
		#print '*Use argparse module\n'
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
		#print '*Use optparse module\n'
		from optparse import OptionParser
		usage = 'nvmMerger.py [-h] [-o output_file] input_files [input_files ...]'
		parser = OptionParser(usage, description = sDescription)
		parser.add_option('-o', '--output', type='string', 
				help='NVM bin/text output file name after merger')
		(options, args) = parser.parse_args()
		input_files = args
		output_file = options.output
		
# class to represent NVM tag
# TagIndex: Tag0, Tag1, ...
# TagNum: integer representation of Tag #
# TagNumLSB: bin representation of Tag #
# TagNumMSB: bin representation of Tag #
# TagLength: integer representation of Tag length	
# TagLengthLSB: bin representation of Tag length	
# TagLengthMSB: bin representation of Tag length	
# TagValue: 
#	binary mode represented by a list of bin values
#	text mode represented by a list of str, only first element used
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
		else:
			self.TagNumLSB = binascii.a2b_hex(hex((self.TagNum % 256)).lstrip('0x').zfill(2))
			self.TagNumMSB = binascii.a2b_hex(hex((self.TagNum / 256)).lstrip('0x').zfill(2))
			self.TagLengthLSB = binascii.a2b_hex(hex((self.TagLength % 256)).lstrip('0x').zfill(2))
			self.TagLengthMSB = binascii.a2b_hex(hex((self.TagLength / 256)).lstrip('0x').zfill(2))

	
	def inputval(self, finput=None, valstr=None):
		if MERGER_MODE == BIN_MODE and finput is not None:
			iLSB = int(binascii.b2a_hex(self.TagLengthLSB), 16)
			iMSB = int(binascii.b2a_hex(self.TagLengthMSB), 16)
			self.TagLength = iLSB + iMSB*16*16
			nLSB = int(binascii.b2a_hex(self.TagNumLSB), 16)
			nMSB = int(binascii.b2a_hex(self.TagNumMSB), 16)
			self.TagNum = nLSB + nMSB*16*16
			for i in range(self.TagLength):
				x = finput.read(1)
				self.TagValue.append(x)

		elif MERGER_MODE == NVM_MODE and valstr is not None:
			valist = valstr.split('=')
			self.TagValue.append(valist[1])
		else:
			print '\n\tNo TagValue inserted\n'
	
	
	def printall(self):
		print '------'
		print self.TagNum
		if MERGER_MODE == BIN_MODE:
			print binascii.b2a_hex(self.TagNumLSB)
			print binascii.b2a_hex(self.TagNumMSB)
			print binascii.b2a_hex(self.TagLengthLSB)
			print binascii.b2a_hex(self.TagLengthMSB)
			for i in range(self.TagLength):
				print binascii.b2a_hex(self.TagValue[i])
		if MERGER_MODE == NVM_MODE:
			print self.TagLength
			print self.TagValue[0]

# check if: 
#	1) files' extension are bin or nvm
#	2) the NVM file is valid: now this is version2, so first byte is 0x02
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
	nlindex = 0
	for fname in flist:
		finfo = os.stat(fname)
		fsize = finfo.st_size
		# open the file
		with open(fname, 'rb+') as fobj:
			# Move cursor to where data starts
			fobj.seek(NVM_TLV_DATA_START)
			i = 0
			while (fobj.tell() < fsize) : 
				nvm_list.append(
					NVMTag(i, fobj.read(1), fobj.read(1), fobj.read(1), fobj.read(1))
				)	
				fobj.seek(NVM_TLV_ZERO_PADDING, 1)
				nvm_list[nlindex].inputval(fobj)
				i += 1
				nlindex += 1
			#print fobj.tell()
			fobj.close()
	#for nvm in nvm_list:
	#	nvm.printall()

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

		if MERGER_MODE == BIN_MODE:
			for j in range(nvm.TagLength):
				fobj.write(nvm.TagValue[j])
		elif MERGER_MODE == NVM_MODE:
			# strip CR and LF to avoid TypeError exception from binascii
			valist = nvm.TagValue[0].strip('\r\n').split(' ')
			for val in valist:
				#print val
				fobj.write(binascii.a2b_hex(val))

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
		sTagValue = 'TagValue =' 
		if MERGER_MODE == NVM_MODE:
			sTagValue += nvm.TagValue[0] 
			if nvm.TagIndex != TAG_NUM - 1:
				sTagValue += '\n'
		elif MERGER_MODE == BIN_MODE:
			for i in nvm.TagValue:
				sTagValue += ' '
				sTagValue += binascii.b2a_hex(i)
			sTagValue += '\n'
			if nvm.TagIndex != TAG_NUM - 1:
				sTagValue += '\n'
			
		fobj.write(sHeader)
		fobj.write(sTagNum)
		fobj.write(sTagLength)
		fobj.write(sTagValue)


# populate all nvms into the list
def nvm2list(flist, nvm_list):
	nlindex = 0
	for fname in flist:
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
					nvm_list[nlindex].inputval(valstr=line)
					#nvm_list[nlindex].printall()
					tagIndex += 1
					nlindex += 1
				else:
					continue
			fobj.close()


# merge two input lists and sort them based on Tag num
def mergelists(listm):
	global TAG_NUM
	nvm_list = sorted(listm, key=lambda nvm: nvm.TagNum)
	for nvm in nvm_list:
		for nvmr in reversed(nvm_list):
			if nvm.TagNum == nvmr.TagNum:
				if nvm is not nvmr:
					#print 'Same TagNum but not same object: ' + str(nvm.TagNum)	
					#nvm.printall()
					#nvmr.printall()
					nvm.TagNum = -1
					
	TAG_NUM = len(nvm_list) 
	complete_list = []
	# redefine TagIndex after merging
	for i in range(TAG_NUM):
		if nvm_list[i].TagNum != -1:
			complete_list.append(nvm_list[i])

	TAG_NUM = len(complete_list) 
	for i in range(TAG_NUM):
		complete_list[i].TagIndex = i
		#complete_list[i].printall()

	return complete_list
	
# main function
def nvmMerger():
	global output_file
	global MIX_MODE
	optParser()
	## Check file format and decides MODE
	if not nvmChecker(input_files):
		exit()

	print ' Pass input file checks, starting to '+ MERGER_MODE + ' merger...'
	if MERGER_MODE == BIN_MODE:
		ofname = DEFAULT_FILE_OUTPUT + '.bin'
		if output_file[-3:] == 'bin':
			ofname = output_file
		elif output_file[-3:] == 'nvm':
			MIX_MODE = True
		else:
			print ' No valid output file name specified, using default one...'

		m = open(ofname, 'w+b')
		bin2list(input_files, list_input)
		#print len(list_input)
		list_output = mergelists(list_input)	
		#
		list2bin(list_output, m)
		m.close()
	elif MERGER_MODE == NVM_MODE:
		ofname = DEFAULT_FILE_OUTPUT + '.nvm'
		if output_file[-3:] == 'nvm':
			ofname = output_file
		elif output_file[-3:] == 'bin':
			MIX_MODE = True
		else:
			print ' No valid output file name specified, using default one...'
			
		m = open(ofname, 'w+')
		nvm2list(input_files, list_input)
		list_output = mergelists(list_input)	
		writeHeaderToFile(m)
		list2NVMfile(list_output, m)
		m.close()

	if MIX_MODE:
		try:
			if output_file[-3:] == 'nvm':
					with open(output_file, 'w+') as m:
						writeHeaderToFile(m)
						list2NVMfile(list_output, m)
						m.close()
			else:
					with open(output_file, 'w+b') as m:
						list2bin(list_output, m)
						m.close()
		except IOError:
			print ' Cannot open \"' + output_file + '\"\n'

	print '\n\tMerge completes\n'


nvmMerger()
