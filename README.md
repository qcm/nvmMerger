# nvmMerger
## Description
nvmMerger will merge multiple bin/text formated NVM files into one. If there are
duplicated NVM tags, the second file's NVM will replace the first ones.

usage: nvmMerger.py [-h] [-o output_file] input_files [input_files ...]

## NVM Format
* First 4 bytes are irrelevant for BT SoC settings
* Every tag contains four fields:
	a. TagNum: 2 bytes
	b. TagLength: 2 bytes
	c. 8 bytes zero padding after TagLength
	d. TagValue: depends on TagLength
* TagClass naming:
	a. TagLengthMSB
	b. TagLengthLSB
	c. TagLength = (TagLengthMSB << 8) + TagLengthLSB
	d. *.nvm is little-endian based, so we'll see:
		[TagNumLSB, TagNumMSB] [TagLengthLSB, TagLengthMSB] 0x00 ... 0x00 [TagValue]
