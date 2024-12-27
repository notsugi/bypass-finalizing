#!/usr/bin/env python3
import sys
from struct import pack, unpack

SECTOR_SIZE = 2048
LSN_MIT_RW_ZN = 0xa00
LSN_START_PARTITION = 0xb00

def copyFileStructure(isoIn, isoOut, fileStructureTable):
    isoOut.seek(LSN_START_PARTITION*SECTOR_SIZE)
    for lsn in fileStructureTable:
        if lsn == 0:
            break
        isoIn.seek(lsn*SECTOR_SIZE)
        # copy 0x10 sectors
        isoOut.write(isoIn.read(0x10*SECTOR_SIZE))

def copyVolumeInfo(isoIn, isoOut, volumeInfoTable):
    isoOut.seek(0)
    for lsn in volumeInfoTable:
        isoIn.seek(lsn*SECTOR_SIZE)
        # copy 0x10 sectors
        isoOut.write(isoIn.read(0x10*SECTOR_SIZE))

def copyPartition(isoIn, isoOut, discSize):
    isoIn.seek(LSN_START_PARTITION*SECTOR_SIZE)
    isoOut.seek(LSN_START_PARTITION*SECTOR_SIZE)
    copied = LSN_START_PARTITION
    while True:
        if copied == discSize:
            break
        sector = isoIn.read(SECTOR_SIZE)
        isoOut.write(sector)
        copied += 1

def processMIT_MTFtable(isoIn, tableLoc):
    isoIn.seek((tableLoc+1)*SECTOR_SIZE)
    MIT_MTF = isoIn.read(SECTOR_SIZE)
    table = MIT_MTF[:0x44]
    volumeInfoTable = [0x7fffffff & unpack('>I', table[i*4:i*4+4])[0] for i in range(len(table)//4)]
    table = MIT_MTF[0x2c0:]
    fileStructureTable = [0x7fffffff & unpack('>I', table[i*4:i*4+4])[0] for i in range(len(table)//4)]
    return volumeInfoTable, fileStructureTable

def getTopInfo(isoIn):
    isoIn.seek(LSN_MIT_RW_ZN*SECTOR_SIZE)
    MIT_RW_ZN = isoIn.read(SECTOR_SIZE)
    if not MIT_RW_ZN.startswith(b'MIT_RW_ZN'):
        print('[*] MIT_RW_ZN signature not found')
        exit(1)
    finalized = MIT_RW_ZN[0x18]
    if finalized:
        reply = input('[*] This disc seems to be finalized. Continue?: ')
        if not reply.startswith('y'):
            print('[*] Abort.')
            exit(1)
    numFiles = unpack('<H', MIT_RW_ZN[0x12:0x14])[0]
    discSize = unpack('<I', MIT_RW_ZN[0x14:0x18])[0]
    tableLoc = unpack('<I', MIT_RW_ZN[0x2c:0x30])[0]
    return numFiles, discSize, tableLoc

def main(isoFileName):
    isoIn = open(isoFileName, 'rb')
    numFiles, discSize, tableLoc = getTopInfo(isoIn)
    print(f'[*] {isoFileName} contains {numFiles} files in metadata')
    print(f'[*] Disc Size: {discSize*SECTOR_SIZE} Bytes')
    volumeInfoTable, fileStructureTable = processMIT_MTFtable(isoIn, tableLoc)

    isoOut = open('fixed.iso', 'wb')
    copyPartition(isoIn, isoOut, discSize)
    copyVolumeInfo(isoIn, isoOut, volumeInfoTable)
    copyFileStructure(isoIn, isoOut, fileStructureTable)
    #addAVDP(discSize)
    
    isoIn.close()
    isoOut.close()
    exit(0)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print(f'{sys.argv[0]} <isofile>')
        exit(1)
    main(sys.argv[1])
