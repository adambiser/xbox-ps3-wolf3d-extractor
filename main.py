"""
Extracts files from the XBOX port and the wolf_ps3.dsk file from the PS3 port of Wolfenstein 3-D.

PS3 tools worth mentioning:
- PS3P PKG Ripper - to extract the dsk file for the PS3 port.
- VLC - to play MSF sound files.
"""
import argparse
import io
import os
import struct


def read_big_endian_uint32(f) -> int:
    return struct.unpack('>I', f.read(4))[0]


def read_entry_header(f):
    file = f.read(64).split(b'\x00')[0].decode()
    # Remove any prefix.
    if file.startswith("GAME:\\"):
        file = file[6:]
    offset = read_big_endian_uint32(f)
    length = read_big_endian_uint32(f)
    return file, offset, length


def read_file_header(f):
    number_of_entries = read_big_endian_uint32(f)
    print(f"Number of entries: {number_of_entries}")
    entry_headers = []
    for index in range(number_of_entries):
        header = read_entry_header(f)
        entry_headers.append(header)
        # print(header)
    read_big_endian_uint32(f)  # Total length of all data after header.  Not needed.
    return entry_headers


def extract_entries(f, entry_headers, output_path):
    start_offset = f.tell()
    for index in range(len(entry_headers)):
        entry_file, entry_offset, entry_length = entry_headers[index]
        f.seek(start_offset + entry_offset)
        print(f"Extracting '{entry_file}', offset={entry_offset:x}, length={entry_length}, tell={f.tell():x}")
        entry_data = f.read(entry_length)
        output_file = os.path.join(output_path, entry_file)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "wb") as ef:
            ef.write(entry_data)


def open_data_stream(file):
    f = open(file, "rb")
    # Check whether PS3 or XBOX file.
    is_xbox = f.read(4) == b"LIVE"
    if not is_xbox:
        return f
    print("XBOX file detected.  Reading data into a memory stream.  Entry offsets won't match file offsets.")
    # When reading an XBOX file, read it into memory, skipping the FAT lookups(?) along the way.
    f.seek(0x23D000)
    xf = io.BytesIO()
    buffer = f.read(0x7B000)
    xf.write(buffer)
    while len(buffer) > 0:
        f.seek(0x1000, os.SEEK_CUR)
        buffer = f.read(0xAA000)
        xf.write(buffer)
    f.close()
    xf.seek(0)
    return xf


def extract_files(file, output_path):
    with open_data_stream(file) as f:
        entry_headers = read_file_header(f)
        extract_entries(f, entry_headers, output_path)


def main():
    parser = argparse.ArgumentParser(description="Extracts files from the XBOX port and the wolf_ps3.dsk file from the "
                                                 "PS3 port of Wolfenstein 3-D.")
    parser.add_argument("-i", "--input", type=str, help="The path to the PS3 dsk file.", required=True)
    parser.add_argument("-o", "--outpath", type=str, help="The path to extract the data to.")
    parser.set_defaults(outpath=r".\output")
    # parser.print_help()
    args = parser.parse_args()
    extract_files(file=args.input, output_path=args.outpath)


if __name__ == '__main__':
    main()
