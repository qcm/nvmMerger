# nvmMerger
nvmMerger will merge two bin/text formated NVM files into one. If there are
duplicated NVM tags, the second file's NVM will replace the first ones.

Usage:
    nvmMerger -f <first_file_name>.bin -s <second_file_name>.bin -m <merged_file_name>.bin
    OR
    nvmMerger -f <first_file_name>.nvm -s <second_file_name>.nvm -m <merged_file_name>.nvm

NVM Format:
1) First 4 bytes are irrelevant for BT SoC settings
2) Every tag contains four fields:
	a. TagNum: 2 bytes
	b. TagLength: 2 bytes
	c. 8 bytes zero padding after TagLength
	d. TagValue: depends on TagLength
3) TagClass naming:
	a. TagLengthMSB
	b. TagLengthLSB
	c. TagLength = (TagLengthMSB << 8) + TagLengthLSB
	d. *.nvm is little-endian based, so we'll see:
		[TagNumLSB, TagNumMSB] [TagLengthLSB, TagLengthMSB] 0x00 ... 0x00 [TagValue]
