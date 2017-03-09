# nvmtool
## Description
nvmtool will merge multiple bin/text formated NVM files into one. If there are
duplicated NVM tags, the second file's NVM will replace the first ones.
nvmtool can also convert format between bin and nvm text format.
If input file extension are nvm and output is bin, nvmtool will transfer file from nvm to bin.
Vice versa.

usage: nvmtool.py [-h] [-o output_file] input_files [input_files ...]

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
	* nvmtool.py intput0.bin input1.bin [...] [-o output.nvm]

* FM multiple bin merge
	* nvmtool.py intput0.bin input1.bin [...] [-o output.nvm]

* BT multiple nvm merge
	* nvmtool.py intput0.nvm input1.nvm [...] [-o output.nvm]
	* nvmtool.py --BT intput0.nvm input1.nvm [...] [-o output.nvm]

* FM multiple nvm merge
	* nvmtool.py intput0.nvm input1.nvm [...] [-o output.nvm]
	* nvmtool.py --FM intput0.nvm input1.nvm [...] [-o output.nvm]

* BT single bin->nvm conversion
	* nvmtool.py input1.bin [-o output.nvm]

* BT single nvm->bin conversion
	* nvmtool.py --BT input1.nvm [-o output.bin]

* FM single bin->nvm conversion
	* nvmtool.py input1.bin [-o output.nvm]

* FM single nvm->bin conversion
	* nvmtool.py --FM input1.nvm [-o output.bin]

* BT multiple bin->nvm conversion
	* nvmtool.py intput0.bin input1.bin [...] [-o output.nvm]

* BT multiple nvm->bin conversion
	* nvmtool.py --BT intput0.nvm input1.nvm [...] [-o output.bin]

* FM multiple bin->nvm conversion
	* nvmtool.py intput0.bin input1.bin [...] [-o output.nvm]

* FM multiple nvm->bin conversion
	* nvmtool.py --FM intput0.nvm input1.nvm [...] [-o output.bin]

* BT&&FM bin merge
	* nvmtool.py intput0.bin input1.bin [...] [-o output.bin]

* BT&&FM nvm merge
	* N/A

* BT&&FM bin->nvm conversion
	* nvmtool input0.bin [...] -s

* BT&&FM nvm->bin conversion
	* nvmtool.py --BT intput0.nvm [...] --FM input0.nvm [...] [-o output.nvm]
