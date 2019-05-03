from zipfile import ZipFile
import os
import re
import hashlib
import argparse
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("output", help="file to output")
parser.add_argument("base_dir", help="base directory to run the packaging in", default=["."], nargs="*")
parser.add_argument("-e", "--exclude", help="a pattern to exclude from packaging", action="append", default=[])

args = parser.parse_args()
exclude = [re.compile(i) for i in args.exclude]
base_dirs = map(lambda p: Path(p).resolve(), args.base_dir)
home = os.getcwd()

with open(f"{args.output}.log", "w") as log:
    with ZipFile(args.output, "w") as zip_file:
        for base_dir in base_dirs:
            os.chdir(base_dir.parent)
            for folder, sub_folders, file_names in os.walk(base_dir.name):
                if any((re.search(x, folder) for x in exclude)):
                    print(f"Ignoring all files in folder {folder}", file=log)
                    sub_folders.clear()
                else:
                    for file_name in file_names:
                        file = os.path.join(folder,file_name)
                        if any((re.search(x, file) for x in exclude)):
                            print(f"Ignoring file {file}", file=log)
                        else:
                            print(f"Adding file to zip {file}", file=log)
                            zip_file.write(file)

os.chdir(home)

hasher = hashlib.md5()
with open(f"{args.output}.log", "rb") as zipped_file:
    buf = zipped_file.read()
    hasher.update(buf)

print(f"{{\"status\":\"ok\", \"hash\": \"{hasher.hexdigest()}\"}}")
