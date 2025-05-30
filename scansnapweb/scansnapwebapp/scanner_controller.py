import datetime
import logging
import os
import subprocess
import threading
import re
import zipfile

from . import utils


logger = logging.getLogger("scansnap_web")


class Settings:

    # If True, uses the fake scanimage command for testing,
    # i.e. does not use a real scanner device.
    test_mode = False

    # TODO: find a way to execute scanimage without sudo
    # On a Ubuntu 18.04 LTS PC (a small fanless box) that I have,
    # sudo is required to execute the scanimage command, so I
    # (reluctantly) added this option.
    # On a laptop running 16.04, this is not necessary.
    sudo_scanimage = False

class EventListenerBase:
    def on_state_changed(self,data):
        logging.info(data)

    def on_progress_updated(self,data):
        logging.info(data)


# Executes the shell command to convert multiple jpg images into a single PDF file and returns (async)
# Note that this requires ImageMagick
def convert_images_to_pdf(image_files_list, output_pdf_pathname):
    convert_cmd = ['convert']
    convert_cmd += image_files_list
    convert_cmd += [output_pdf_pathname]
    logging.info(f'convert_cmd: {convert_cmd}')
    p = subprocess.Popen(convert_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in p.stderr:
        logging.info('convert stderr:',line)
    return p


class ScannerController:

    def __init__(self):
        self.event_listener = EventListenerBase()

    def parse_stderr_and_send_events(self, stderr_lines):
        #scan_complete = False
        scan_state = 'scanning'
        progress_report_count = 0
        for line in stderr_lines:
            logging.info(f'scan stderr: {line}')

            if line.startswith('Scanned page '):
                m = re.search(r"(?<=Scanned page )\d+", line)
                page = m.group(0)
                self.event_listener.on_progress_updated({'scanned_page': page})
            elif re.match(r"Batch terminated, \d+ page(s)? scanned", line):
                logging.info('Batch terminated')
                m = re.search(r"\d+", line)
                scanned_pages = m.group(0)
                self.event_listener.on_progress_updated({'last_scanned_page': scanned_pages})
                self.event_listener.on_state_changed({'state': 'scan_complete', 'message': 'Scan complete'})
                #scan_complete = True
                scan_state = 'scan_complete'
            elif re.match('Document feeder jammed', line):
                logging.info('Feeder jammed')
                self.event_listener.on_state_changed({'state': 'document_feeder_jammed', 'message': 'Document feeder jammed'})
                #scan_complete = False
                scan_state = 'feeder_jammed'
                break
            elif re.match('^Progress: ', line):
                progress_report_count += 1
                pass
            else:
                pass
                #logging.info('Some other stderr info')

        logging.info(f'progress_report_count: {progress_report_count}')
        #return scan_complete
        return scan_state

    def rotate_scanned_images(self, output_dir, rotate):
        if 0 < len(rotate):
            image_files = subprocess.check_output(
                [f"ls {os.path.join(output_dir,'*.jpg')}"], shell=True)
            image_files_list = image_files.decode('utf-8').split()
            if rotate == '90':
                for img_file_name in image_files_list:
                    img_path = os.path.join(output_dir,img_file_name)
                    utils.rotate_image_and_save(img_path,90)
            elif rotate == '0,180':
                logging.info('Rotating even-numbered pages by 180 degrees')
                # Rotate even-numbered pages
                # Used to scan booklet stapled at the top
                for img_file_name in image_files_list[1::2]:
                    img_path = os.path.join(output_dir,img_file_name)
                    utils.rotate_image_and_save(img_path,180)
            elif rotate == '90,270':
                side = 1
                for img_file_name in image_files_list:
                    img_path = os.path.join(output_dir,img_file_name)
                    deg = 90 if side == 1 else 270
                    utils.rotate_image_and_save(img_path,deg)
                    side = side * (-1)

    def get_num_scanned_pages_before_jamming(self, output_dir):
        jpg_files = [f for f in os.listdir(output_dir) if re.match(r'.+\.jpg$', f)]
        num_jpg_files = len(jpg_files)
        print(f'{num_jpg_files} JPG files have been created.')
        return num_jpg_files

    # 1. Reads the stdout of the scanimage command and reports the status
    #    to the event listener, e.g. the scanner finished scanning i-th page
    # 2. If the scan is a success, starts converting the scanned image files into a PDF file.
    def scan_and_convert_process_main_loop(
        self,
        process,
        output_dir,
        output_dir_url,
        output_page_option,
        rotate,
        output_format
        ):

        print('scan_and_convert_process_main_loop')

        scan_result = ''
        while(True):

            utils.parse_stdout(process.stdout)

            # stderr
            scan_state = self.parse_stderr_and_send_events(process.stderr)
            #if scan_state == 'scan_complete':
            #    scan_result = 'success'

            logging.info('Polling')
            rc = process.poll()
            if rc is None:
                pass # None indicates the process has NOT been terminated
            else:
                logging.info(f'scanimage process returncode: {rc}')
                process.stdout.close()
                break

        self.on_scan_process_terminated(
            scan_state,
            output_dir,
            output_dir_url,
            output_page_option,
            rotate,
            output_format
        )

    def on_scan_process_terminated(
        self,
        scan_state,
        output_dir,
        output_dir_url,
        output_page_option,
        rotate,
        output_format
        ):

        #event_listener.on_progress_updated('scan process terminated')
        #if scan_result == 'success':
        if scan_state == 'scan_complete':
            self.on_scan_complete(
                output_dir,
                output_dir_url,
                output_page_option,
                rotate,
                output_format
            )
        elif scan_state == 'feeder_jammed':
            logging.info('Unfortunately, the feeder has jammed.')
            num_scanned_pages = self.get_num_scanned_pages_before_jamming(output_dir)
        else:
            logging.info('scan_state!=success')

    def generate_pdf_from_image_files(
        self,
        output_format,
        output_dir,
        output_dir_url,
        output_page_option,
        output_filename_stem,
        images_zip_pathname):

        # Generate PDF from image files
        self.event_listener.on_state_changed({'state': 'converting', 'message': 'Converting image files into a PDF file...'})

        # A pathname of the output file (pdf or zip)
        ext = '.pdf' if output_format == 'pdf' else '.zip'
        output_file_pathname = os.path.join(output_dir, output_filename_stem + ext)
        logging.info(f'output_file_pathname: {output_file_pathname}')

        # output_dir starts with 'static' without the leading forward slash
        # Run the convert command asynchronously and monitor the stdout

        download_file_url = output_dir_url + '/' + output_filename_stem + ext
        logging.info(f'download_file_url: {download_file_url}')

        image_files_list = subprocess.check_output(
            [f"ls {os.path.join(output_dir,'*.jpg')}"],
            shell=True).decode('utf-8').split()
        if output_page_option == 'single-pdf-file':
            # PDF for review purpose (available whether the output format is
            # pdf or combined zip file of pdf and image files)
            pdf_filename = output_filename_stem + '.pdf'
            pdf_file_pathname = os.path.join(output_dir, pdf_filename)
            pdf_file_url = output_dir_url + '/' + pdf_filename

            arc_dir = output_filename_stem
            images_zip_filename = os.path.basename(images_zip_pathname)

            convert_process = convert_images_to_pdf(image_files_list, pdf_file_pathname)
            t = threading.Thread(target=self.convert_process_main_loop,
                kwargs={
                    'process': convert_process,
                    'output_format': output_format,
                    'output_dir': output_dir,
                    'output_file_pathname': output_file_pathname,
                    'arc_dir': arc_dir,

                    # These 2 args are empty string if output_format == 'pdf'
                    'images_zip_pathname': images_zip_pathname,
                    'images_zip_filename': images_zip_filename,

                    # PDF for preview; available in both output formats (pdf and pdf_and_jpeg)
                    'pdf_file_pathname': pdf_file_pathname,
                    'pdf_filename': pdf_filename,
                    'pdf_file_url': pdf_file_url,

                    'download_file_url': download_file_url
                    })
            t.start()

        elif output_page_option == 'pdf-for-each-scanned-page':
            output_pdf_pathnames = []
            for i, image_file in enumerate(image_files_list):
                pdf_filename = f'{output_filename_stem}_{str(i+1).zfill(3)}.pdf'
                pdf_file_pathname = os.path.join(output_dir, pdf_filename)
                convert_process = convert_images_to_pdf([image_file], pdf_file_pathname)
                while(True):
                    rc = convert_process.poll()
                    if rc is None:
                        # rc is None: the process has NOT been terminated.
                        pass
                    else:
                        # Process has been terminated
                        logging.info(f'PDF file {i} rc: {rc}')
                        if rc == 0:
                            output_pdf_pathnames.append(pdf_file_pathname)

                            # Don't do this; this would add each character of string
                            # pdf_file_pathname as separate list elements
                            # output_pdf_pathnames += pdf_file_pathname
                            logging.info(f'PDF generated: {pdf_file_pathname}')
                        else:
                            logging.warn(f'{image_file} might not have been successfully converted to a PDF file')
                        break

            # If no errors occurred during the conversions, all image files
            # have been converted to PDF files.
            # Onto creating a zip file.
            zip_filename = f'{output_filename_stem}.zip'
            zipfile_path = os.path.join(output_dir, zip_filename)
            logging.info(f'Zipping {len(output_pdf_pathnames)} PDF files')
            logging.info(f'PDF pathnames: {output_pdf_pathnames}')
            with zipfile.ZipFile(zipfile_path, 'w') as pages_zip:
                for pdf_path in output_pdf_pathnames:
                    pages_zip.write(pdf_path, f'{arc_dir}/{os.path.basename(pdf_path)}')
                if output_format == 'pdf_and_jpeg':
                    pages_zip.write(images_zip_pathname, f'{arc_dir}/{images_zip_filename}')

            download_zipfile_size = get_file_size_in_bytes(zipfile_path)
            self.event_listener.on_state_changed({
                'state': 'download_ready',
                'download_file_url': output_dir_url + '/' + zip_filename,
                'download_file_size': download_zipfile_size})
        elif output_page_option == 'pdf-for-each-2-scanned-pages':
            logging.error('PDF file for each 2 scanned pages: not implemented')
        else:
            logging.error('Unrecognized output page option')

    def on_scan_complete(
        self,
        output_dir,
        output_dir_url,
        output_page_option,
        rotate,
        output_format
        ):
        """
        Generates a PDF file from the images of the scanned pages
        if the output format(s) include PDF document.
        """

        logging.info('Document scan complete')

        output_filename_stem = 'scan_' + datetime.datetime.now().replace(microsecond=0).isoformat().replace(':','_')

        self.rotate_scanned_images(output_dir, rotate)

        images_zip_filename = ''
        images_zip_pathname = ''
        arc_dir = output_filename_stem
        if output_format == 'jpeg' or output_format == 'pdf_and_jpeg':
            # Zip the generated image files
            self.event_listener.on_state_changed({'state': 'creating_zip', 'message': 'Creating a zip from image files...'})
            images_zip_filename = f'{output_filename_stem}_jpg.zip'
            images_zip_pathname = os.path.join(output_dir, images_zip_filename)
            utils.save_scanned_images_as_zip_file(output_dir, images_zip_pathname, arc_dir)
            self.event_listener.on_state_changed({'state': 'zip_created', 'message': 'Created a zip from image files.'})

            if output_format == 'jpeg':
                # No need to create a PDF file
                download_file_size = get_file_size_in_bytes(images_zip_pathname)
                self.event_listener.on_state_changed({
                    'state': 'download_ready',
                    'output_format': output_format,
                    'pdf_file_url': '',
                    'download_file_url': output_dir_url + '/' + images_zip_filename,
                    'download_file_size': download_file_size,
                    'num_scanned_pages': 0
                })

        if output_format == 'pdf' or output_format == 'pdf_and_jpeg':
            # Generate a PDF file / PDF files from the image files.
            # - Add the PDF file(s) to the zip file if output is images + pdf(s)
            # - Create a zip file if output is set to "1 pdf file per page"
            self.generate_pdf_from_image_files(
                output_format,
                output_dir,
                output_dir_url,
                output_page_option,
                output_filename_stem,
                images_zip_pathname)

    def poll_prrocess(self, process, on_process_terminated):
        while(True):
            rc = process.poll()
            if rc is None:
                # rc is None: the process has NOT been terminated.
                pass
            else:
                logging.info(f'returncode: {rc}')
                self.on_process_terminated()

    def convert_process_main_loop(
        self,
        process,
        output_format,
        output_dir,
        output_file_pathname,
        arc_dir, # Internal directory in the ZIP archive
        images_zip_pathname,
        images_zip_filename,
        pdf_file_pathname,
        pdf_filename,
        pdf_file_url,
        download_file_url,
        ):

        while(True):

            rc = process.poll()
            if rc is None:
                # rc is None: the process has NOT been terminated.
                pass
            else:
                logging.info(f'conversion returncode: {rc}')
                if rc == 0:
                    if output_format == 'pdf':
                        # Download file is a PDF file; no more conversions / compressions are
                        # performed. Just return the link to the PDF file, i.e. output_file_pathname
                        # (.pdf) already exists.
                        pass
                    elif output_format == 'pdf_and_jpeg':
                        # Zip the pdf file and the zip file of images to create
                        # a single zip file for download
                        with zipfile.ZipFile(output_file_pathname, 'w') as pdf_and_images_zip:
                            #arc_dir = datetime.datetime.now().replace(microsecond=0).isoformat().replace(':','_')
                            pdf_and_images_zip.write(pdf_file_pathname, f'{arc_dir}/{pdf_filename}')
                            pdf_and_images_zip.write(images_zip_pathname, f'{arc_dir}/{images_zip_filename}')
                    else:
                        logging.error('Unsupported output format')

                    logging.info(f'download_file_url: {download_file_url}')
                    download_file_size = get_file_size_in_bytes(output_file_pathname)
                    self.event_listener.on_state_changed({
                        'state': 'download_ready',
                        'output_format': output_format,
                        'pdf_file_url': pdf_file_url,
                        'download_file_url': download_file_url,
                        'download_file_size': download_file_size,
                        'num_scanned_pages': 0
                    })

                    #create_zip_of_scanned_pages()

                self.event_listener.on_state_changed({'state': 'conversion_process_terminated', 'message': ''})
                break # Process has been terminated

    def build_scanimage_command(
            self,
            sheet_width=215,
            sheet_height=297,
            resolution=200,
            sides='front',
            color_mode='color',
            brightness=25,
            starting_page_number=1,
            output_dir='.') -> list:

        cmd = ['scanimage']

        # Add the '-p' option to display the progress
        cmd += ['-p']

        # Increase the buffer size from the default 32KB to a much larger value
        # - Without this, the scanner stops scanning at about page 4 or so
        #   (resolution set to 300)
        # - This was not necessary when executing scanimage from terminal,
        #   but somehow if it is when the command is invoked in Python.
        cmd += ['--buffer-size=1024']

        # Page width and height (unit: mm)
        cmd += ['--page-width', str(sheet_width), '--page-height', str(sheet_height)]

        # Resolution
        cmd += [f'--resolution={resolution}']

        # Color mode
        mode = 'Gray' if color_mode == 'grayscale' else 'Color'
        cmd += ['--mode', mode]

        # Set the output image format
        cmd += ['--format', 'jpeg']

        #output_dir = os.path.join(base_output_dir, secrets.token_hex(8))
        #output_dir = base_output_dir + '/' + secrets.token_hex(8)
        logging.info(f'output_dir: {output_dir}')

        # Turn on the batch mode option
        cmd += [f"--batch={os.path.join(output_dir,'page%03d.jpg')}"]

        # Page number to start naming files with
        cmd += [f'--batch-start={starting_page_number}']

        # front side only or duplex (front & back)
        source = 'ADF Front' if sides == 'front' else 'ADF Duplex'
        cmd += ['--source', source]

        # Brightness
        cmd += ['--brightness', str(brightness)]

        if Settings.sudo_scanimage and not Settings.test_mode:
            cmd.insert(0, 'sudo') # Prepend the command with 'sudo'

        logging.info(f'cmd: {cmd}')

        return cmd

    def scan_papers(
            self,
            sheet_width=215,
            sheet_height=297,
            resolution=200,
            sides='front',
            color_mode='color',
            brightness=25,
            starting_page_number=1,
            output_dir='.'):
        """
        Executes the scanimage command asynchronously and returns the process object
        - This function should return fairly quickly as it does not wait until the scanimage command to complete the scan.
        - output_dir: Directory path on the filesystem where pdf, zipped jpg, and individual jpg files are to be saved
        """

        cmd = self.build_scanimage_command(
            sheet_width,
            sheet_height,
            resolution,
            sides,
            color_mode,
            brightness,
            starting_page_number,
            output_dir
        )

        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            logging.info(f'scanimage threw an error: {e.returncode}, {e.output}')
            self.event_listener.on_state_changed({'state', 'scan_failed', 'message', 'Scan failed'})

        return p

    def scan_and_save_results(
        self,
        sheet_width=215,
        sheet_height=297,
        resolution=200,
        sides='front',
        color_mode='color',
        brightness=25,
        page_rotate_options='',
        starting_page_number=1,
        output_dir='.',
        output_dir_url='',
        output_format='pdf',
        output_page_option='single-pdf-file'
        ):

        logger.info(f'page_rotate_options: {page_rotate_options}')

        rotate = ''
        #if rotate_page_90_degrees:
        if 0 <= page_rotate_options.find('rotate_by_90_degrees'):
            if 0 <= page_rotate_options.find('rotate_even_numbered_page_by_180_degrees'):
                logging.error('Rotate 90 + upside down correction: not supported yet.')
                pass
            else:
                if sides == 'front':
                    rotate = '90'
                elif sides == 'duplex':
                    # Need to alternate the direction of the rotation,
                    # assuming that the top of the page is aligned to the same
                    # edge on both front and back.
                    rotate = '90,270'
                else:
                    logging.error(f'Unsupported sides value: {sides}')
                    return
        else:
            if 0 <= page_rotate_options.find('rotate_even_numbered_page_by_180_degrees'):
                rotate = '0,180'

        # This executes the scanimage command and returns without
        # waiting for the command to finish
        scan_process = self.scan_papers(
            sheet_width=sheet_width,
            sheet_height=sheet_height,
            resolution=resolution,
            sides=sides,
            color_mode=color_mode,
            brightness=brightness,
            starting_page_number=starting_page_number,
            output_dir=output_dir
        )

        t = threading.Thread(
            target=self.scan_and_convert_process_main_loop,
            kwargs={
                'process': scan_process,
                'output_dir': output_dir,
                'output_dir_url': output_dir_url,
                'output_page_option': output_page_option,
                'rotate': rotate,
                'output_format': output_format
                })

        t.start()

    def get_scanner_info_sync(self):

        try:
            cmd = ['scanimage', '-L']

            if Settings.sudo_scanimage and not Settings.test_mode:
                cmd.insert(0, 'sudo') # Prepend the command with 'sudo'

            logging.info(f'scanner check cmd: {cmd}')

            out = ''
            logging.info(f'Settings.test_mode : {Settings.test_mode}')
            if Settings.test_mode:
                out = "device `hambina:NyankoScan N500:1607650' is a HAMBINA NyankoSnap N500 scanner"
            else:
                out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf8')

            if(0 <= out.find('No scanners were identified.')):
                logging.info('Scanner not found')
                return {'scanner_found': False}
            else:
                # Example stdout when a scanner is found:
                # device `fujitsu:ScanSnap iX500:1508641' is a FUJITSU ScanSnap iX500 scanner
                m = re.search("' is a .+scanner$", out)

                # Note that in Python's ternary expression, the condition
                # is evaluated first, so the statement below does not throw
                # an exception even when m is None
                scanner_name = m.group(0)[7:-8] if m is not None else "Couldn't get the scanner name"
                print("scanner_name", scanner_name)
                return {'scanner_found': True, 'scanner_name': scanner_name}

        except subprocess.CalledProcessError:
            print('CalledProcessError')

        return {'scanner_found': False}
