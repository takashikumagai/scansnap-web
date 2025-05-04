import json
import logging
from pathlib import Path

from django.http import JsonResponse
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from . import utils


def hello(request):
    return JsonResponse({"message": "hello"})


@login_required(login_url="/login/")
def home(request):
    return render(request, "scansnapwebapp/main.html", context={})

# def get_scanner_info_sync():
#     return {"scanner_found": True, "scanner_name": "meowscan"}

def get_scanner_info(request):
    return JsonResponse(utils.get_scanner_info_sync())

def scan(request):
    content = json.loads(request.body.decode('utf-8'))
    print("/scan/ request body:", content)

    logging.info(f"main:sheet_width: {content['sheet_width']}")
    logging.info(f"main:sheet_height: {content['sheet_height']}")
    logging.info(f"main:sides: {content['sides']}")
    logging.info(f"main:color: {content['color']}")
    logging.info(f"main:resolution: {content['resolution']}")

    # output_dirpath = Path('scanned_documents') / secrets.token_hex(8)
    # output_dir = Path(current_app.root_path) / output_dirpath
    output_dir = "."
    Path(output_dir).mkdir(exist_ok=True)
    # output_dir_url = url_for('static', filename=(output_dirpath))
    output_dir_url = "."
    if output_dir_url.endswith('/'):
        logging.error('output_dir_url ending with /')

    utils.scan_and_save_results(
        sheet_width=content['sheet_width'],
        sheet_height=content['sheet_height'],
        resolution=content['resolution'],
        color_mode=content['color'],
        brightness=content['brightness'],
        sides=content['sides'],
        page_rotate_options=content['page_rotate_options'],
        starting_page_number=content['starting_page_number'],
        # Working directory for this package > set to '(path to the package dir)/scansnap/' for scripts of the package?
        output_dir=output_dir,
        output_dir_url=output_dir_url,
        output_format = content['output_format'],
        output_page_option = content['output_page_option']
    )

    return JsonResponse({'scan': 'started'})
