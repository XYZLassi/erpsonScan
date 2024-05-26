import logging
import os
import shutil
from queue import Queue
from threading import Thread
from time import sleep

import ocrmypdf

from scan_info import ScanInfo
from subject import Subject


class OCRService(Thread, Subject[ScanInfo]):
    def __init__(self):
        Thread.__init__(self)
        Subject.__init__(self)

        self.__is_running = False
        self.info_queue = Queue[ScanInfo]()

    def run(self):
        self.__is_running = True
        while self.__is_running:
            if self.info_queue.empty():
                sleep(0.5)
                continue

            while not self.info_queue.empty():
                info = self.info_queue.get()

                if not info.merge_file:
                    continue

                logging.info(f'OCR File:{info.merge_file}')

                filename = os.path.join(info.work_directory, 'ocr.pdf')
                ocrmypdf.ocr(info.merge_file, filename, language='deu', deskew=True, clean=True, progress_bar=False)

                if info.output_filename:
                    shutil.copyfile(filename, info.output_filename)

                self.notify(info)

    def stop(self):
        self.__is_running = False
