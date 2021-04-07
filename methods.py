'''
Programmer:     Fernando Rodriguez
Program Name:   Lab 2
File Name:      methods.py
Description:    Program prints volume specification, exports file allocation tables, and retrieves files
'''

import sys

# returns Volume infomation as dictionary
def getVolumeInformation(in_file):
    volume_information = {}

    # skip code and seek to start position
    in_file.seek(3)
    
    volume_information["OS Name"] = in_file.read(8).decode()
    volume_information["Bytes per sector"] = int.from_bytes(in_file.read(2), "little")
    volume_information["Sector per cluster"] = int.from_bytes(in_file.read(1), "little")
    volume_information["Reserved sectors"] = int.from_bytes(in_file.read(2), "little")
    volume_information["Number of FAT copies"] = int.from_bytes(in_file.read(1), "little")
    volume_information["Number of possible root entries"] = int.from_bytes(in_file.read(2), "little")
    volume_information["Small number of sectors"] = int.from_bytes(in_file.read(2), "little")
    volume_information["Media Descriptor"] = in_file.read(1).hex() 
    volume_information["Sectors per FAT"] = int.from_bytes(in_file.read(2), "little")
    volume_information["Sectors per Track"] = int.from_bytes(in_file.read(2), "little")
    volume_information["Number of Heads"] = int.from_bytes(in_file.read(2), "little")
    volume_information["Hidden Sectors"] = int.from_bytes(in_file.read(4), "little")
    volume_information["Large number of sectors"] = int.from_bytes(in_file.read(4), "little")
    volume_information["Drive Number"] = int.from_bytes(in_file.read(1), "little")
    volume_information["Reserved"] = int.from_bytes(in_file.read(1), "little")

    extend_boot_signature = in_file.read(1)
    volume_information["Extended Boot Signature"] = extend_boot_signature.hex() + "h"

    # validate extended boot signature is equal to 29h; if true store next three 
    if int.from_bytes(extend_boot_signature, "little") == 41:
        volume_information["Volume Serial Number"] = in_file.read(4).hex()
        # check if volume label is empty; if so set as NO_NAME
        volume_label = in_file.read(11).decode()
        if volume_label.strip() == "":
                    volume_information["Volume Label"] = "NO_NAME"
        else:
            volume_information["Volume Label"] = volume_label   # else what is in it
        volume_information["File System Type"] = in_file.read(8).decode()
    else:
        in_file.seek(62)    # skip data if extended boot sig != 29h
    volume_information["Bootstrap code"] = hex(int.from_bytes(in_file.read(448), "little"))
    volume_information["Boot sector signature"] = in_file.read(2).hex() 

    # return dictionary
    return volume_information

# formats a string; used for exporting the fat table
def format(s):
    n = 2   # number of characters per split
    sl = [s[i:i+n] for i in range(0, len(s), n)] # split string
    result = " ".join(sl) # join string w/ space
    return result

# reads the fat16 tables; "w": writes the fat16 tables to disk; "r": returns one copy of a fat16 table
def readFAT(in_file, flag):
    volume = getVolumeInformation(in_file)  # retrieve volume information/specifications
    number_of_fat = volume["Number of FAT copies"]
    reserved_region = 0
    reserved_sectors = volume["Reserved sectors"]
    fat_region_start = reserved_region + reserved_sectors # protrayed as a sector, so 1 = 512 bytes

    # move to FAT start
    current_location = in_file.seek(fat_region_start * volume["Bytes per sector"])
    fat_size = volume["Bytes per sector"] * volume["Sectors per FAT"]
    iterations = int(fat_size/16)   # determines how many times we need to loop due to printing 16 bytes at a time

    # write fat to file
    if flag == "w":
        print(number_of_fat, "FAT copies found")
        # write n fat files; n = number of fat copies
        for i in range(1, number_of_fat + 1):
            out_file = open("FAT" + str(i) + ".txt", "w")   # open fat table n
            for x in range(0, iterations):  # iterate x times
                # read line of bytes and print
                line = in_file.read(16).hex()
                out_file.write(hex(current_location) + "|\t" + format(line) + "\n")
                # increment location
                current_location += 16
            out_file.close()
            print("FAT" + str(i) + ".txt created")
    # return fat in case it's needed; needed when retrieving files
    elif flag == "r":
        fat = in_file.read(fat_size) 
        n = 2   # number of characters per split
        fat_list = [fat[i:i+n] for i in range(0, len(fat), n)] # split string
        for x in range(0, len(fat_list)):
            position = int.from_bytes(fat_list[x], "little")
            fat_list[x] = position
        return fat_list # fat16 table is returned as a list with indecies

# recovers files from root directory using fat16 table; accounts for slack space and deleted files
def recoverFiles(in_file):
    volume = getVolumeInformation(in_file)  # get volume information
    reserved_region = 0
    reserved_sectors = volume["Reserved sectors"]
    fat_region_start = reserved_region + reserved_sectors   # protrayed as a sector/cluster?, so 1 = 512 bytes
    number_of_fats = volume["Number of FAT copies"]
    sectors_per_fat = volume["Sectors per FAT"]
    bytes_per_sector = volume["Bytes per sector"]
   
    # calculate root start
    root_directory_start = (fat_region_start + (number_of_fats * sectors_per_fat)) * bytes_per_sector

    # calculate data region start in bytes
    data_region_start = int(root_directory_start + (volume["Number of possible root entries"] * 32))

    # stores fat table for reading
    fat = readFAT(in_file, "r")

    # seek to start of root
    in_file.seek(root_directory_start)

    # initialize variables
    hex_list = [""] # contains a directory entry as a list of bytes in hex
    dir_offset = 0  # offset for reading directory info; used to continue reading data
    file_name = ""
    extension = ""  # file extension if it has one
    file_size = 0

    # search directory for entries
    while True:
        # seek to start of root directory
        in_file.seek(root_directory_start + dir_offset)

        # skips a portion of data; found 32 byte entry before each file
        in_file.read(32)    # TODO fix hacky skip
        dir_offset += 32    # skip metadata?

        entry = in_file.read(32).hex()  # directory is stores as hex
        dir_offset += 32    # account for entry read
        n = 2   # number of characters per split
        hex_list = [entry[i:i+n] for i in range(0, len(entry), n)]  # split string; stores entry as list of two pair bytes in hex

        # condition to quit file search
        if hex_list[0] == "00":
            break
        # if deleted file is found
        elif hex_list[0] == "e5":
            file_name = bytes.fromhex(entry[2:16]).decode()
            extension = bytes.fromhex(entry[16:22]).decode()
            starting_cluster = int.from_bytes(bytes.fromhex(entry[52:56]), "little") # store starting cluster
            file_size = int.from_bytes(bytes.fromhex(entry[56:64]), "little") # store file size
            print("!" + file_name.strip() + "." + extension.strip() + " (Deleted)")
            # print("\t", starting_cluster, file_size)
        # if normal file is found
        else:
            file_name = bytes.fromhex(entry[0:16]).decode()
            extension = bytes.fromhex(entry[16:22]).decode()
            starting_cluster = int.from_bytes(bytes.fromhex(entry[52:56]), "little") # store starting cluster
            file_size = int.from_bytes(bytes.fromhex(entry[56:64]), "little")

        in_file.seek(data_region_start + (starting_cluster - 2) * bytes_per_sector) # move to data region

        # check if extension exists; if so append to file name
        if extension.strip() == "":
            full_file_name = file_name.strip()
        else:
            full_file_name = file_name.strip() + "." + extension.strip()

        # open file to write
        out_file = open(full_file_name, "wb")

        # init variables for later use
        bytes_written = 0   # tracks the amount of bytes written to a single file
        bytes_needed = file_size    # tracks how many bytes need to be written
        leftovers = 0   # tracks any leftover bytes
        sectors_used = 0    # tracks how many cluster/sectors were used
        next_cluster = fat[starting_cluster]    # contains the value of the starting cluster (1 cluster = 1 sector in our case)
        current_cluster = starting_cluster  # keeps track of the current cluster during seeks

        # loop to write files
        while True:
            if fat[current_cluster] != 65535: # write 512 bytes
                in_file.seek(data_region_start + (current_cluster - 2) * bytes_per_sector) # move to data region
                raw_data = in_file.read(bytes_per_sector)
                out_file.write(raw_data)
                bytes_written += bytes_per_sector
                # print("\t", full_file_name, "wrote", bytes_written)
                bytes_needed = file_size - bytes_written
                sectors_used += 1
                if next_cluster == 0:
                    break
                else:
                    next_cluster = fat[current_cluster]
                    # print("\t", full_file_name, "next", next_cluster)
                    current_cluster = next_cluster
            elif fat[current_cluster] == 65535: # write remaining bytes
                in_file.seek(data_region_start + (current_cluster - 2) * bytes_per_sector) # move to data region
                raw_data = in_file.read(bytes_needed)
                out_file.write(raw_data)
                bytes_written += bytes_needed
                # print("\t",full_file_name, "wrote", bytes_written)
                sectors_used += 1
                leftovers = (sectors_used * bytes_per_sector) - bytes_written   # calculate leftover bytes
                break

        # close file and print acknowledgement of file
        out_file.close()
        print(full_file_name)
        # print("\t", starting_cluster, file_size)

        # write file slack if it exists
        if leftovers > 0:
            raw_data = in_file.read(leftovers)
            if not int.from_bytes(raw_data, "little") == 0:
                out_file = open(full_file_name + ".FileSlack", "wb")
                out_file.write(raw_data)
                out_file.close()
                print(full_file_name + ".FileSlack")