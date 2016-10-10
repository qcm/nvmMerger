#!/usr/bin/python
import argparse

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
	
def nvmMerger():
	args = optParser()
	m = open(args.m, 'w+b')
	f = open(args.f, 'rb+')
	#f.readline()
	#m.write(f.readline())
	for line in f:
		print line
	


#class NVMTag:
	
nvmMerger()
