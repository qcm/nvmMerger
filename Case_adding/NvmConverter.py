#!/usr/bin/python

import sys
import re
import os
from optparse import OptionParser

NVM_TLV_TYPE_VAL = 2
NVM_TLV_TYPE_POS = 0
NVM_TLV_TYPE_SIZE = 1

NVM_TLV_LENGTH_POS = 1
NVM_TLV_LENGTH_SIZE = 3

NVM_TLV_DATA_START = 4
NVM_TLV_TAG_ID_SIZE = 2
NVM_TLV_TAG_LEN_SIZE = 2
NVM_TLV_TAG_PTR_SIZE = 4
NVM_TLV_TAG_EXTFLG_SIZE = 4

#This function writes the number of bytes provided in the argument by converting 
#the decimal value to hex value in little endian format.
def WriteDec2hex (fobj, value, num_bytes):
    while (num_bytes > 0):
        fobj.write(chr(value%256))
        value /= 256
        num_bytes -= 1

#This function splits the hex string and writes the data as hex values
def WriteHexString (fobj, hexStr):
    hexlist = hexStr.split( )
    for hexValStr in hexlist:
        intValue = int(hexValStr, 16)
        fobj.write(chr(intValue))


#------------------------------------------------------------------------------
# Parse command line arguments
#------------------------------------------------------------------------------
def parse_args():
   usage = "usage: NvmConverter.py -i <.nvm file> -o <.bin file>"
   version = "NvmConverter.py 1.0"
   
   parser = OptionParser(usage=usage, version=version)
   parser.add_option("-i", "--input", dest="inputfile_nvm",
                  help="Read the file in .nvm format", metavar="FILE")
   parser.add_option("-o", "--output", dest="outputfile_bin",
                  help="Write output to FILE in TLV format", metavar="FILE")
          
   (options, args) = parser.parse_args()
   #print options.inputfile_nvm
   #print options.outputfile_bin
   if options.inputfile_nvm is None:
      parser.error("-i option must be defined")
      sys.exit(2)
                  
   if options.outputfile_bin is None:
      parser.error("-O option must be defined")
      sys.exit(2)                  
                  
   return (options, args)

#------------------------------------------------------------------------------
#Main function which parses the input nvm file and output the binary file
#------------------------------------------------------------------------------
def NvmConverter():

    (options, args) = parse_args()

    nvm_obj = open(options.inputfile_nvm, "r")
    bin_obj = open(options.outputfile_bin, "wb")

    #Write the NVM TLV Type 
    WriteDec2hex(bin_obj, NVM_TLV_TYPE_VAL, NVM_TLV_TYPE_SIZE)
    #bin_obj.write(chr(NVM_TLV_TYPE_VAL))

    #Write the Dummy Length initially
    WriteDec2hex(bin_obj, 0, NVM_TLV_LENGTH_SIZE)

    for line in nvm_obj:
        if re.match("\[Tag\]", line):
            #Get the number of Tags
            str = nvm_obj.next()
            NumOfTags = re.sub("^Num = ", '', str)
            #print "No of Tags: ", NumOfTags

        elif re.match("\[Tag[0-9]", line):
            #Write Tag ID
            str = nvm_obj.next()
            TagNum = re.sub("^TagNum = ", '', str)
            WriteDec2hex(bin_obj, int(TagNum), NVM_TLV_TAG_ID_SIZE)

            #Write Tag Length
            str = nvm_obj.next()
            TagLength = re.sub("^TagLength = ", '', str)
            WriteDec2hex(bin_obj, int(TagLength), NVM_TLV_TAG_LEN_SIZE)

            #Write Tag Ptr value which is 0 as of now
            WriteDec2hex(bin_obj, 0, NVM_TLV_TAG_PTR_SIZE)

            #Write Tag Ext Flag value is 0 as of now
            WriteDec2hex(bin_obj, 0, NVM_TLV_TAG_EXTFLG_SIZE)

            #Write Tag Data
            str = nvm_obj.next()
            TagValue = re.sub("^TagValue = ", '', str)
            WriteHexString(bin_obj, TagValue)

            
    NvmLength =  int(bin_obj.tell()) - 4
    bin_obj.seek(NVM_TLV_LENGTH_POS)
    WriteDec2hex(bin_obj, NvmLength, NVM_TLV_LENGTH_SIZE)

    nvm_obj.close()
    bin_obj.close()
    return None

NvmConverter()

