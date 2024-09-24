from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime
from pypdf import PdfReader, PdfWriter
from pathlib import Path
from enum import Enum
import re, time, logging, base64


CHAR_PATTERN_CAN_NOT_USE_FOR_PATH = r'[:\/\\\?<>\*\|]'


class PdfType(Enum):
    Redmine = 'Redmineチェックリスト'
    GitLab = 'GitLabマージリクエスト結果'


class ExportPdfBase:
    pdf_type = PdfType.Redmine

    driver = None

    print_pdf_wait_time_sec = 5

    login_url = 'http://172.20.18.22:10081'
    login_user_id = 'root'
    login_password = 'Xsw2Cde3'
    dom_user_id_input_id = 'user_login'
    dom_password_input_id = 'user_password'
    dom_login_button_name = 'commit'

    date = None

    to_merge = False
    merged_file_name = 'レビュー結果.pdf'

    print_cnt = 1

    logger = logging.getLogger(__name__)

    def create_export_folder(self):
        self.date = f'{datetime.now():%Y%m%d%H%M%S}'
        export_folder_path = self.get_export_folder_path()
        self.logger.info(f'export_folder_path: {export_folder_path}')
        if not export_folder_path.exists():
            export_folder_path.mkdir(parents=True)

    def create_driver(self):
        options = self.create_options()
        self.driver = webdriver.Chrome(options=options)

    def destroy_driver(self):
        self.driver.close()
        self.driver.quit()

    def create_options(self):
        options = Options()
        options.add_argument('--headless')
        return options

    def find_element(self, by, value):
        element = None
        while True:
            element = self.driver.find_element(by, value)
            if element is not None:
                break
            time.sleep(1)
        return element

    def login(self):
        self.driver.get(self.login_url)
        self.find_element(By.ID, self.dom_user_id_input_id).send_keys(
            self.login_user_id
        )
        self.find_element(By.ID, self.dom_password_input_id).send_keys(
            self.login_password
        )
        self.find_element(By.NAME, self.dom_login_button_name).click()

    def open_page(self, url):
        self.driver.get(url)
        self.wait_page()

    def wait_page(self):
        raise NotImplementedError

    def get_export_folder_path(self):
        return Path.cwd() / Path(
            'ExportPdf',
            f'{self.date}_{self.pdf_type.value}',
            'data'
        )

    def get_individual_file_name(self):
        raise NotImplementedError

    def print_pdf(self):
        parameters = {
            'printBackground': True,
            'paperWidth': 8.27,
            'paperHeight': 11.69,
            'displayHeaderFooter': True
        }
        pdf_base64 = self.driver.execute_cdp_cmd(
            'Page.printToPDF', parameters
        )
        pdf = base64.b64decode(pdf_base64["data"])
        file_path = self.get_export_folder_path() / Path(
            self.get_individual_file_name()
        )
        with file_path.open(mode='bw') as f:
            f.write(pdf)
        return file_path

    def merge_pdf(self, export_files):
        page_cnt = 0
        export_file_path = \
            self.get_export_folder_path() / Path(self.merged_file_name)
        writer = PdfWriter()
        for file in export_files:
            reader = PdfReader(file)
            page_num = reader.get_num_pages()
            for page_i in range(page_num):
                page = reader.get_page(page_i)
                writer.add_page(page)
            writer.add_outline_item(
                title=file.name, page_number=page_cnt, parent=None
            )
            page_cnt += page_num
        writer.write(export_file_path)
        writer.close()
        for file in export_files:
            file.unlink()

    def run(self, export_urls):
        self.logger.info(f'PDFファイルの出力開始')
        try:
            if len(export_urls) == 0:
                raise Exception

            self.create_export_folder()

            self.create_driver()

            self.login()

            export_files = []

            for export_url in export_urls:
                self.open_page(export_url)
                export_files.append(self.print_pdf())
                self.print_cnt += 1

            if self.to_merge:
                self.merge_pdf(export_files)

            self.destroy_driver()

            return str(self.get_export_folder_path())
        except:
            pass
        return None


class ExportPdfGitLab(ExportPdfBase):
    pdf_type = PdfType.GitLab
    login_url = 'http://172.20.18.22:10081'
    dom_user_id_input_id = 'user_login'
    dom_password_input_id = 'user_password'
    dom_login_button_name = 'commit'
    to_merge = True

    def open_page(self, url):
        super().open_page(url)

        # すべてのスレッドを展開
        exists_discussion = False
        discussion_toggle_buttons = self.driver.find_elements(
            By.CLASS_NAME, 'discussion-toggle-button'
        )
        for discussion_toggle_button in discussion_toggle_buttons:
            exists_discussion = True
            svg = discussion_toggle_button.find_element(By.TAG_NAME, 'svg')
            if svg.get_attribute('data-testid') == 'chevron-down-icon':
                discussion_toggle_button.click()
        if exists_discussion:
            self.find_element(By.CLASS_NAME, 'diff-content')
            time.sleep(3)

    def wait_page(self):
        self.find_element(By.CLASS_NAME, 'timeline-icon')
        time.sleep(5)

    def get_individual_file_name(self):
        title = re.sub(
            CHAR_PATTERN_CAN_NOT_USE_FOR_PATH, '_',
            self.driver.find_element(
                By.CLASS_NAME, 'qa-title'
            ).text
        )
        return f'{self.print_cnt}_{title}.pdf'


class ExportPdfRedmine(ExportPdfBase):
    pdf_type = PdfType.Redmine
    login_url = 'http://172.20.18.22:3000'
    dom_user_id_input_id = 'username'
    dom_password_input_id = 'password'
    dom_login_button_name = 'login'

    def wait_page(self):
        self.find_element(By.ID, 'footer')
        time.sleep(3)

    def get_individual_file_name(self):
        ticket_id = re.findall(r'(\d+)/*$', self.driver.current_url)[0]
        title = re.sub(
            CHAR_PATTERN_CAN_NOT_USE_FOR_PATH, '_',
            self.driver.find_element(
                By.CLASS_NAME, 'subject'
            ).find_element(By.TAG_NAME, 'h3').text
        )
        return f'#{ticket_id}_{title}.pdf'
