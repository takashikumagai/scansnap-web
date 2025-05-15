import json
import logging
from pathlib import Path

from django.http import JsonResponse
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from rest_framework import serializers, viewsets
from rest_framework.response import Response

from . import scanner_controller
from .models import Scan


scanner_controller = scanner_controller.ScannerController()


class ScanSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Scan
        fields = "__all__"

        # fields derived from the scanning operation
        # These fields are NOT validated with serializer.is_valid()
        read_only_fields = ["status", "num_scanned_papers"]


class ScanViewSet(viewsets.ModelViewSet):
    queryset = Scan.objects.all()
    serializer_class = ScanSerializer

    def create(self, request, *args, **kwargs):
        # Validate incoming scan settings using the serializer
        # The serializer will only validate fields *not* in read_only_fields
        # or fields provided by the client.
        print("ScanViewSet create", request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save the initial Scan object with status NOT_EXECUTED (default)
        # perform_create calls serializer.save()
        # This creates the DB record and populates fields from request.data
        self.perform_create(serializer)
        # Get the newly created instance
        instance = serializer.instance

        # Extract settings needed for the async scan initiation
        # Use the validated data from the serializer if available, or request.data
        scan_settings = {
            "color": instance.color, # Use saved instance data or validated data
            "sheet_width": instance.sheet_width,
            "sheet_height": instance.sheet_height,
            "sides": instance.sides,
            "resolution": instance.resolution,
            "brightness": instance.brightness,
            "page_rotate_options": instance.page_rotate_options,
            "starting_page_number": instance.starting_page_number,
            # Pass any other settings required by initiate_async_scan
            # For simulation purposes:
            "simulate_init_failure": request.data.get('simulate_init_failure', False),
            # 'simulate_failure': request.data.get('simulate_failure', False), # Pass if your async task uses it
        }

        # Initiate the asynchronous scan process
        # Pass the ID of the created instance so the async process knows which
        # record to update later.
        res = initiate_async_scan(instance.id, scan_settings)

        # 5. Update the instance status based on whether initiation succeeded
        if res and res.get("status") == "scanning":
            # Set status to PENDING if initiation was successful
            instance.status = Scan.Status.SCANNING
            # Save the instance again with the updated status
            instance.save()
            # Use the serializer to represent the instance with the PENDING status
            # Re-serializing ensures the response includes the updated status
            response_serializer = self.get_serializer(instance)
            headers = self.get_success_headers(response_serializer.data)
            # Return 201 CREATED, indicating the scan request was accepted and queued
            return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            # If initiation failed, update the status to FAILED
            instance.status = Scan.Status.FAILED
            instance.save()
             # Return 400 or 500 depending on the nature of the initiation failure
            return Response(
                {"detail": "Failed to initiate scan process.", "scan_id": instance.id},
                status=status.HTTP_400_BAD_REQUEST # Or HTTP_500_INTERNAL_SERVER_ERROR
            )

    # You don't need to explicitly define list, retrieve, update, destroy
    # unless you want to override *their* behavior as well.
    # They are inherited from ModelViewSet.


@login_required(login_url="/login/")
def home(request):
    return render(request, "scansnapwebapp/main.html", context={})

# def get_scanner_info_sync():
#     return {"scanner_found": True, "scanner_name": "meowscan"}

def get_scanner_info(request):
    return JsonResponse(scanner_controller.get_scanner_info_sync())

def initiate_async_scan(instand_id, scan_settings):
    # data = json.loads(request.body.decode('utf-8'))
    print("/scan/ request body:", scan_settings)

    logging.info(f"main:sheet_width: {scan_settings.get('sheet_width')}")
    logging.info(f"main:sheet_height: {scan_settings.get('sheet_height')}")
    logging.info(f"main:sides: {scan_settings.get('sides')}")
    logging.info(f"main:color: {scan_settings.get('color')}")
    logging.info(f"main:resolution: {scan_settings.get('resolution')}")

    # output_dirpath = Path('scanned_documents') / secrets.token_hex(8)
    # output_dir = Path(current_app.root_path) / output_dirpath
    output_dir = "."
    Path(output_dir).mkdir(exist_ok=True)
    # output_dir_url = url_for('static', filename=(output_dirpath))
    output_dir_url = "."
    if output_dir_url.endswith('/'):
        logging.error('output_dir_url ending with /')

    scanner_controller.scan_and_save_results(
        sheet_width=scan_settings.get("sheet_width"),
        sheet_height=scan_settings.get("sheet_height"),
        resolution=scan_settings.get("resolution"),
        color_mode=scan_settings.get("color"),
        brightness=scan_settings.get("brightness"),
        sides=scan_settings.get("sides"),
        page_rotate_options=scan_settings.get("page_rotate_options"),
        starting_page_number=scan_settings.get("starting_page_number"),
        # Working directory for this package > set to "(path to the package dir)/scansnap/" for scripts of the package?
        output_dir=output_dir,
        output_dir_url=output_dir_url,
        output_format=scan_settings.get("output_format"),
        output_page_option=scan_settings.get("output_page_option")
    )

    return JsonResponse({'scan': 'started'})


def ping(request):
    return JsonResponse({"status": "UP"})
