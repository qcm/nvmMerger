#!/usr/bin/python
import argparse
import binascii
import os

NVM_TLV_DATA_START = 4
NVM_TLV_TAG = 2
NVM_TLV_LEN = 2
NVM_TLV_ZERO_PADDING = 8
NVM_HEADER = 0
NVM_BODY_LEN = 0
# create lists stores whole bin file
list_f = []
list_s = []
list_m = []

def optParser():
	parser = argparse.ArgumentParser(description='nvmMerger merges two NVM bin files into one')
	parser.add_argument('-f', metavar='bin1', type=str, required=True, help='First bin file, the base NVM')
	parser.add_argument('-s', metavar='bin2', type=str, required=True, help='Second bin file to add')
	parser.add_argument('-m', metavar='bin3', type=str, required=True, help='Merged bin file')
	#parser.print_help()
	
	args = parser.parse_args()
	#print args
	#print args.m
	
	return args
	
class NVMTag:
	def __init__(self, TIDX, TNL, TNB, TLL, TLM):
		self.TagIndex = TIDX
		self.TagNumLSB = TNL  
		self.TagNumMSB = TNB
		self.TagLengthLSB = TLL
		self.TagLengthMSB = TLM
		self.length = 0
		self.TagValue = []
		self.num = 0
	
	def inputval(self, fobj):
		iLSB = int(binascii.b2a_hex(self.TagLengthLSB), 16)
		iMSB = int(binascii.b2a_hex(self.TagLengthMSB), 16)
		self.length = iLSB + iMSB*16
		nLSB = int(binascii.b2a_hex(self.TagNumLSB), 16)
		nMSB = int(binascii.b2a_hex(self.TagNumMSB), 16)
		self.num = nLSB + nMSB*16
		#print self.num
		for i in range(self.length):
			x = fobj.read(1)
			self.TagValue.append(x)
			i += 1
	
	def printall(self):
		print binascii.b2a_hex(self.TagNumLSB)
		print binascii.b2a_hex(self.TagNumMSB)
		print binascii.b2a_hex(self.TagLengthLSB)
		print binascii.b2a_hex(self.TagLengthMSB)
		for i in range(self.length):
			print binascii.b2a_hex(self.TagValue[i])
			i += 1

# check if the NVM file is valid
def nvmChecker(fname, sname):
	# extract the NVM header
	with open(fname, 'rb+') as f:
		fheader = f.read(NVM_TLV_DATA_START)
		f.close()
	with open(sname, 'rb+') as s:
		sheader = s.read(NVM_TLV_DATA_START)
		s.close()
	#print binascii.b2a_hex(fheader[0])
	#print binascii.b2a_hex(sheader[0])
	# first type is the TLV type
	if fheader[0]==sheader[0]:
		print ' Note: if tags are duplicated, the second file will overwrite first one'
		print ' Pass file checks, starting to merge...'
		#print binascii.b2a_hex(fheader)
	else:
		print 'Two NVM have different headers, exit...'
		exit()

# populate all nvms into the list
def bin2list(fname, nvm_list):
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

# write the list to file
def list2bin(nvm_list, fobj):
	# fill up the NVM_HEADER
	taglen_sum = 0
	fobj.seek(NVM_TLV_DATA_START)
	for nvm in nvm_list:
		taglen_sum += (NVM_TLV_TAG + NVM_TLV_LEN + NVM_TLV_ZERO_PADDING + nvm.length)
		fobj.write(nvm.TagNumLSB)
		fobj.write(nvm.TagNumMSB)
		fobj.write(nvm.TagLengthLSB)
		fobj.write(nvm.TagLengthMSB)
		for j in range(NVM_TLV_ZERO_PADDING):
			fobj.write(b'\x00')
			j += 1
		for j in range(nvm.length):
			fobj.write(nvm.TagValue[j])
	#print taglen_sum
	tmp = hex(taglen_sum).lstrip('0x').zfill(6)
	NVM_BODY_LEN = binascii.a2b_hex(tmp[4:]) + binascii.a2b_hex(tmp[2:4]) + binascii.a2b_hex(tmp[:2])
	NVM_HEADER = b'\x02' + NVM_BODY_LEN
	#print binascii.b2a_hex(NVM_HEADER)
	fobj.seek(0)
	fobj.write(NVM_HEADER)

# merge two input lists and sort them based on Tag num
def mergelists(listf, lists):
	for nvms in reversed(lists):
		for nvmf in listf:
			if nvms.num == nvmf.num:
				listf.pop(nvmf.TagIndex)	
	listm = listf + lists
	return sorted(listm, key=lambda nvm: nvm.num)
	
# main function
def nvmMerger():
	args = optParser()
	m = open(args.m, 'w+b')
	nvmChecker(args.f, args.s)

	bin2list(args.f, list_f)
	bin2list(args.s, list_s)
	list_m = mergelists(list_f, list_s)	

	#
	list2bin(list_m, m)
	m.close()
	print ' '
	print '\tMerge completes'
	print ' '

nvmMerger()
