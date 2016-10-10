# nvmMerger
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
