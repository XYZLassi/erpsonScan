import logging
import os
import shutil
import tempfile
import time

from sane import SaneDev

from scan_info import ScanInfo
from subject import Subject


class ScanService(Subject[ScanInfo]):
    def serve(self, device: SaneDev):

        tmp_dir: str | None = None
        try:
            while True:
                tmp_dir = tempfile.mkdtemp()
                logging.info(f"Temp-directory for batch: {tmp_dir}")

                info = ScanInfo(
                    work_directory=tmp_dir,
                    work_directory_is_temporary=True
                )

                page_index = 0
                was_running = False
                while True:
                    try:
                        time.sleep(1)
                        device.start()
                        im = device.snap()
                        was_running = True

                        im = im.rotate(180)
                        file_path = os.path.join(tmp_dir, f'{page_index}.pdf')
                        im.save(file_path)
                        info.files.append(file_path)

                        logging.info(f'Save Scan: {page_index}.pdf')
                        page_index += 1
                    except Exception as ex:
                        if len(ex.args) >= 1:
                            valid_errors = [
                                'Document feeder out of documents',
                                'Device busy'
                            ]
                            if ex.args[0] in valid_errors:

                                if was_running:
                                    break
                                continue
                        raise ex

                # End of Scan
                self.notify(info)

        except Exception as e:
            if tmp_dir is not None:
                shutil.rmtree(tmp_dir)
            raise e
