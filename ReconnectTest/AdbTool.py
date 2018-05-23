# -*- coding:utf-8 -*-
"""
编写时间：2017-10-18
adb 工具类
"""
import os, platform, re, subprocess, ast,time,random


class AdbTools(object):
    def __init__(self, device_id=""):
        self.__command = ''
        self.__device_id = device_id
        self.__find = ""
        self.__check_adb()
        self.__connection_device()

    def __check_adb(self):
        """
        检查adb环境
        :return:
        """
        if "ANDROID_HOME" in os.environ:
            if "Windows" == platform.system():
                self.__find = "findstr"
                adb_path = os.path.join(os.environ["ANDROID_HOME"], "platform-tools", "adb.exe")
                if os.path.exists(adb_path):
                    self.__command = adb_path
                else:
                    raise EnvironmentError("Adb not found in $ANDROID_HOME path: %s." % os.environ["ANDROID_HOME"])
            else:  # 其他系统
                self.__find = "grep"
                path = os.path.join(os.environ["ANDROID_HOME"], "platform-tools", "adb")
                if os.path.exists(path):
                    self.__command = path
                else:
                    raise EnvironmentError(
                        "Adb not found in $ANDROID_HOME path: %s." % os.environ["ANDROID_HOME"])
        else:
            raise EnvironmentError(
                "Adb not found in $ANDROID_HOME path: %s." % os.environ["ANDROID_HOME"])

    def __connection_device(self):
        """
        指定设备id时，在使用adb命令需要加上-s 设备id
        :return:
        """
        if self.__device_id == "":
            return
        else:
            self.__device_id = "-s {}".format(self.__device_id)

    def executeCmd(self, cmd):  # 返回状态及执行结果
        return subprocess.getstatusoutput(cmd)

    def getmystatusoutput(self, cmd):
        try:
            data = subprocess.check_output(cmd, timeout=90, shell=True, universal_newlines=True,
                                           stderr=subprocess.STDOUT)
            status = 0
        except subprocess.CalledProcessError as ex:
            data = ex.output
            status = ex.returncode
        if data[-1:] == '\n':
            data = data[:-1]
        return status, data

    def adb(self, args):
        """
        执行普通adb命令
        :param args:
        :return:
        """
        cmd = "{} {} {}".format(self.__command, self.__device_id, str(args))
        # print(cmd)
        return self.getmystatusoutput(cmd)

    def shell(self, args):
        """
        执行adb shell命令
        :param args:
        :return:
        """
        cmd = "{} {} shell {}".format(self.__command, self.__device_id, str(args))
        # print(cmd)
        return self.getmystatusoutput(cmd)

    @classmethod
    def get_devices_list(cls):
        """
        获取连接的所有设备列表
        :return:
        """
        dev = []
        status, output = cls().adb("devices")
        print(output)
        if not status:
            templist = output.strip("").split("\n")
            count = len(templist) - 2
            for i in range(count):
                try:
                    devrows = templist[i + 1].split("\t")
                    assert len(devrows) == 2
                    if devrows[1] == 'device':
                        dev.append(devrows[0])
                    else:
                        print("设备连接异常 %s" % str(devrows))
                except AssertionError as e:
                    print('assert error :%s' % e)
            return dev

        else:
            print("出现异常：%s" % output)

    def get_bluetooth_file_path(self):
        """
        获取蓝牙路径，大部分手机可通过cat  /etc/bluetooth/bt_stack.conf获取
        :return:
        """
        status, output = self.shell('cat  /etc/bluetooth/bt_stack.conf')
        bluetooth_path = re.search(r"(?<=BtSnoopFileName=)(.*)", output).group(1)
        return bluetooth_path

    def remove_file(self, filePath):
        """
        清除指定路径下的文件或者文件夹
        :param filePath:
        :return:
        """
        print(self.shell("rm {}".format(filePath)))

    def pull(self, source, target):
        """
        从手机端推送文件至电脑端
        :param source:
        :param target:
        :return:
        """
        return self.adb("pull {} {}".format(source, target))

    def push(self, source, target):
        """
        从电脑端推送文件至手机端
        :param source:
        :param target:
        :return:
        """
        self.adb('push {} {}'.format(target, source))

    def get_device_model(self):
        """
        获取设备型号
        :return:
        """
        status, output = self.shell("getprop ro.product.model")
        return output.strip("\n")

    def get_device_brand(self):
        """
        获取设备厂商名
        :return:
        """
        status, output = self.shell("getprop ro.product.brand")
        return output.strip("\n")

    def get_device_SDK_version(self):
        """
        获取设备sdk版本
        :return:
        """
        _, output = self.shell(" getprop ro.build.version.sdk")
        return output.strip("\n")

    def get_device_android_version(self):
        """
        获取设备android版本
        :return:
        """
        _, output = self.shell(" getprop  ro.build.version.release")
        return output.strip("\n")

    def get_device_state(self):
        """
        获取设备状态
               device： 设备已连接
               offline：连接出现异常，设备无响应
               unknown：没有连接设备
        :return:
        """
        return self.adb("get-state")

    def get_device_resolution(self):
        """
        获取设备的分辨率
        :return:
        """
        cmd="adb {} shell dumpsys window displays".format(self.__device_id)
        pattern = re.compile(r"(?<=init=)(\d+x\d+) ")
        PI = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        for i in iter(PI.stdout.readline, "b"):
            if i == b'':
                break
            result = pattern.findall(str(i, encoding="utf-8"))

            if result:
                return result[0]
        return

    def install(self, path):
        """
        安装apk
        :param path: apk路径,路径不能包含空格
        :return:
        """
        # 安装常见错误，错误字典
        errors = {'INSTALL_FAILED_ALREADY_EXISTS': '程序已经存在',
                  'INSTALL_DEVICES_NOT_FOUND': '找不到设备',
                  'INSTALL_FAILED_DEVICE_OFFLINE': '设备离线',
                  'INSTALL_FAILED_INVALID_APK': '无效的APK',
                  'INSTALL_FAILED_INVALID_URI': '无效的链接',
                  'INSTALL_FAILED_INSUFFICIENT_STORAGE': '没有足够的存储空间',
                  'INSTALL_FAILED_DUPLICATE_PACKAGE': '已存在同名程序',
                  'INSTALL_FAILED_NO_SHARED_USER': '要求的共享用户不存在',
                  'INSTALL_FAILED_UPDATE_INCOMPATIBLE': '版本不能共存',
                  'INSTALL_FAILED_SHARED_USER_INCOMPATIBLE': '需求的共享用户签名错误',
                  'INSTALL_FAILED_MISSING_SHARED_LIBRARY': '需求的共享库已丢失',
                  'INSTALL_FAILED_REPLACE_COULDNT_DELETE': '需求的共享库无效',
                  'INSTALL_FAILED_DEXOPT': 'dex优化验证失败',
                  'INSTALL_FAILED_DEVICE_NOSPACE': '手机存储空间不足导致apk拷贝失败',
                  'INSTALL_FAILED_DEVICE_COPY_FAILED': '文件拷贝失败',
                  'INSTALL_FAILED_OLDER_SDK': '系统版本过旧',
                  'INSTALL_FAILED_CONFLICTING_PROVIDER': '存在同名的内容提供者',
                  'INSTALL_FAILED_NEWER_SDK': '系统版本过新',
                  'INSTALL_FAILED_TEST_ONLY': '调用者不被允许测试的测试程序',
                  'INSTALL_FAILED_CPU_ABI_INCOMPATIBLE': '包含的本机代码不兼容',
                  'CPU_ABIINSTALL_FAILED_MISSING_FEATURE': '使用了一个无效的特性',
                  'INSTALL_FAILED_CONTAINER_ERROR': 'SD卡访问失败',
                  'INSTALL_FAILED_INVALID_INSTALL_LOCATION': '无效的安装路径',
                  'INSTALL_FAILED_MEDIA_UNAVAILABLE': 'SD卡不存在',
                  'INSTALL_FAILED_INTERNAL_ERROR': '系统问题导致安装失败',
                  'INSTALL_PARSE_FAILED_NO_CERTIFICATES': '文件未通过认证 >> 设置开启未知来源',
                  'INSTALL_PARSE_FAILED_INCONSISTENT_CERTIFICATES': '文件认证不一致 >> 先卸载原来的再安装',
                  'INSTALL_FAILED_INVALID_ZIP_FILE': '非法的zip文件 >> 先卸载原来的再安装',
                  'INSTALL_CANCELED_BY_USER': '需要用户确认才可进行安装',
                  'INSTALL_FAILED_VERIFICATION_FAILURE': '验证失败 >> 尝试重启手机',
                  'DEFAULT': '未知错误'
                  }
        status, output = self.adb("install -r {}".format(path))
        if "Success" in output:
            print("install Success:{}".format(self.__device_id))
        if 'Failure' in output:
            key = re.findall("\\[(.+?)(?=)\\]", output)[0]
            try:
                print('Install Failure >> %s' % errors[key])
            except KeyError:
                print('Install Failure >> %s' % key)

        return output

    def silence_install(self,apkpath):
        """
        静默安装app，跳过小米等需要账号验证的手机
        :param apkpath:
        :return:
        """
        errors = {'INSTALL_FAILED_ALREADY_EXISTS': '程序已经存在',
                  'INSTALL_DEVICES_NOT_FOUND': '找不到设备',
                  'INSTALL_FAILED_DEVICE_OFFLINE': '设备离线',
                  'INSTALL_FAILED_INVALID_APK': '无效的APK',
                  'INSTALL_FAILED_INVALID_URI': '无效的链接',
                  'INSTALL_FAILED_INSUFFICIENT_STORAGE': '没有足够的存储空间',
                  'INSTALL_FAILED_DUPLICATE_PACKAGE': '已存在同名程序',
                  'INSTALL_FAILED_NO_SHARED_USER': '要求的共享用户不存在',
                  'INSTALL_FAILED_UPDATE_INCOMPATIBLE': '版本不能共存',
                  'INSTALL_FAILED_SHARED_USER_INCOMPATIBLE': '需求的共享用户签名错误',
                  'INSTALL_FAILED_MISSING_SHARED_LIBRARY': '需求的共享库已丢失',
                  'INSTALL_FAILED_REPLACE_COULDNT_DELETE': '需求的共享库无效',
                  'INSTALL_FAILED_DEXOPT': 'dex优化验证失败',
                  'INSTALL_FAILED_DEVICE_NOSPACE': '手机存储空间不足导致apk拷贝失败',
                  'INSTALL_FAILED_DEVICE_COPY_FAILED': '文件拷贝失败',
                  'INSTALL_FAILED_OLDER_SDK': '系统版本过旧',
                  'INSTALL_FAILED_CONFLICTING_PROVIDER': '存在同名的内容提供者',
                  'INSTALL_FAILED_NEWER_SDK': '系统版本过新',
                  'INSTALL_FAILED_TEST_ONLY': '调用者不被允许测试的测试程序',
                  'INSTALL_FAILED_CPU_ABI_INCOMPATIBLE': '包含的本机代码不兼容',
                  'CPU_ABIINSTALL_FAILED_MISSING_FEATURE': '使用了一个无效的特性',
                  'INSTALL_FAILED_CONTAINER_ERROR': 'SD卡访问失败',
                  'INSTALL_FAILED_INVALID_INSTALL_LOCATION': '无效的安装路径',
                  'INSTALL_FAILED_MEDIA_UNAVAILABLE': 'SD卡不存在',
                  'INSTALL_FAILED_INTERNAL_ERROR': '系统问题导致安装失败',
                  'INSTALL_PARSE_FAILED_NO_CERTIFICATES': '文件未通过认证 >> 设置开启未知来源',
                  'INSTALL_PARSE_FAILED_INCONSISTENT_CERTIFICATES': '文件认证不一致 >> 先卸载原来的再安装',
                  'INSTALL_FAILED_INVALID_ZIP_FILE': '非法的zip文件 >> 先卸载原来的再安装',
                  'INSTALL_CANCELED_BY_USER': '需要用户确认才可进行安装',
                  'INSTALL_FAILED_VERIFICATION_FAILURE': '验证失败 >> 尝试重启手机',
                  'DEFAULT': '未知错误'
                  }
        self.adb("push {} /data/local/tmp/QuDaoTest.apk".format(apkpath))
        time.sleep(1)
        status, output=self.shell(" pm install -r -f /data/local/tmp/QuDaoTest.apk")
        if 'Success' in output:
            print("install Success:{}".format(self.__device_id))
        else:
            if 'Failure' in output:
                key = re.findall("\\[(.+?)(?=)\\]", output)[0]
                try:
                    print('Install Failure >> %s' % errors[key])
                except KeyError:
                    print('Install Failure >> %s' % key)
        self.shell('"rm -r /data/local/tmp/QuDaoTest.apk"')  # 清除手机本地产生的xml文件
        return output

    def uninstall(self, package):
        """
        卸载app
        :param package:应用包名
        :return:
        """
        _, output = self.adb("uninstall {}".format(package))
        return output

    def get_apk_package(self, apkpath):
        """
        获取apk的包名
        :param apkpath:
        :return:
        """
        cmd = 'aapt dump badging %s ' % (apkpath)
        status, output = self.executeCmd(cmd)
        # 获取数据名字匹配字符串
        getNameRe = re.compile('(?:name=\')(.*)\' versionCode=', re.I | re.M)
        getName = re.findall(getNameRe, output)
        return getName[0]

    def get_cache_logcat(self):
        """
        获取缓存日志，应为属于实时日志，不能使用普通的read（）
        :return:
        """
        cmd="adb {} logcat -v time -d".format(self.__device_id)
        PI = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        for i in iter(PI.stdout.readline, "b"):
            if i == b'':
                break
            yield i

    def clear_cache_logcat(self):
        """
        清除缓存日志
        :return:
        """
        self.adb("logcat -c")

    def get_pid(self, package_name):
        """
        获取pid
        :param package_name:
        :return:
        """
        if "Windows" == platform.system():
            out = self.shell("ps | {} {} ".format(self.__find, package_name))
            if out:
                result = str(out[1]).split()
                result.remove(result[0])
                return re.findall(r"\d+", " ".join(result))[0]
            else:
                print("The process doesn't exist")
                return
        else:
            return

    def get_uid(self, pid):
        """
        获取uid
        :param pid:
        :return:
        """
        result = self.shell("cat /proc/%s/status" % pid)
        for i in result[1].split("\n"):
            if 'uid' in i.lower():
                return i.split()[1]

    def reboot_phone(self):
        """
        重启手机
        """
        self.adb("reboot")

    def get_airplane_status(self):
        """
        飞行模式状态
        0 关闭，1是打开
        """
        try:
            status, mode = self.shell("settings get global airplane_mode_on")
            if int(mode) == 1:
                return True
            else:
                return False
        except Exception as e:
            print(e)


    def quit_app(self, package):
        """
        退出app，类似于kill掉进程
        """
        return self.shell("pm  force_stop  {}".format(package))


    def clear_data(self, package):
        """
        force_stop 仅杀进程，不清除数据，clear可以清除数据"
        """
        return self.shell("pm clear {}".format(package))


    def start_activity(self, activity):
        """
        启动activity，即启动界面
        """
        return self.shell("am start -a {}".format(activity))


    def input_keyevent(self, key):
        """
        输入键码
        """
        return self.shell("input keyevent {}".format(key))


    def get_screen_status(self):
        """
        获取屏幕状态
        """
        _, out = self.shell("dumpsys power")
        result = re.findall(r"(?<=Display Power: state=)(.*)", out)
        if result:
            return result[0]
        else:
            return


    def get_device_lock_status(self):
        """
        获取锁屏状态
        解锁状态isStatusBarKeyguard和mShowingLockscreen_status均为false
        """

        _, isStatusBarKeyguard = self.shell("dumpsys window policy|{} isStatusBarKeyguard".format(self.__find))
        isStatusBarKeyguard_status = re.findall(r"(?<=isStatusBarKeyguard=)(\w+)", isStatusBarKeyguard)

        _, mShowingLockscreen = self.shell("dumpsys window policy|{} mShowingLockscreen".format(self.__find))
        mShowingLockscreen_status = re.findall(r"(?<=mShowingLockscreen=)(\w+)", mShowingLockscreen)

        if isStatusBarKeyguard_status and mShowingLockscreen_status:
            return (ast.literal_eval(isStatusBarKeyguard_status[0].capitalize()) or ast.literal_eval(
                mShowingLockscreen_status[0].capitalize()))
        elif isStatusBarKeyguard_status:
            return ast.literal_eval(isStatusBarKeyguard_status[0].capitalize())
        else:
            return ast.literal_eval(mShowingLockscreen_status[0].capitalize())

    #以下新增
    def get_matching_app_list(self, keyword):
        """
        模糊查询与keyword匹配的应用包名列表
        usage: getMatchingAppList("qq")
        """
        mat_app = []
        _, out=self.shell("pm list packages %s" % keyword)
        if out:
            mat_app.append(out.split(":")[-1].splitlines()[0])
        return mat_app

    def is_install(self,packageName):
        if self.get_matching_app_list(packageName):
            return True
        else:
            return False

    def get_phone_ime(self):
        """
        获取设备已安装的输入法包名
        """
        _, out =self.shell("ime list -s")
        print(out)
        ime_list = [ime.strip()  for ime in out.strip("").split("\n") if ime]
        return ime_list

    def set_phone_ime(self, arg):
        """
        :return: 更改手机输入法
        """
        return self.shell("ime set %s" % arg)

    def touch_by_element(self, element):
        """
        点击元素,坐标方式
        """
        self.shell("input tap %s %s" % (str(element[0]), str(element[1])))
        time.sleep(0.5)

    def touch_by_coord(self,x,y):
        """
        点击元素
        usage: touchByElement(Element().findElementByName(u"计算器"))
        """
        self.shell("input tap %s %s" % (str(x), str(y)))
        time.sleep(0.5)

    def get_focused_package_xml(self, save_path):
        """
        抓取当前页面的UI结构内容
        """
        file_name = random.randint(10, 99)
        print(self.shell('uiautomator dump /data/local/tmp/{}.xml'.format(file_name)))
        print(self.adb('pull /data/local/tmp/{}.xml  {}'.format(file_name, save_path)))

    def get_app_version_name(self, package) :
        """
        获取app的版本信息
        """
        _,out = self.shell("dumpsys package {} | {}  versionName".format(package, self.__find))
        if "versionName" in out:
            return out.split("=")[1].strip()

    def get_app_version_code(self, package) :
        """
        获取app的versionCode
        """
        _, out = self.shell("dumpsys package {} | {} versionCode".format(package, self.__find))
        if "versionCode" in out :
            return out.split("=")[1].split(" ")[0]

    def get_disk(self) :
        """
        获取手机磁盘信息
        :return: Used:用户占用,Free:剩余空间
        """
        _,out=self.shell('df')
        for s in out.split("\n"):
            if '/mnt/shell/emulated' in s or '/storage/sdcard0' in s :
                lst = []
                for i in s.split(" "):
                    if i:
                        lst.append(i)

                return lst[2],lst[3]

    def get_wm_density(self) :
        """
        屏幕密度
        :return:Physical density: 480
        """
        _,out = self.shell("wm density")
        if "Physical density" in out :
            return out.split(":")[1].strip("\n")

    def get_mac_address(self) :
        """
        :return:mac地址,android版本较高获取不了
        """
        _,out=self.shell("cat /sys/class/net/wlan0/address")
        return out.strip("\n")

    def send_text(self,textc):
        """
        发送一段文本，只能包含英文字符和空格，多个空格视为一个空格
        usage: sendText("i am unique")
        :param text:
        :return:
        """
        text = str(textc).split(" ")
        out = []
        for i in text:
            if i != "":
                out.append(i)
        length = len(out)
        for i in range(length):
            self.shell("input text %s" % out[i])
        time.sleep(0.5)

if __name__ == "__main__":
    tool = AdbTools()
    print(tool.get_device_android_version())
    print(tool.get_device_SDK_version())
    print(tool.get_disk())
