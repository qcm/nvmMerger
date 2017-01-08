# nvmMerger
## Description
nvmMerger will merge multiple bin/text formated NVM files into one. If there are
duplicated NVM tags, the second file's NVM will replace the first ones.
nvmMerger can also convert format between bin and nvm text format.
If input file extension are nvm and output is bin, nvmMerger will transfer file from nvm to bin.
Vice versa.

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
## Example Usage
* BT multiple bin merge
	*nvmMerger.py intput0.bin input1.bin [...] [-o output.nvm]

* FM multiple bin merge
	*nvmMerger.py intput0.bin input1.bin [...] [-o output.nvm]

* BT multiple nvm merge
	*nvmMerger.py intput0.nvm input1.nvm [...] [-o output.nvm]
	*nvmMerger.py --BT intput0.nvm input1.nvm [...] [-o output.nvm]

* FM multiple nvm merge
	*nvmMerger.py intput0.nvm input1.nvm [...] [-o output.nvm]
	*nvmMerger.py --FM intput0.nvm input1.nvm [...] [-o output.nvm]

* BT single bin->nvm conversion
	*nvmMerger.py input1.bin [-o output.nvm]

* BT single nvm->bin conversion
	*nvmMerger.py --BT input1.nvm [-o output.bin]

* FM single bin->nvm conversion
	*nvmMerger.py input1.bin [-o output.nvm]

* FM single nvm->bin conversion
	*nvmMerger.py --FM input1.nvm [-o output.bin]

* BT multiple bin->nvm conversion
	*nvmMerger.py intput0.bin input1.bin [...] [-o output.nvm]

* BT multiple nvm->bin conversion
	*nvmMerger.py --BT intput0.nvm input1.nvm [...] [-o output.bin]

* FM multiple bin->nvm conversion
	*nvmMerger.py intput0.bin input1.bin [...] [-o output.nvm]

* FM multiple nvm->bin conversion
	*nvmMerger.py --FM intput0.nvm input1.nvm [...] [-o output.bin]

* BT&&FM bin merge
	*nvmMerger.py intput0.bin input1.bin [...] [-o output.bin]

* BT&&FM nvm merge
	*N/A

* BT&&FM bin->nvm conversion
	*N/A

BT&&FM nvm->bin conversion
