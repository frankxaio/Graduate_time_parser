import mechanicalsoup
from datetime import datetime


class VerboseBooster:
    def __init__(self, name, sample_count, res, verbose_input):
        # data用來紀錄學生姓名、L串列紀錄各畢業時間的入學年與口試日期
        self.name = name
        self.sample_count = sample_count
        self.res = res
        self.students = verbose_input
        self.L1, self.L2, self.L3 = ([],[],[])

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

    def show(self):
        print("--------------Detail searching...-------------")

        # 開啟url
        url = 'https://ndltd.ncl.edu.tw/cgi-bin/gs32/gsweb.cgi/login?o=dwebmge'
        browser = mechanicalsoup.StatefulBrowser()
        browser.open(url)
        browser.select_form('form[name="main"]')

        # 填入資料並開始搜尋
        browser["qs0"] = self.name
        browser["dcf"] = "ad"
        browser.submit_selected()
        
        # 紀錄網址中的ccd項
        ccd = browser.get_url()
        ccd = ccd[52:58:]

        # 根據畢業年遞減排序
        try:
            browser.select_form('form[name="main"]')
        except LinkNotFoundError:
            print("系統過載，請稍後再試")
        browser["sortby"] = "-yr"
        browser["SubmitChangePage"] = "1"

        # 進入第一筆資料，並取得資料網址
        enter = f"/cgi-bin/gs32/gsweb.cgi/ccd={ccd}/record"
        browser.follow_link(enter.strip())
        now = browser.get_url()
        
        # 迴圈控制變數宣告
        i = 0

        # 利用迴圈依序進入每一筆資料
        while  i < self.sample_count:
            i += 1
            now = now[:69] + str(i)
            browser.open(now.strip())
            access = browser.get_current_page()

            # 取得學生名字，若學生名字存在data字典中，嘗試取得口試日期
            student_name = access.body.form.div.table.tbody.tr.td.table.find("th", text="研究生:").find_next_sibling().get_text()
            if student_name in self.students:
                try:
                    oral_defense = access.body.form.div.table.tbody.tr.td.table.find("th", text="口試日期:").find_next_sibling().get_text()
                    # 取得論文題目
                    thesis_title = access.body.form.div.table.tbody.tr.td.table.find("th", text="論文名稱:").find_next_sibling().get_text()
    
                    # 計算實際就學年數
                    enter_year = int(self.students[student_name][0]) + 1911
                    study_years = self.calculate_study_years(enter_year, oral_defense)
                    
                    self.students[student_name].append(oral_defense)
                    self.students[student_name].append(thesis_title)
                    self.students[student_name].append(study_years)
                    self.students[student_name][0] = f"{str(enter_year)} 年"

                    # 根據實際就學年數重新分類
                    if study_years is not None:
                        if study_years <= 2.5:
                            self.L1.append([self.students[student_name][0], self.students[student_name][2], 
                                          self.students[student_name][3], self.students[student_name][4]])
                        elif study_years <= 3.0:
                            self.L2.append([self.students[student_name][0], self.students[student_name][2], 
                                          self.students[student_name][3], self.students[student_name][4]])
                        else:  # 3.0年以上
                            self.L3.append([self.students[student_name][0], self.students[student_name][2], 
                                          self.students[student_name][3], self.students[student_name][4]])

                # 若口試日期取得失敗，繼續迴圈
                except AttributeError:
                    continue



        # 輸出結果
        print("\n" + "="*60)
        print(f"🎓 2.5年(含)以內畢業的 {len(self.L1)} 位學生中：")
        print("="*60)
        if(self.L1 != []):
            for time in self.L1:
                print(f"📅 入學時間：{time[0]}")
                print(f"🎯 口試時間：{time[1]}")
                print(f"📚 論文題目：{time[2]}")
                print(f"⏱️ 實際就學年數：{time[3]} 年")
                print("-"*60)
        else:
            print("❌ 無資料")
            print("-"*60)

        print("\n" + "="*60)
        print(f"🎓 2.5-3年畢業的 {len(self.L2)} 位學生中：")
        print("="*60)
        if(self.L2 != []):
            for time in self.L2:
                print(f"📅 入學時間：{time[0]}")
                print(f"🎯 口試時間：{time[1]}")
                print(f"📚 論文題目：{time[2]}")
                print(f"⏱️ 實際就學年數：{time[3]} 年")
                print("-"*60)
        else:
            print("❌ 無資料")
            print("-"*60)

        print("\n" + "="*60)
        print(f"🎓 3年以上畢業的 {len(self.L3)} 位學生中：")
        print("="*60)
        if(self.L3 != []):
            for time in self.L3:
                print(f"📅 入學時間：{time[0]}")
                print(f"🎯 口試時間：{time[1]}")
                print(f"📚 論文題目：{time[2]}")
                print(f"⏱️ 實際就學年數：{time[3]} 年")
                print("-"*60)
        else:
            print("❌ 無資料")
            print("-"*60)
