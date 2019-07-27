import logging
import os
import secrets
from flask import render_template, redirect, url_for, current_app, request
from scansnap import app
from scansnap.forms import ScanSettingsForm
from scansnap.utils import scan_and_save_results

@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def app_home():
    form = ScanSettingsForm()

    logging.info('/ or /home, request: {}'.format(request.method))
    logging.info('color: {}, sides: {}, paper size: {}, resolution: {}'.format(
        form.color.data,
        form.sides.data,
        form.paper_size.data,
        form.resolution.data
    ))
    if form.validate_on_submit():
        logging.info('Scan papers')
        # User submitted a valid form in the form of a POST request
        # Scan the papers placed on the feeder tray.

        output_dirpath = os.path.join('scanned_documents', secrets.token_hex(8))
        output_dir = os.path.join(current_app.root_path, 'static', output_dirpath)
        os.makedirs(output_dir)
        output_dir_url = url_for('static', filename=os.path.join(output_dirpath))
        if output_dir_url.endswith('/'):
            logging.error('output_dir_url ending with /')
        #output_jpg_zip_url = url_for('static', filename=)
        scan_and_save_results(
            paper_size=form.paper_size.data,
            resolution=form.resolution.data,
            color_mode=form.color.data,
            sides=form.sides.data,

            # Working directory for this package > set to '(path to the package dir)/scansnap/' for scripts of the package?
            output_dir=output_dir,
            output_dir_url=output_dir_url,
            output_pdf_filename='scan.pdf',
            save_images_as_zip = False
        )

    return render_template('home.html', form=form)