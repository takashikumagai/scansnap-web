
from unittest.mock import patch
from PIL import Image
import pytest

from . import utils


class TestUtils:

    def test_rotate_image_and_save(self):

        image_path = 'before_rotate.jpg'
        degrees = 90
        utils.rotate_image_and_save(image_path, degrees)

    @patch('subprocess.check_output')
    @patch('utils.rotate_image_and_save')
    def test_rotate_scanned_images(self, rotate_image_and_save_mock, check_output_mock):

        check_output_mock.return_value = b'image.jpg'


        utils.rotate_scanned_images('./', '90')

        check_output_mock.assert_called_once()
        rotate_image_and_save_mock.assert_called_once()
