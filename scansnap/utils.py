import logging
import os
import subprocess
import threading
import re
import secrets
import zipfile

class Settings:

    # If True, uses the fake scanimage command for testing,
    # i.e. does not use a real scanner device.
    test_mode = True

    # TODO: find a way to execute scanimage without sudo
    # On a Ubuntu 18.04 LTS PC (a small fanless box) that I have,
    # sudo is required to execute the scanimage command, so I
    # (reluctantly) added this option.
    # On a laptop running 16.04, this is not necessary.
    sudo_scanimage = True

class EventListenerBase:
    def on_state_changed(self,data):
        logging.info(data)

    def on_progress_updated(self,data):
        logging.info(data)

event_listener = EventListenerBase()

def set_event_listener(listener):
    global event_listener
    event_listener = listener

def save_scanned_images_as_zip_file(img_files_dir, zip_file_path):
    with zipfile.ZipFile(zip_file_path, 'w') as pages_zip:
        # There should only be *.jpg files in the output_dir at this moment
        for f in os.listdir(img_files_dir):
            pages_zip.write(f)

def parse_stdout(stdout_lines):
    for line in stdout_lines:
        #line = line.decode('utf-8')
        logging.info('stdout: {}'.format(line))

def parse_stderr_and_send_events(stderr_lines):
    global event_listener
    scan_complete = False
    for line in stderr_lines:
        logging.info('scan stderr: {}'.format(line))

        if line.startswith('Scanned page '):
            m = re.search('(?<=Scanned page )\d+', line)
            page = m.group(0)
            event_listener.on_progress_updated({'scanned_page': page})
        elif re.match('Batch terminated, \d+ page(s)? scanned', line):
            logging.info('Batch terminated')
            m = re.search('\d+', line)
            scanned_pages = m.group(0)
            event_listener.on_progress_updated({'last_scanned_page': scanned_pages})
            event_listener.on_state_changed({'state': 'scan_complete', 'message': 'Scan complete'})
            scan_complete = True
        else:
            logging.info('Some other stderr info')
            logging.info(line)

    return scan_complete

# 1. Reads the stdout of the scanimage command and reports the status
#    to the event listener, e.g. the scanner finished scanning i-th page
# 2. If the scan is a success, starts converting the scanned image files into a PDF file.
def scan_and_convert_process_main_loop(
    process,
    output_dir,
    output_dir_url,
    output_pdf_filename,
    save_images_as_zip
    ):

    global event_listener

    scan_result = ''
    while(True):

        parse_stdout(process.stdout)

        # stderr
        scan_complete = parse_stderr_and_send_events(process.stderr)
        if scan_complete:
            scan_result = 'success'

        logging.info('Polling')
        rc = process.poll()
        if rc is None:
            pass # None indicates the process has NOT been terminated
        else:
            logging.info('scanimage process returncode: {}'.format(rc))
            process.stdout.close()
            break

    #event_listener.on_progress_updated('scan process terminated')
    if scan_result == 'success':
        logging.info('Document scan complete')

        if save_images_as_zip:
            event_listener.on_state_changed({'state': 'compressing', 'message': 'Compressing image files...'})
            jpg_files_zip_pathname = os.path.join(output_dir,'pages_jpg.zip')
            save_scanned_images_as_zip_file(output_dir, jpg_files_zip_pathname)

        if 0 < len(output_pdf_filename):
            event_listener.on_state_changed({'state': 'converting', 'message': 'Converting image files into a PDF file...'})

            # A pathname of the output PDF file
            output_pdf_pathname = os.path.join(output_dir, output_pdf_filename)
            logging.info('output_pdf_pathname: {}'.format(output_pdf_pathname))

            # output_dir starts with 'static' without the leading forward slash
            # Run the convert command asynchronously and monitor the stdout

            download_pdf_url = output_dir_url + '/' + output_pdf_filename
            logging.info('download_pdf_url: {}'.format(download_pdf_url))
                

            convert_process = convert_images_to_pdf(output_dir, output_pdf_pathname)
            t = threading.Thread(target=convert_process_main_loop,
                kwargs={'process': convert_process, 'output_pdf_pathname': output_pdf_pathname, 'download_pdf_url': download_pdf_url})
            t.start()
    else:
        logging.info('scan_result!=success')

def get_file_size_in_mb(pathname):
    return os.stat(pathname).st_size / 1000.0 / 1000.0

def convert_process_main_loop(process, output_pdf_pathname, download_pdf_url):
    while(True):

        rc = process.poll()
        if rc is None:
            # rc is None: the process has NOT been terminated.
            pass
        else:
            logging.info('conversion returncode: {}'.format(rc))
            if rc == 0:
                logging.info('download_pdf_url: {}'.format(download_pdf_url))
                pdf_file_size = get_file_size_in_mb(output_pdf_pathname)
                event_listener.on_state_changed({
                    'state': 'conversion_complete', 
                    'download_pdf_url': download_pdf_url,
                    'pdf_file_size': pdf_file_size})

                #create_zip_of_scanned_pages()

            event_listener.on_state_changed({'state': 'conversion_process_terminated', 'message': ''})
            break # Process has been terminated

# Executes the shell command to convert multiple jpg images into a single PDF file and returns (async)
def convert_images_to_pdf(image_files_dir, output_pdf_pathname):
    image_files_list = subprocess.check_output(['ls {}'.format(os.path.join(image_files_dir,'*.jpg'))], shell=True)
    convert_cmd = ['convert']
    convert_cmd += image_files_list.decode('utf-8').split()
    convert_cmd += [output_pdf_pathname]
    logging.info('convert_cmd: {}'.format(convert_cmd))
    p = subprocess.Popen(convert_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in p.stderr:
        logging.info('convert stderr:',line)
    return p

# Executes the scanimage command asynchronously and returns the process object
# - This function should return fairly quickly as it does not wait until the scanimage command to complete the scan.
# - output_dir: Directory path on the filesystem where pdf, zipped jpg, and individual jpg files are to be saved
def scan_papers(paper_size='a4-portrait', resolution=200, sides='front', color_mode='color',
                output_dir='.', 
                output_pdf_filename='out.pdf',
                save_images_as_zip=False):

    cmd = []

    if Settings.test_mode:
        cmd += ['./scanimage_test.py']
    else:
        cmd += ['scanimage']

    # Add the '-p' option to display the progress
    cmd += ['-p']

    # Page width and height (unit: mm)
    w, h = 215, 297 # Unsupported paper size will fall back on A4 portrait
    if paper_size == 'a4-portrait':
        w, h = 215, 297
    elif paper_size == 'a5-portrait':
        w, h = 150, 215

    cmd += ['--page-width', str(w), '--page-height', str(h)]

    # Resolution
    cmd += ['--resolution={}'.format(resolution)]

    # Color mode
    mode = 'Gray' if color_mode == 'grayscale' else 'Color'
    cmd += ['--mode', mode]

    # Set the output image format
    cmd += ['--format', 'jpeg']

    #output_dir = os.path.join(base_output_dir, secrets.token_hex(8))
    #output_dir = base_output_dir + '/' + secrets.token_hex(8)
    logging.info('output_dir: {}'.format(output_dir))

    # Turn on the batch mode option
    cmd += ['--batch={}'.format(os.path.join(output_dir,'out%03d.jpg'))]

    # front side only or duplex (front & back)
    source = 'ADF Front' if sides == 'front' else 'ADF Duplex'
    cmd += ['--source', source]

    if Settings.sudo_scanimage:
        cmd.insert(0, 'sudo') # Prepend the command with 'sudo'

    logging.info('cmd: {}'.format(cmd))

    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        logging.info('scanimage threw an error: {}, {}'.format(e.returncode,e.output))
        event_listener.on_state_changed({'state', 'scan_failed', 'message', 'Scan failed'})

    return p

def scan_and_save_results(
    paper_size='a4-portrait',
    resolution=200,
    sides='front',
    color_mode='color',
    output_dir='.',
    output_dir_url='',
    output_pdf_filename='out.pdf',
    save_images_as_zip=False
    ):

    # This executes the scanimage command and returns without
    # waiting for the command to finish
    p = scan_papers(
        paper_size=paper_size,
        resolution=resolution,
        sides=sides,
        color_mode=color_mode,
        output_dir=output_dir,
        output_pdf_filename=output_pdf_filename,
        save_images_as_zip=False
        )

    t = threading.Thread(
        target=scan_and_convert_process_main_loop,
        kwargs={
            'process': p,
            'output_dir': output_dir,
            'output_dir_url': output_dir_url,
            'output_pdf_filename': output_pdf_filename,
            'save_images_as_zip': save_images_as_zip
            })

    t.start()

def get_scanner_info_sync():

    try:
        cmd = ['scanimage', '-L']

        if Settings.sudo_scanimage:
            cmd.insert(0, 'sudo') # Prepend the command with 'sudo'

        logging.info('scanner check cmd: {}'.format(cmd))

        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf8')

        if(0 <= out.find('No scanners were identified.')):
            return {'scanner_found': False}
        else:
            # Example stdout when a scanner was found:
            # device `fujitsu:ScanSnap iX500:1508641' is a FUJITSU ScanSnap iX500 scanner
            m = re.search("' is a .+scanner$", out)

            # Note that in Python's ternary expression, the condition
            # is evaluated first, so the statement below does not throw
            # an exception even when m is None
            scanner_name = m.group(0)[7:-8] if m is not None else "Couldn't get the scanner name"
            return {'scanner_found': True, 'scanner_name': scanner_name}

    except subprocess.CalledProcessError:
        print('CalledProcessError')

    return {'scanner_found': False}
