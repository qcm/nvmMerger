# nvmMerger
## Description
nvmMerger will merge multiple bin/text formated NVM files into one. If there are
duplicated NVM tags, the second file's NVM will replace the first ones.

usage: nvmMerger.py [-h] [-o output_file] input_files [input_files ...]

## NVM Format
* First 4 bytes are irrelevant for BT SoC settings
* Every tag contains four fields:
	1. TagNum: 2 bytes
	2. TagLength: 2 bytes
	3. 8 bytes zero padding after TagLength
	4. TagValue: depends on TagLength
* TagClass naming:
	1. `TagLengthMSB`
	2. `TagLengthLSB`
	3. `TagLength = (TagLengthMSB << 8) + TagLengthLSB`
	4. *.nvm is little-endian based, so we'll see:
		[TagNumLSB, TagNumMSB] [TagLengthLSB, TagLengthMSB] 0x00 ... 0x00 [TagValue]
