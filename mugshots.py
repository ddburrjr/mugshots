import time, os
from datetime import date
from datetime import timedelta
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.firefox.options import Options
from dbpackages import db_connect, db_search


class Locators:
    css_sel = [
        'div.inmate-slide-container:nth-child({}) > ',
        'div:nth-child(2) > div:nth-child(1) > span:nth-child(1)',
        'div:nth-child(2) > div:nth-child(1) > span:nth-child(2)',
        'div:nth-child(2) > div:nth-child(2) > span:nth-child(2)',
        'div:nth-child(2) > div:nth-child(3) > span:nth-child(2)',
        'div:nth-child(2) > div:nth-child(4) > span:nth-child(2)',
        'div:nth-child(2) > div:nth-child(5) > span:nth-child(2)',
        'div:nth-child(2) > div:nth-child(6) > span:nth-child(2)',
        'div:nth-child(2) > div:nth-child(7) > div:nth-child(2) > ul:nth-child(1)',
        'div:nth-child(1) > img:nth-child(2)'
    ]
    ui_month_cls = 'ui-datepicker-month'
    ui_cal_cls = 'ui-datepicker-calendar'
    ui_state_cls = 'ui-state-default'
    county_id = 'county-dropdown'
    earliest_id = 'earliest_search_date'
    latest_id = 'latest_search_date'
    css_search = '#mugshot-search > input:nth-child(6)'
    rec_count_cls = 'record-count'
    next_id = 'next-photo'
    previous_id = 'previous-photo'
    src_attr = 'src'
    li_tag = 'li'


class Mugshot:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    IMAGE_DIR = os.path.join(BASE_DIR, 'images') + '/'
    WEB_PAGE = 'http://mugshots.sun-sentinel.com/'
    HEADLESS = '--headless'
    COUNTY_OPTIONS = [
        'Broward County',
        'Miami-Dade County',
        'Palm Beach County',
        'All Areas'
    ]
    MAXDAYS = 90
    ONE_DAY = timedelta(days=1)
    MAX_DELTA = timedelta(days=MAXDAYS)
    SEL_INMATE = "SELECT * FROM inmates WHERE case_id='{}' LIMIT 1"
    SEL_PHOTOS = "SELECT id FROM photos WHERE case_id='{}' LIMIT 1"
    INS_CHARGE_QRY = "INSERT INTO charges (case_id, charge) VALUES (%s, %s)"
    INS_INMATE_QRY = "INSERT INTO inmates (case_id, last_name, first_name, sex, " \
                     "race, county, arrest_by, booked, img_url, img_file) " \
                     "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

    date_table = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                  'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

    def __init__(self, by_area=1, from_date=None, to_date=None):
        self.driver = None
        self.options = Options()
        self.options.add_argument(self.HEADLESS)
        self.curr_record = 0
        self.total_records = 0
        self.slides = []
        self.by_area = by_area if by_area in range(len(self.COUNTY_OPTIONS)) else 3
        if self.valid_date(from_date, to_date):
            self.date_to = to_date
            self.date_from = from_date
        else:
            self.date_to = date.today()
            self.date_from = self.date_to - self.ONE_DAY

    def __enter__(self):
        self.driver = webdriver.Firefox(firefox_options=self.options)
        # self.driver = webdriver.Firefox()
        self.driver.get(self.WEB_PAGE)
        self.db = db_connect()
        self.cursor = self.db.cursor()
        self.filter_search()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()
        self.cursor.close()
        self.db.close()

    def __repr__(self):
        return f"Mugshot( filtered_by: [ area='{self.COUNTY_OPTIONS[self.by_area]}', " \
            f"from={self.date_from:%Y-%m-%d}, to={self.date_to:%Y-%m-%d} ], " \
            f"total_records: {self.total_records} )"

    @property
    def total_slides(self):
        return self.total_records

    @property
    def current_slide(self):
        return self.curr_record

    def valid_date(self, from_arg, to_arg):
        valid_date = False
        if from_arg is not None and to_arg is not None:
            curr = date.today()
            past = curr - self.MAX_DELTA
            if past <= from_arg <= to_arg <= curr:
                valid_date = True
        return valid_date

    def datepicker_filter(self, month, day):
        drv = self.driver
        # Select month
        sel_date = Select(drv.find_element_by_class_name(Locators.ui_month_cls))
        sel_date.select_by_value(str(month))
        # Select day
        sel_table = drv.find_element_by_class_name(Locators.ui_cal_cls)
        sel_days = sel_table.find_elements_by_class_name(Locators.ui_state_cls)
        sel_days[day].click()

    def filter_search(self):
        drv = self.driver
        # Select county option
        select = Select(drv.find_element_by_id(Locators.county_id))
        select.select_by_visible_text(self.COUNTY_OPTIONS[self.by_area])
        # Select From Filter By
        drv.find_element_by_id(Locators.earliest_id).click()
        self.datepicker_filter(self.date_from.month-1, self.date_from.day-1)
        # Select To Filter By
        drv.find_element_by_id(Locators.latest_id).click()
        self.datepicker_filter(self.date_to.month-1, self.date_to.day-1)
        time.sleep(3)
        # Click on search button
        drv.find_element_by_css_selector(Locators.css_search).click()
        time.sleep(1)
        record_count = drv.find_element_by_class_name(Locators.rec_count_cls).text
        self.total_records = int(record_count.split(' ')[-3].replace(',',''))
        self.curr_record = 1
        self.get_slide_data()

    def booking_date(self,str_data):
        # parameter format: 'Saturday, Jul 06, 2019'
        temp = str_data.split(' ')
        return date(int(temp[-1]), self.date_table[temp[-3]],int(temp[-2][:-1]))

    @staticmethod
    def slide_case_id(url):
        return url.split('/')[-1].split('.')[0].split('-')[-1]

    def next_slide(self):
        if self.curr_record < self.total_records:
            self.driver.find_element_by_id(Locators.next_id).click()
            time.sleep(1)
            self.curr_record += 1
            self.get_slide_data()

    def previous_slide(self):
        if self.curr_record > 1:
            self.driver.find_element_by_id(Locators.previous_id).click()
            time.sleep(1)
            self.curr_record -= 1
            self.get_slide_data()

    def get_slide_data(self):
        rec_no = self.curr_record
        if rec_no not in self.slides:
            drv = self.driver
            sel = Locators.css_sel[0].format(rec_no)
            first_name = drv.find_element_by_css_selector(sel + Locators.css_sel[1]).text
            last_name = drv.find_element_by_css_selector(sel + Locators.css_sel[2]).text
            sex = drv.find_element_by_css_selector(sel + Locators.css_sel[3]).text
            race = drv.find_element_by_css_selector(sel + Locators.css_sel[4]).text
            county = drv.find_element_by_css_selector(sel + Locators.css_sel[5]).text
            arrest = drv.find_element_by_css_selector(sel + Locators.css_sel[6]).text
            booked_text = drv.find_element_by_css_selector(sel + Locators.css_sel[7]).text
            booked = self.booking_date(booked_text)
            url = drv.find_element_by_css_selector(sel + Locators.css_sel[9]).get_attribute(Locators.src_attr)
            file = os.path.basename(url)
            case_id = self.slide_case_id(url)
            charge_element = drv.find_element_by_css_selector(sel + Locators.css_sel[8])

            print(f'case: {case_id} - {first_name} {last_name} who is a {race} '
                  f'{sex} of {county}. arrested by {arrest} on {booked} for:')

            charges = []
            for charge in charge_element.find_elements_by_tag_name(Locators.li_tag):
                charges.append(charge.text)

                print(charge.text)

            print(f"REC NO: {rec_no:0=4} URL: {url} FILE: {file}", end='\n\n')

            self.slides.append(
                [rec_no, case_id, last_name, first_name, sex, race,
                 county, arrest, booked, url, file, charges])

            if not db_search(self.cursor, self.SEL_INMATE.format(case_id)):
                inmate_args = (case_id, last_name, first_name, sex, race, county, arrest, booked, url, file)
                self.cursor.execute(self.INS_INMATE_QRY, inmate_args)
                for item in charges:
                    charge_args = (case_id, item)
                    self.cursor.execute(self.INS_CHARGE_QRY, charge_args)
                self.db.commit()


def main():

    date_from = date(2019, 6, 12)
    date_to = date(2019, 6, 13)
    county_opt = 1

    with Mugshot(county_opt, date_from, date_to) as ms:
        for _ in range(ms.current_slide, ms.total_slides+1):
            time.sleep(.5)
            ms.next_slide()
        print(ms)


if __name__ == "__main__":
    main()