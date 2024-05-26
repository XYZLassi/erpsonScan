#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import datetime
import functools
import logging
import os
import shutil
import sys

import ocrmypdf
import ocrmypdf.data

import tempfile
import time

import sane
from PyPDF2 import PdfFileMerger

from pydantic import BaseModel

__author__ = "Lassi"
__copyright__ = "Lassi"
__license__ = "MIT"
__version__ = "1.0"

from file_merger import FileMerger
from ocr_service import OCRService
from scan_info import ScanInfo
from scan_service import ScanService

_logger = logging.getLogger(__name__)


class AppArgs(BaseModel):
    path: str
    log_level: int | None = logging.WARNING
    no_ocd: bool = False


def parse_args(args) -> AppArgs:
    parser = argparse.ArgumentParser(prog='oscan', )
    parser.add_argument(
        "--version",
        action="version",
        version="oscan {ver}".format(ver=__version__))

    parser.add_argument('--no-ocd', dest="no_ocd", action='store_true')
    parser.add_argument(
        "path",
        nargs="?",
        type=str,
        default=os.getcwd()
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="log_level",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO)
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="log_level",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG)

    r_args = vars(parser.parse_args(args))
    return AppArgs(**r_args)


def setup_logging(loglevel: int | None):
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def find_output_file(output_dir: str, info: ScanInfo):
    index = 0
    while True:
        date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        output_filename = os.path.join(output_dir, f'{date}-{index}.pdf')
        if os.path.exists(output_filename):
            index += 1
            continue

        break
    info.output_filename = output_filename


def delete_tmp_directory(info: ScanInfo):
    if info.work_directory_is_temporary:
        logging.info(f'Remove Tmp-Directory: {info.work_directory}')
        shutil.rmtree(info.work_directory)


def print_output(info: ScanInfo):
    if info.output_filename:
        full_path = os.path.abspath(info.output_filename)
        print(full_path)


def main(args):
    args = parse_args(args)
    setup_logging(args.log_level)

    save_path = os.path.abspath(args.path)
    logging.info(f"Save-Path:{save_path}")

    sane.init()

    search_device_model = "ES-500WII"

    device: sane.SaneDev | None = None
    try:
        while device is None:
            devices = sane.get_devices()
            for device_url, device_vendor, device_model, device_type in devices:
                if device_model == search_device_model:
                    device = sane.open(device_url)
                    break
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        logging.exception(e)
        return 1

    properties: dict[str, int | str] = {
        'source': 'ADF Duplex',
        'resolution': 600,
        'br_x': 210,  # A4 in mm
        'br_y': 297,  # A4 in mm
    }

    for name, value in properties.items():
        try:
            setattr(device, name, value)
        except Exception as ex:
            logging.exception(ex)

    exit_code = 0

    scan_service = ScanService()
    merger = FileMerger()
    ocr_service = OCRService()

    scan_service.attach(functools.partial(find_output_file, args.path))
    scan_service.attach(merger.info_queue.put)

    if args.no_ocd:
        merger.attach(delete_tmp_directory)
        merger.start()
    else:
        merger.attach(ocr_service.info_queue.put)
        ocr_service.attach(print_output)
        ocr_service.attach(delete_tmp_directory)

        merger.start()
        ocr_service.start()

    try:
        scan_service.serve(device)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.exception(e)
        exit_code = 1
    finally:
        merger.stop()
        ocr_service.stop()

        merger.join()
        ocr_service.join()

    return exit_code


def run():
    exit_code = main(sys.argv[1:])

    return exit_code


if __name__ == "__main__":
    sys.exit(run())
