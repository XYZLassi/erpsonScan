import logging
import os
import shutil
from queue import Queue
from threading import Thread
from time import sleep

from PyPDF2 import PdfMerger

from scan_info import ScanInfo
from subject import Subject


class FileMerger(Thread, Subject[ScanInfo]):
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
                logging.info(f'Merge Directory:{info.work_directory}')

                pdf_merger = PdfMerger()
                file_name = os.path.join(info.work_directory, 'no_ocr.pdf')
                info.merge_file = file_name

                for path in info.files:
                    pdf_merger.append(path)

                with open(file_name, 'wb') as fs:
                    pdf_merger.write(fs)

                if info.output_filename:
                    shutil.copy(file_name, info.output_filename)

                self.notify(info)

    def stop(self):
        self.__is_running = False
