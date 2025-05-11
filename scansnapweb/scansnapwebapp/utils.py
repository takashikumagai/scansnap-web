import logging
import os
import subprocess
import zipfile
from pathlib import Path

from PIL import Image


def get_file_size_in_bytes(pathname):
    return os.stat(pathname).st_size


def save_scanned_images_as_zip_file(img_files_dir, zip_file_path, arc_dir):
    with zipfile.ZipFile(zip_file_path, 'w') as pages_zip:
        # There should only be *.jpg files in the output_dir at this moment
        for f in os.listdir(img_files_dir):
            if f.endswith('.jpg'):
                pages_zip.write(filename=os.path.join(img_files_dir,f), arcname=f'{arc_dir}/{f}')


def parse_stdout(stdout_lines):
    for line in stdout_lines:
        #line = line.decode('utf-8')
        logging.info(f'stdout: {line}')


def rotate_image_and_save(image_path,degrees_to_rotate):
    rotated = None
    rotated_image_path = ''
    with Image.open(image_path) as img:
        src_img_dpi = img.info['dpi']
        rotated = img.rotate(degrees_to_rotate, expand=1)
        rotated_image_path = image_path + '-rotated.jpg'
        rotated.save(rotated_image_path, dpi=src_img_dpi)

    subprocess.check_output(['mv', '-f', rotated_image_path, image_path])

    # Just doing this outside the context manager worked on laptop (Ubuntu 16.04)
    # But does not work on the Linux box (Buster)
    #rotated.save(image_path)
