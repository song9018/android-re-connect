# -*- coding:utf-8 -*-

import os,xlwt,re, configparser,time,json
from common import *
from  collections import OrderedDict

root_path=os.path.join(os.getcwd(),"log")
confi=configparser.ConfigParser()

def set_height():
    tall_style = xlwt.easyxf('font:height 360;') # 36pt,类型小初的字号
    return tall_style

def set_cell_style(is_high_light=False):
    g_normalStyle = xlwt.XFStyle()
    borders = xlwt.Borders()
    borders.left = xlwt.Borders.THIN
    borders.right = xlwt.Borders.THIN
    borders.top = xlwt.Borders.THIN
    borders.bottom = xlwt.Borders.THIN
    g_normalStyle.alignment.horz = 2
    g_normalStyle.alignment.vert = 1
    g_normalStyle.borders=borders
    if is_high_light:
        font = xlwt.Font()  # 为样式创建字体
        font.colour_index =2
        g_normalStyle.font=font
    return g_normalStyle

def get_local_time():
    current_time=time.localtime(time.time())
    return time.strftime('%F %H_%M_%S', current_time)
    # return current_time.strftime("%F %H_%M_%S")

def  parser_result(email_host,email_user,email_pwd,email_receivers_list,test_count,is_send_mail=False):
    subject="自动化执行：重连专项结果"
    content="内容为自动化脚本执行"
    file_name=get_local_time()+"重连专项结果.xls"
    result_path=os.path.join(os.getcwd(),file_name)
    workbook =xlwt.Workbook(encoding = 'utf-8')
    worksheet = workbook.add_sheet('汇总',cell_overwrite_ok=True)

    mode_pattern=re.compile(r"(?<=机型：)(.+)(?=测试轮次)")
    count_pattern=re.compile(r"(?<=测试轮次:)(\d+)")
    opera_pattern=re.compile(r"(?<=开始测试)(\w+)")
    current_count_pattern=re.compile(r"(?<=第)(\d+)(?=轮)")
    mode=""
    count=""
    operator=""
    current_count=""
    row=1
    col=0
    if os.path.exists(root_path):
        current_dir=os.listdir(root_path)
        for each in current_dir:
            row=row+1
            col=0
            file_path=os.path.join(root_path,each,"runtime.log")
            info_path = os.path.join(root_path,each,"info.json")
            if os.path.exists(info_path):#写入设备信息
                with open(info_path) as f:
                    obj=json.load(f,object_pairs_hook=OrderedDict)
                    for key in obj:
                        worksheet.write(row, col, key, set_cell_style()) #合并单元格
                        worksheet.write_merge(row,row,col+1,col+1+int(test_count),obj[key], set_cell_style())
                        row += 1
                        col = 0
            row=row-1  #写入信息最后多一行
            if os.path.exists(file_path):#写入结果
                for line in open(file_path,"r",encoding='utf-8',errors='surrogateescape'):
                    if "测试轮次" in line:
                        row+=1#换行，列归为0
                        col=0
                        mode=re.findall(mode_pattern,line)[0]
                        count=re.findall(count_pattern,line)[0]
                        operator=re.findall(opera_pattern,line)[0]
                        current_row = worksheet.row(row)
                        current_row.set_style(set_height())
                        worksheet.write(row,col,mode,set_cell_style())
                        worksheet.write(row,col+1,operator,set_cell_style())

                    if "测试轮次" not  in line and operator in line:
                        if re.findall(current_count_pattern,line):
                            current_count=re.findall(current_count_pattern,line)[0]

                            if current_count:
                                col=int(current_count)+1
                            else:
                                print("current_count问题:{}".format(current_count))

                    if "蓝牙已连接" in line:
                        worksheet.write(row,col,"OK",set_cell_style())

                    if "蓝牙未连接" in line:
                        worksheet.write(row,col,"NG",set_cell_style(True))
					
    workbook.save(result_path)
    if is_send_mail:
        with SendEmail(email_host,email_user,email_pwd) as myemail:
            myemail.send_attach_email(subject,email_receivers_list,content, [result_path])


if __name__=="__main__":	
    confi=configparser.ConfigParser()
    confi.read("basic.ini")
    #邮箱信息
    email_host=confi.get("email","smtp_server")
    email_user=confi.get("email","user")
    email_pwd=confi.get("email","password")
    email_receivers_list=confi.get("email","receivers").split(",")
    parser_result(email_host,email_user,email_pwd,email_receivers_list)



