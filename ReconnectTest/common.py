# -*- coding: utf-8 -*-
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.mime.application import MIMEApplication
import smtplib ,os
class SendEmail(object):
       # 构造函数，初始化基本信息
       def __init__(self, host, user, password):
              user_info = user.split("@")
              self.sender = user
              self.host=host
              self.password=password
              self._server=None

       def  __enter__(self):
              print("exc __enter__")
              if self._server is not None:
                     raise RuntimeError('Already connected')
              server = smtplib.SMTP()
              server.connect(self.host)
              server.login(self.sender, self.password)
              self._server = server

              return self

       def __exit__(self, exc_type, exc_value, exc_traceback):
              print("exc __exit__")
              self._server.quit()
              self._server.close()
              self._server=None

       def __repr__(self):
              return 'SendEmail({0.sender!r}, {0.host!r}, {0.password!r})'.format(self)


       def send_text_email(self, subject, to_list, content, sub_type="plain"):
              """
              发送纯文本邮件
              :param subject:
              :param to_list:
              :param content:
              :param sub_type:默认是 :plain，另外可选html
              :return:
              """
              msg = MIMEMultipart()
              msg['Subject'] = Header(subject, 'utf-8')
              msg['From'] = self.sender
              msg['To'] = ",".join(to_list)
              msg.attach(MIMEText(content, sub_type, _charset="utf-8"))  # 纯文本
              try:
                     self._server.sendmail(self.sender, to_list, msg.as_string())
                     return True
              except Exception as e:
                     print(e)
                     return False

       def send_attach_email(self, subject, to_list, content, file_list, sub_type="plain"):
              """
              发送带有文件附件的邮件
              :param subject:
              :param to_list:
              :param content:
              :param sub_type:默认是 :plain，另外可选html
              :return:
              """
              msg = MIMEMultipart()
              msg['Subject'] = Header(subject, 'utf-8')
              msg['From'] = self.sender
              msg['To'] = ",".join(to_list)
              msg.attach(MIMEText(content, sub_type, _charset="utf-8"))  # 纯文本
              for file in file_list:
                     filename = os.path.basename(file)
                     print(file,file)
                     xlsxpart = MIMEApplication(open(file, 'rb').read())
                     xlsxpart.add_header('Content-Disposition', 'attachment', filename=filename)
                     msg.attach(xlsxpart)

              try:
                     self._server.sendmail(self.sender, to_list, msg.as_string())
                     return True
              except Exception as e:
                     print(e)
                     return False




