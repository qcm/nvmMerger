#!/usr/bin/python
import argparse
import binascii

NVM_TLV_DATA_START = 4
NVM_TLV_ZERO_PADDING = 8

# create lists stores whole bin file
list_f = []
list_s = []

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
	
	def inputval(self, fobj):
		iLSB = int(binascii.b2a_hex(self.TagLengthLSB), 16)
		iMSB = int(binascii.b2a_hex(self.TagLengthMSB), 16)
		self.length = iLSB + iMSB*16
		#print num
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

# populate all nvms into the list
def bin2list(fobj, nvm_list):
	# Move cursor to where data starts
	fobj.seek(NVM_TLV_DATA_START)
	for i in range(3):
		nvm_list.append(
			NVMTag(i, fobj.read(1), fobj.read(1), fobj.read(1), fobj.read(1))
		)
		fobj.seek(NVM_TLV_ZERO_PADDING, 1)
		nvm_list[i].inputval(fobj)
		print i
		i += 1
		#t1.printall()
	

def list2bin(nvm_list, fobj):
	for i in range(3):
		nvm = nvm_list[i]
		fobj.write(nvm.TagNumLSB)
		fobj.write(nvm.TagNumMSB)
		fobj.write(nvm.TagLengthLSB)
		fobj.write(nvm.TagLengthMSB)
		for j in range(NVM_TLV_ZERO_PADDING):
			fobj.write(b'\x00')
			j += 1
		for j in range(nvm.length):
			fobj.write(nvm.TagValue[j])

def nvmMerger():
	args = optParser()
	m = open(args.m, 'w+b')
	f = open(args.f, 'rb+')
	s = open(args.s, 'rb+')
	#f.readline()
	#m.write(f.readline())
	#for line in f:
	#	print line
	#
	#i = int.from_bytes(f.read(1), byteorder='big') # only valid in Python3
	bin2list(f, list_f)
	list2bin(list_f, m)

	m.close()
	f.close()

nvmMerger()
