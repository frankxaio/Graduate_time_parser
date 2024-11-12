from controller import id_converter
import mechanicalsoup
from datetime import datetime
from mechanicalsoup.utils import LinkNotFoundError

class LabCensusSystem:
    def __init__(self, school, name, sample_count, filter_cnt):
        self.school = school
        self.name = name
        self.sample_count = int(sample_count)
        self.filter = []
        filter_cnt = int(filter_cnt) if filter_cnt!='' else 0
        while filter_cnt:
            self.filter.append(input('過濾系所：'))
            filter_cnt -= 1

        self.verbose_input = {}
        self.result = [0,0,0]

    def calculate_study_years(self, enter_year, oral_date):
        # 設定入學日期為該年度的8月1日
        start_date = datetime.strptime(f"{enter_year}/08/01", "%Y/%m/%d")
        try:
            # 將日期中的 "-" 替換為 "/"
            oral_date = oral_date.strip().replace("-", "/")
            end_date = datetime.strptime(oral_date, "%Y/%m/%d")
            # 計算天數差異並除以365
            days_diff = (end_date - start_date).days
            years = round(days_diff / 365, 2)
            return years
        except ValueError:
            return None

    def Search(self):
        print("-----------------Searching...-----------------")

        try:
            # 開啟url
            url = 'http://etd.lib.nycu.edu.tw/cgi-bin/gs32/gsweb.cgi/login?o=dwebmge'
            browser = mechanicalsoup.StatefulBrowser()
            browser.open(url)
            browser.select_form('form[name="main"]')

            # 填入資料並開始搜尋
            browser["qs0"] = self.name
            browser["dcf"] = "ad"
            browser["limitdb"] = int(self.school)-1
            browser.submit_selected()

            # 紀錄網址中的ccd項
            ccd = browser.get_url()
            ccd = ccd[54:60:]

            # 根據畢業年遞減排序
            try:
                browser.select_form('form[name="main"]')
                browser["sortby"] = "-yr"
            except (LinkNotFoundError, KeyError):
                print(f"查無 {self.name} 教授的資料")
                return self.verbose_input

            # 進入第一筆資料，並取得資料網址
            try:
                enter = f"/cgi-bin/gs32/gsweb.cgi/ccd={ccd}/record"
                browser.follow_link(enter.strip())
                now = browser.get_url()
            except LinkNotFoundError:
                print(f"查無 {self.name} 教授的資料")
                return self.verbose_input

            # Y2：兩年畢業、Y2_3：兩年以上三年以下畢業，以此類推；previous_number用來紀錄前一筆的學號
            previous_number, i = 0, 0

            # 檢查無窮迴圈用的變數
            diff_odd, diff_even, check = (0, 0, 0)

            # 迴圈依序進入每一筆資料
            cnt = self.sample_count
            while i < cnt:
                i += 1
                now = now[:71] + str(i)
                browser.open(now.strip())
                access = browser.get_current_page()

                # 避免過度過濾導致無窮迴圈

                if(i%2==1):
                    diff_odd = cnt - i
                else:
                    diff_even = cnt - i
                if(diff_odd == diff_even):
                    check += 1
                else:
                    check = 0
                if(check == 30):
                    i -= 30
                    break

                # 過濾博士生資料
                degree = access.body.form.div.table.tbody.tr.td.table.find("th",text="學位類別:").find_next_sibling().get_text()
                if (degree == "博士"):
                    cnt += 1
                    continue

                # 過濾系所
                Department = access.body.form.div.table.tbody.tr.td.table.find("th",text="系所名稱:").find_next_sibling().get_text()
                if(Department in self.filter):
                    cnt += 1
                    continue

                # 取得學號，並偵測第 i 筆資料是否已超過教授收過的學生量
                number = access.body.form.div.table.tbody.tr.td.table.find("th",text="學號:").find_next_sibling().get_text()
                if(previous_number == number):
                    break
                else:
                    previous_number = number

                # 取得畢業學年度
                grad_year = access.body.form.div.table.tbody.tr.td.table.find("th",text="畢業學年度:").find_next_sibling().get_text()

                # 過濾出學號中的入學年資訊
                if(self.school == "1"):
                    enter_year = id_converter.NCTU(number)
                elif(self.school == "2"):
                    enter_year = id_converter.NCU(number)
                elif(self.school == "3"):
                    enter_year = id_converter.NTHU(number)
                elif(self.school == "4"):
                    enter_year = id_converter.NYMU(number)

                # 畢業生名字
                try:
                    student_name = access.body.form.div.table.tbody.tr.td.table.find("th",text="作者:").find_next_sibling().get_text()
                except AttributeError:
                    student_name = access.body.form.div.table.tbody.tr.td.table.find("th",text="作者(中文):").find_next_sibling().get_text()

                # 取得口試日期
                calculate = int(grad_year) - int(enter_year)
                if calculate <= 1:
                    print(f"{student_name} 歸類到2年")
                    self.result[0] += 1  # 改為歸類到2年
                    new = {student_name:[int(enter_year),"1"]}
                elif calculate <= 2:
                    self.result[1] += 1  # 改為歸類到2-3年
                    new = {student_name:[int(enter_year),"2"]}
                else:
                    self.result[2] += 1  # 改為歸類到3年以上
                    new = {student_name:[int(enter_year),"3"]}

                # dict(data) = { key(學生名字):value[入學年, 畢業時間] }
                self.verbose_input.update(new)
        except Exception as e:
            print(f"發生錯誤：{str(e)}")
            print(f"查無 {self.name} 教授的資料")
            return self.verbose_input

        return self.verbose_input

    def Show(self):
        return self.result
