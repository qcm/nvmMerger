#!/usr/bin/python
import binascii
import os
import sys
from datetime import datetime

# use argparse for python version higher than 2.7
# use optparse for python version lower than 2.7
# argparse was added since 2.7
PYTHON_VERSION = 0x02070000

NVM_TLV_VERSION_BT = b'\x02'
NVM_TLV_VERSION_FM = b'\x03'
NVM_TLV_VERSION_BTFM = b'\x04'
NVM_TLV_VERSION = b'\x02'
NVM_TLV_DATA_START = 4
NVM_TLV_TAG = 2
NVM_TLV_LEN = 2
NVM_TLV_ZERO_PADDING = 8
NVM_BODY_LEN = 0
NVM_HEADER = ''

TAG_NUM = 0 
# create lists stores whole bin file
list_input_bt = []
list_input_fm = []
#list_output = []
bt_list_output = []
fm_list_output = []
input_files = []
output_file = ''
DEFAULT_FILE_OUTPUT = 'merged_nvm_' + datetime.now().strftime('%H%M%S')
#
MERGER_MODE = ''
TRANS_MODE = False # output involves a bin->nvm/nvm->bin transfer
BIN_MODE = 'bin' # merge binary files of NVM
NVM_MODE = 'nvm' # merge text files of NVM
BTFM_MODE = False
BT_CNT = 0 # BT NVM file counts
FM_CNT = 0 # FM NVM file counts

# command-line input processor
def optParser():
	global input_files, output_file
	global BTFM_MODE, MERGER_MODE, BT_CNT, FM_CNT
	py_ver = sys.hexversion
	py_ver_str = str(sys.version_info[0]) + '.' + str(sys.version_info[1]) + '.' + str(sys.version_info[2])
	#print '\n*Your python version is ' + py_ver_str
	sDescription = ' nvmMerger merges multiple NVM text/bin files into one'
	sDescription += ', and file extension will decide merging into bin/text file.'
	sDescription += '\n Note: if tags are duplicated, further right file has precedence'

	if py_ver >= PYTHON_VERSION:
		import argparse
		#print '*Use argparse module\n'
		parser = argparse.ArgumentParser(description = sDescription)
		parser.add_argument('input_files', nargs='*', help='NVM bin/text files to merge')
		#parser.add_argument('input_files', nargs='+', help='NVM bin/text files to merge')
		parser.add_argument('-o', '--output', metavar='output_file', 
				type=str, help='NVM bin/text output file name after merger')
		# for BTFM_MODE text-based merge
		parser.add_argument('--BT', metavar='BT.nvm', nargs='*', help='BT NVM text-based input files')
		parser.add_argument('--FM', metavar='FM.nvm', nargs='*', help='FM NVM text-based input files')
		args = parser.parse_args()
		input_files = args.input_files
		output_file = args.output
		if len(input_files) == 0: # imply NVM_MODE, otherwise simply using positional argument
			MERGER_MODE = NVM_MODE
			if args.BT is not None and args.FM is not None:
				BT_CNT = len(args.BT)
				FM_CNT = len(args.FM)
				input_files = [NVM_TLV_VERSION_BT, args.BT, NVM_TLV_VERSION_FM, args.FM]
				BTFM_MODE = True
			elif args.BT is not None:
				BT_CNT = len(args.BT)
				input_files = [NVM_TLV_VERSION_BT, args.BT]
			elif args.FM is not None:
				FM_CNT = len(args.FM)
				input_files = [NVM_TLV_VERSION_FM, args.FM]
			else:
				parser.print_help()
				print '\n No input files'
				exit()
		else:
			if args.BT is not None or args.FM is not None:
				parser.print_help()
				print '\nFor BTFM-NVM merge:'
				print ' Please append all BT-NVM text file after --BT, all FM-NVM text file after --FM'
				exit()
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
	
	if len(input_files) == 1 and output_file is None :
		print '\n\tNothing to be done. Exit\n'
		exit()
	elif output_file is None:
		#print 'use default name'
		output_file = DEFAULT_FILE_OUTPUT
		
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

	
	def inputval(self, finput=None, valstr=None, index=None):
		if MERGER_MODE == BIN_MODE:
			iLSB = int(binascii.b2a_hex(self.TagLengthLSB), 16)
			iMSB = int(binascii.b2a_hex(self.TagLengthMSB), 16)
			self.TagLength = iLSB + iMSB*16*16
			nLSB = int(binascii.b2a_hex(self.TagNumLSB), 16)
			nMSB = int(binascii.b2a_hex(self.TagNumMSB), 16)
			self.TagNum = nLSB + nMSB*16*16
				
			if index is None:
				for i in range(self.TagLength):
					# use file I/O to read
					x = finput.read(1)
					self.TagValue.append(x)
			else:
				for i in range(index, index+self.TagLength):
					self.TagValue.append(finput[i])

		elif MERGER_MODE == NVM_MODE and valstr is not None:
			valist = valstr.split('=')
			self.TagValue.append(valist[1])
		else:
			print '\n\tNo TagValue inserted\n'
	
	
	def printall(self):
		print '/' * 10
		print 'TagNum: %d' %self.TagNum
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
		print '\\' * 10

# check if: 
#	1) files' extension are bin or nvm
#	2) the NVM file is valid: 
#		BT's first byte is 0x02
#		FM's first byte is 0x03
#		BTFM first byte is 0x04
# flist has two forms:
#	1) non BTFM_MODE: list of input file names
#	2) BTFM_MODE: bianry type code + list of input file names
def nvmChecker(flist):
	# check the file extension
	global MERGER_MODE, BTFM_MODE
	global BT_CNT, FM_CNT

	if BT_CNT == 0 and FM_CNT == 0:
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
				if fheader[0] == NVM_TLV_VERSION_BT:
					BT_CNT += 1
				elif fheader[0] == NVM_TLV_VERSION_FM:
					FM_CNT += 1
				elif fheader[0] == NVM_TLV_VERSION_BTFM:
					continue
				else:
					print '\n\t' + fname + ' has invalid header, exit...\n'
					return False
			except IOError:
				print '\n\t' + fname + ' not exist, exit...\n'
				return False
		
		if BT_CNT != len(flist) and FM_CNT != len(flist):
			BTFM_MODE = True

	elif MERGER_MODE == NVM_MODE:
		print '!'*10
		fnamelist = []
		if BT_CNT > 0 or FM_CNT > 0:
			#pass
			ptr = iter(flist)
			for i in ptr:
				if i == NVM_TLV_VERSION_BT:
					tmp = next(ptr)
					print 'BT length %d' %len(tmp)
					fnamelist += tmp
				if i == NVM_TLV_VERSION_FM:
					tmp = next(ptr)
					print 'FM length %d' %len(tmp)
					fnamelist += tmp
		else:
			fnamelist = flist
		for fname in fnamelist:
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
## input:
## 	 flist: a list of file names
## 	 btlist: a list to save BT NVMTag 
## 	 fmlist: a list to save FM NVMTag 
#
def bin2list(flist, btlist=None, fmlist=None):
	btindex = 0 # index of btlist (across all input files)
	fmindex = 0 # index of fmlist (across all input files)
	for fname in flist:
		finfo = os.stat(fname)
		fsize = finfo.st_size
		# open the file
		with open(fname, 'rb') as fobj:
			# check the file type
			# move cursor to where data starts
			fheader = fobj.read(NVM_TLV_DATA_START)
			if fheader[0] == NVM_TLV_VERSION_BT:
				i = 0
				while (fobj.tell() < fsize) : 
					btlist.append(
						NVMTag(i, fobj.read(1), fobj.read(1), fobj.read(1), fobj.read(1))
					)	
					fobj.seek(NVM_TLV_ZERO_PADDING, 1)
					btlist[btindex].inputval(fobj)
					i += 1
					btindex += 1
			elif fheader[0] == NVM_TLV_VERSION_FM:
				i = 0
				while (fobj.tell() < fsize) : 
					fmlist.append(
						NVMTag(i, fobj.read(1), fobj.read(1), fobj.read(1), fobj.read(1))
					)	
					fobj.seek(NVM_TLV_ZERO_PADDING, 1)
					fmlist[fmindex].inputval(fobj)
					i += 1
					fmindex += 1
			elif fheader[0] == NVM_TLV_VERSION_BTFM:
				# loop for BT and FM sections
				flen = getDataLength(fheader)
				while(flen > 0):
					dh = fobj.read(NVM_TLV_DATA_START)
					dlen = getDataLength(dh)
					data = fobj.read(dlen)

					if dh[0] == NVM_TLV_VERSION_BT:
						# BT data, put in btlist #
						print '\n\tBT data dlen: %d\n' %dlen
						i = 0 # index in data
						li = btindex # index in list
						while(i < dlen):
							btlist.append(
								NVMTag(li, data[i], 
								data[i+1], data[i+2], data[i+3])
	     						)
							i += NVM_TLV_TAG + NVM_TLV_LEN 
							i += NVM_TLV_ZERO_PADDING
							btlist[li].inputval(finput=data,index=i)
							i += btlist[li].TagLength
							#btlist[li].printall()
							li += 1
						btindex = li

					if dh[0] == NVM_TLV_VERSION_FM:
						# FM data, put in fmlist #
						print '\n\tFM data dlen: %d\n' %dlen
						i = 0 # index in data
						li = fmindex # index in the list
						while(i < dlen):
							fmlist.append(
								NVMTag(li, data[i], 
								data[i+1], data[i+2], data[i+3])
	     						)
							i += NVM_TLV_TAG + NVM_TLV_LEN 
							i += NVM_TLV_ZERO_PADDING
							fmlist[li].inputval(finput=data,index=i)
							i += fmlist[li].TagLength
							#fmlist[li].printall()
							li += 1
						fmindex = li	

					flen -= NVM_TLV_DATA_START
					flen -= dlen

			#print fobj.tell()
			fobj.close()

# append header for BIN file
def getBinHeader(btype, ilist, llen):
	if ilist is None:
		llen = hex(llen).lstrip('0x').zfill(6)
	elif llen is None:
		llen = 0
		for i in ilist:
			llen += NVM_TLV_TAG + NVM_TLV_LEN + NVM_TLV_ZERO_PADDING + i.TagLength
		llen = hex(llen).lstrip('0x').zfill(6)
	blen = binascii.a2b_hex(llen[4:]) + binascii.a2b_hex(llen[2:4]) + binascii.a2b_hex(llen[:2]) 
	return btype + blen
	

# write the list to BIN file
# input:
#	key-value pair (Dictionary)
#	file object to write
# {BTHEADER: BTLIST, FMHEADER: FMLIST, ...}	
def list2bin_(dicts, fobj):
	# lengh in top-level header, not includes top-level header itself
	tlv_len = 0
	if len(dicts) > 1: 
		# multiple lists, save first 4 bytes for top-level header
		fobj.seek(NVM_TLV_DATA_START)
	for bincode in sorted(dicts):
		nvmlist = dicts[bincode]
		print '*' *10
		print binascii.b2a_hex(bincode)
		print '*' *10
		# write header for every list
		fobj.write(getBinHeader(bincode, nvmlist, None))
		tlv_len += 4
		# write NVMs
		for nvm in nvmlist:
			fobj.write(nvm.TagNumLSB)
			fobj.write(nvm.TagNumMSB)
			fobj.write(nvm.TagLengthLSB)
			fobj.write(nvm.TagLengthMSB)
			for i in range(NVM_TLV_ZERO_PADDING):
				fobj.write(b'\x00')
			if MERGER_MODE == BIN_MODE:
				for j in range(nvm.TagLength):
					fobj.write(nvm.TagValue[j])
			elif TRANS_MODE:
				# strip CR and LF to avoid TypeError exception from binascii
				valist = nvm.TagValue[0].strip('\r\n').split(' ')
				for val in valist:
					#print val
					fobj.write(binascii.a2b_hex(val))
			tlv_len += (NVM_TLV_TAG + NVM_TLV_LEN + NVM_TLV_ZERO_PADDING + nvm.TagLength)

	# write top-level header
	if len(dicts) > 1: 
		fobj.seek(0)
		fobj.write(getBinHeader(NVM_TLV_VERSION_BTFM, None, tlv_len))
		

def list2bin(nvm_list, fobj):
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
		elif MERGER_MODE == TRANS_MODE:
			# strip CR and LF to avoid TypeError exception from binascii
			valist = nvm.TagValue[0].strip('\r\n').split(' ')
			for val in valist:
				#print val
				fobj.write(binascii.a2b_hex(val))

	#print taglen_sum
	tmp = hex(taglen_sum).lstrip('0x').zfill(6)
	NVM_BODY_LEN = binascii.a2b_hex(tmp[4:]) + binascii.a2b_hex(tmp[2:4]) + binascii.a2b_hex(tmp[:2])
	# TBD
	# still not working if transfer fm.nvm -> fm.bin
	# also not working on btfm mode
	global NVM_HEADER
	if not BTFM_MODE:
		if BT_CNT > 0:
			NVM_HEADER = NVM_TLV_VERSION_BT + NVM_BODY_LEN
		if FM_CNT > 0:
			NVM_HEADER = NVM_TLV_VERSION_FM + NVM_BODY_LEN
	else:
		pass
	#print binascii.b2a_hex(NVM_HEADER)
	fobj.seek(0)
	fobj.write(NVM_HEADER)

# get BIN file payload length from header
## input: 4 bytes header ##
## return: length of the BIN payload ##
def getDataLength(h):
	h1 = int(binascii.b2a_hex(h[1]), 16)
	h2 = int(binascii.b2a_hex(h[2]), 16)
	h3 = int(binascii.b2a_hex(h[3]), 16)
	length = (h1%16) + (h1/16)*16
	length += ((h2%16) + (h2/16)*16)*256
	length += ((h3%16) + (h3/16)*16)*65536
	return length
	
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
	print '* list size %d' %len(nvm_list)
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


# merge input lists and sort them based on Tag num
def mergelists(ilist):
	global TAG_NUM
	nvm_list = sorted(ilist, key=lambda nvm: nvm.TagNum)
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
	global output_file, bt_list_output, fm_list_output
	global TRANS_MODE
	optParser()
	## Check file format and decides MODE
	if not nvmChecker(input_files):
		exit()

	print ' Pass input file checks, starting to '+ MERGER_MODE + ' merger...'
	print 'MERGER_MODE: %s' %(MERGER_MODE)
	print 'BT_CNT: %d; FM_CNT %d' %(BT_CNT, FM_CNT)
	if MERGER_MODE == BIN_MODE:
		ofname = DEFAULT_FILE_OUTPUT + '.bin'
		if output_file[-3:] == 'bin':
			ofname = output_file
		elif output_file[-3:] == 'nvm':
			TRANS_MODE = True
		else:
			print ' No valid output file name specified, using default one...'

		m = open(ofname, 'w+b')
		bin2list(input_files, list_input_bt, list_input_fm)
		#for bnvm in list_input_bt:
		#	bnvm.printall()

		print 'BTFM_MODE: %r' %(BTFM_MODE)
		if BTFM_MODE:
			#pass
			bt_list_output = mergelists(list_input_bt)
			fm_list_output = mergelists(list_input_fm)
			print '~~~'
			#for bnvm in bt_list_output:
			#	bnvm.printall()
			#return
			#for fnvm in fm_list_output:
			#	fnvm.printall()
			#return
			complete_dic = { 
					NVM_TLV_VERSION_BT: bt_list_output,
					NVM_TLV_VERSION_FM: fm_list_output
					}
			list2bin_(complete_dic, m)		
		else:
			# BT-only or FM-only merger
			if BT_CNT > 0: 
				
				bt_list_output = mergelists(list_input_bt)	
				complete_dic = { 
					NVM_TLV_VERSION_BT: bt_list_output
					}
				list2bin_(complete_dic, m)		
			if FM_CNT > 0: 
				fm_list_output = mergelists(list_input_fm)	
				complete_dic = { 
					NVM_TLV_VERSION_FM: fm_list_output
					}
				list2bin_(complete_dic, m)		
		m.close()
	elif MERGER_MODE == NVM_MODE:
		ofname = DEFAULT_FILE_OUTPUT + '.nvm'
		if output_file[-3:] == 'nvm':
			ofname = output_file
		elif output_file[-3:] == 'bin':
			TRANS_MODE = True
		else:
			print ' No valid output file name specified, using default one...'
			
		m = open(ofname, 'w+')
		# TBD
		if BTFM_MODE:
			print '?' * 10
			print 'BT_CNT: %d' %BT_CNT
			print 'FM_CNT: %d' %FM_CNT
			# this won't merge into one NVM file, since it's not possible
			# only merge BT NVMs into one, FM NVMs into one
			pass
		else:
			if BT_CNT > 0:
				nvm2list(input_files[1], list_input_bt)
				bt_list_output = mergelists(list_input_bt)	
				writeHeaderToFile(m)
				list2NVMfile(bt_list_output, m)
			elif FM_CNT > 0:
				nvm2list(input_files[1], list_input_fm)
				fm_list_output = mergelists(list_input_fm)	
				writeHeaderToFile(m)
				list2NVMfile(fm_list_output, m)
			elif FM_CNT == 0 or BT_CNT == 0:
				non_spec_list = []
				nvm2list(input_files, non_spec_list)	
				non_spec_list_output = mergelists(non_spec_list)
				writeHeaderToFile(m)
				list2NVMfile(non_spec_list_output, m)
		m.close()

	if TRANS_MODE:
		print 'TRANS_MODE: %r' %TRANS_MODE
		try:
			if output_file[-3:] == 'nvm':
			# BIN -> NVM
					with open(output_file, 'w+') as m:
						writeHeaderToFile(m)
						if BTFM_MODE:
							pass
						else:
							if BT_CNT > 0:
								list2NVMfile(bt_list_output, m)
							if FM_CNT > 0:
								list2NVMfile(fm_list_output, m)
						m.close()
			else:
			# NVM -> BIN
					with open(output_file, 'w+b') as m:
						if BTFM_MODE:
							pass
						else:
							if BT_CNT > 0:
								complete_dic = {
									NVM_TLV_VERSION_BT: bt_list_output
								}
								list2bin_(complete_dic, m)
							if FM_CNT > 0:
								complete_dic = {
									NVM_TLV_VERSION_FM: fm_list_output
								}
								list2bin_(complete_dic, m)
						m.close()
		except IOError:
			print ' Cannot open \"' + output_file + '\"\n'

	print '\n\tMerge completes\n'


nvmMerger()