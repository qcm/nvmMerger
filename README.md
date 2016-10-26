# nvmMerger
## Description
nvmMerger will merge multiple bin/text formated NVM files into one. If there are
duplicated NVM tags, the second file's NVM will replace the first ones.

usage: nvmMerger.py [-h] [-o output_file] input_files [input_files ...]

## NVM Format
* First 4 bytes are irrelevant for BT SoC settings:
	1. First byte indicates the NVM file version. Now the version is '02'
	2. Second to the fourth byte represent the total file length without this 4 bytes, also little-endian
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
