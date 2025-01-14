import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import argparse
import requests
import subprocess
import os
import shutil
import sys
from requests.cookies import RequestsCookieJar
from requests.utils import dict_from_cookiejar, cookiejar_from_dict
import threading
import time
import base64
from datetime import datetime
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class ChromeDriverDownloader:
    def __init__(self, version: str, platform: str):
        self._current_name = ""
        self._version = version
        self._version_str = self._version.split('.')
        self._platform = platform
        self._chrome_driver_version_list = []
        self._base_url = "https://chromedriver.storage.googleapis.com"
        self._base_test_url = "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing"

    def _get_latest_version(self):
        main_version = '.'.join(self._version_str[:3])
        #if main_version.startswith("115."):
        #    return self._version
        response = requests.get(f"{self._base_url}/LATEST_RELEASE_{main_version}")
        return response.text

    def download_chromedriver(self):
        major_version = self._version_str[0]
        print(f"major version is {major_version}")
        if int(major_version) >= 115:
            return self._download_testing()
        latest_version = self._get_latest_version()
        return self._download(latest_version)

    def _download(self, version):
        url = f"{self._base_url}/{version}/chromedriver_linux64.zip"
        if version.startswith('115.'):
            url = f"{self._base_test_url}/{version}/{self._platform}/chromedriver-linux64.zip"
        print(f"downloading chrome driver from {url}")
        response = requests.get(url)
        file_name = "chromedriver.zip"
        with open(file_name, "wb") as f:
            f.write(response.content)
        if os.path.exists(file_name):
            print("download chrome driver successfully.")
        os.system("unzip chromedriver.zip -d chromedriver")
        try:
            src_file = './chromedriver/chromedriver-linux64/chromedriver'
            dst_file = './chromedriver/chromedriver'
            shutil.move(src_file, dst_file)
        except Exception as e:
            print(e)
        os.remove(file_name)
        
    def _download_testing(self):
        response = requests.get(f"https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json")        
        # print(response.json())
        
        url = list(filter(lambda x: x["platform"]=="linux64",response.json()["milestones"][f"{self._version_str[0]}"]["downloads"]["chromedriver"]))[0]["url"]
        # if "116." not in url:
        #    url = "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/116.0.5845.96/linux64/chromedriver-linux64.zip"
        print(f"downloading chrome driver from {url}")
        download_response = requests.get(url)
        file_name = "chromedriver.zip"
        with open(file_name, "wb") as f:
            f.write(download_response.content)
        if os.path.exists(file_name):
            print("download chrome driver successfully.")
        os.system("unzip chromedriver.zip -d chromedriver")
        try:
            src_file = './chromedriver/chromedriver-linux64/chromedriver'
            dst_file = './chromedriver/chromedriver'
            shutil.move(src_file, dst_file)
        except Exception as e:
            print(e)
        os.remove(file_name)


def get_chrome_version():
    result = subprocess.run(['google-chrome', '--version'], stdout=subprocess.PIPE)
    output = result.stdout.decode('utf-8')
    version = output.strip().split()[-1]
    print(f"google chrome version: {version}")
    return version

def download_chromedriver():
    chrome_version = get_chrome_version()
    os_type = sys.platform
    platform = "linux64"
    if os_type == "linux":
        platform = "linux64"
    elif os_type == "win32":
        platform = "win32"
    elif os_type == "darwin":
        platform = "mac64"
    downloader = ChromeDriverDownloader(chrome_version,platform)
    downloader.download_chromedriver()

def parse_arguments():
    parser = argparse.ArgumentParser(description="CordCloud Checkin")
    parser.add_argument("-u", "--username", help="username", type=str,required=True)
    parser.add_argument("-p", "--password", help="password", type=str,required=True)
    parser.add_argument("-U","--url",help="cordcloud url",type=str,required=True)
    parser.add_argument("-s","--skey",help="skey",type=str,required=True)
    parser.add_argument("-P","--proxykey",help="proxykey",type=str,required=True)
    return parser.parse_args()

def start_checkin(username, password, url, skey, proxykey):
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1280,1024")
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument("--excludeSwitches=enable-automation")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.headless = True
    # options.add_argument(f'--proxy-server=http://fa82f17718a8576a773e9e24605649449559e3a9:antibot=true@proxy.zenrows.com:8001')
    
    driver = uc.Chrome(options=options,driver_executable_path = "./chromedriver/chromedriver")

    #service = Service(ChromeDriverManager("114.0.5735.90").install())
    #driver = uc.Chrome(options=options,driver_executable_path = service.path)
    
    driver.implicitly_wait(10)
    
    try:

        driver.get(f'{url}/auth/login')
        
        WebDriverWait(driver, timeout=15).until(lambda d: d.find_element(By.ID, "email"))
        list_windows = driver.window_handles
        print(list_windows)
        driver.switch_to.window(list_windows[0])
        
        print(driver.title)
        print(driver.current_url)

        email_input = driver.find_element(by=By.ID, value="email")
        email_input.send_keys(username)
        password_input = driver.find_element(by=By.ID, value="passwd")
        password_input.send_keys(password)
        driver.find_element(by=By.ID, value="login").click()
        text = driver.find_element(by=By.XPATH, value="/html/body/main/div[2]/section/div[2]/div[1]/div[1]/div/div[2]/p[2]").text
        print("Login success!")
        print(text)

        cookies = driver.get_cookies()
        c={}
        for cookie in cookies:
            cookie = dict(cookie)
            c[cookie["name"]] = cookie["value"]
        
        response = requests.post(f'{url}/user/checkin', cookies=c, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.52",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": url,
            "Referer": f"{url}/user"
        },timeout=10)

        result = response.json()
        print(result)
            
        if result["ret"] == 1 and "trafficInfo" in result:
            un_used = result["trafficInfo"]["unUsedTraffic"] if "unUsedTraffic" in result["trafficInfo"] else "无效key"
            table = str.maketrans("", "", "获得了流量 ")
            str_get = result["msg"].translate(table)
            push_title = "得:" + str_get + "剩:" + un_used
            push_content = "Cord签到.剩余流量: " + un_used
        else:
            push_title = "Cord签到:" + result["msg"]
            push_content = "签到过了."
        push_msg(skey, push_title, push_content)
    
    except Exception as e:
        print(e)
    finally:
        driver.quit()

def main():
    args=parse_arguments()

    username = args.username
    password = args.password
    url = args.url
    skey = args.skey
    proxykey = args.proxykey
    
    download_chromedriver()
    start_checkin(username, password, url, skey, proxykey)

def push_msg(skey: str, title: str, content: str):
    params = {"title": title, "desp": content}
    push_url = "https://sctapi.ftqq.com/" + skey +".send"
    requests.get(push_url, params=params)
    

if __name__ == '__main__':
    main()
    
    '''
    parser = argparse.ArgumentParser(description="CordCloud Checkin")
    parser.add_argument("-u", "--username", help="username", type=str,required=True)
    parser.add_argument("-p", "--password", help="password", type=str,required=True)
    parser.add_argument("-U","--url",help="cordcloud url",type=str,required=True)
    parser.add_argument("-s","--skey",help="skey",type=str,required=True)
    parser.add_argument("-P","--proxykey",help="proxykey",type=str,required=True)
    args=parser.parse_args()

    username = args.username
    password = args.password
    url = args.url
    skey = args.skey
    proxykey = args.proxykey

    options = uc.ChromeOptions()
    options.add_argument("--window-size=1280,1024")
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument("--excludeSwitches=enable-automation")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f'--proxy-server=http://fa82f17718a8576a773e9e24605649449559e3a9:antibot=true@proxy.zenrows.com:8001')
    
    driver = uc.Chrome(driver_executable_path="/usr/bin/chromedriver", use_subprocess=True, options=options)
    driver.implicitly_wait(10)
    try:
        
        now = datetime.now()
        nowstr = str(now)

        driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers":{
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            }
        })
        
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => False
            })
        """})
        
        driver.get(f'{url}/auth/login')
        
        time.sleep(30)
        list_windows = driver.window_handles
        print(list_windows)
        driver.switch_to.window(list_windows[0])
        
        print(driver.title)
        print(driver.current_url)

        driver.save_screenshot('screenshot_' + nowstr + '.png')

        f = open('screenshot_' + nowstr + '.png','rb') 
        encodedata = base64.b64encode(f.read())
        print("data:image/bmp;base64," + str(encodedata.decode()))
        f.close()
        
        email_input = driver.find_element(by=By.ID, value="email")
        email_input.send_keys(username)
        password_input = driver.find_element(by=By.ID, value="passwd")
        password_input.send_keys(password)
        driver.find_element(by=By.ID, value="login").click()
        text = driver.find_element(by=By.XPATH, value="/html/body/main/div[2]/section/div[2]/div[1]/div[1]/div/div[2]/p[2]").text
        print("Login success!")
        print(text)

        cookies = driver.get_cookies()
        c={}
        for cookie in cookies:
            cookie = dict(cookie)
            c[cookie["name"]] = cookie["value"]
        
        response = requests.post(f'{url}/user/checkin', cookies=c, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.52",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": url,
            "Referer": f"{url}/user"
        },timeout=10)

        result = response.json()
        print(result)
        push_title = "Cord签到:" + result["msg"]    
        if result["ret"] == 1 and "trafficInfo" in result:
            un_used = result["trafficInfo"]["unUsedTraffic"] if "unUsedTraffic" in result["trafficInfo"] else "无效key"
            push_title += "剩: " + un_used
            push_content = "剩余流量: " + un_used
        else:
            push_content = "签到过了."
        push_msg(skey, push_title, push_content)
    
    except Exception as e:
        print(e)
    finally:
        driver.quit()
    '''
