#!/usr/bin/env python

# To test this script, execute this:
# ./scanimage_test.py --page-width 12 --batch=./aaa/out%02d.png

import re
import sys
import time
import argparse
from PIL import Image

# Oddly enough, scanimage prints seemingly non-error message to stderr
def print_to_stderr(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

parser = argparse.ArgumentParser()
parser.add_argument('-L', '--list-devices', action='store_true')
parser.add_argument('--batch')
parser.add_argument('--mode')
parser.add_argument('--format')
parser.add_argument('--source')
parser.add_argument('--resolution')
parser.add_argument('--page-width')
parser.add_argument('--page-height')
parser.add_argument('--brightness')
parser.add_argument('--buffer-size')
parser.add_argument('-p', action='store_true')
# print('sys.argv[1:]',sys.argv[1:])
args = parser.parse_args(sys.argv[1:])

if args.list_devices:
    print("device `tabby:meowscan M1000:1234560' is a TABBY meowscan M1000 scanner")
    exit(0)

print(args)
print('batch:',args.batch)
print('page width & height:', args.page_width, args.page_height)
print('mode:',args.mode)
print('source:',args.source)
#print(sys.argv[1:])

print('Scanning infinity pages, incrementing by 1, numbering from 1')

# Get the output directory argument value
output_fmt_str=args.batch

img = Image.new('RGB', (256,256))
num_pages = 5
for i in range(1,num_pages+1):
    print('Scanning page {}'.format(i))
    print_to_stderr('Scanned page {}. (scanner status = 5)'.format(i))
    # filename = 'out{}.png'.format(str(i).zfill(3))
    # img_path = os.path.join(output_dir,filename)
    # Only support integer format strings, e.g. '%d', '%0Nd'
    if output_fmt_str and re.search("%\\d+d", output_fmt_str):
        img_path = output_fmt_str % (i)
    else:
        img_path = output_fmt_str
    print(img_path)
    if img_path:
        img.save(img_path)
    time.sleep(1.0)

print('scanimage: sane_start: Document feeder out of documents')
print_to_stderr('Batch terminated, {} pages scanned'.format(num_pages))
