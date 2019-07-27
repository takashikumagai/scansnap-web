#!/usr/bin/env python3

# To test this script, execute this:
# ./scanimage_test.py --page-width 12 --batch=./aaa/out%02d.png

import os
import sys
import time
import argparse
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('--batch')
parser.add_argument('--mode')
parser.add_argument('--format')
parser.add_argument('--source')
parser.add_argument('--resolution')
parser.add_argument('--page-width')
parser.add_argument('--page-height')
parser.add_argument('-p', action='store_true')
print('sys.argv[1:]',sys.argv[1:])
args = parser.parse_args(sys.argv[1:])
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
    print('Scanned page {}. (scanner status = 5)'.format(i))
    # filename = 'out{}.png'.format(str(i).zfill(3))
    # img_path = os.path.join(output_dir,filename)
    img_path = output_fmt_str % (i)
    print(img_path)
    img.save(img_path)
    time.sleep(1.0)

print('scanimage: sane_start: Document feeder out of documents')
print('Batch terminated, {} pages scanned'.format(num_pages))
