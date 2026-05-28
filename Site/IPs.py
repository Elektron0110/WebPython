import requests
import my_lib
import json


class IP_Seeker:
    IP = ''

    def __init__(self, IP: str) -> None:
        self.IP = IP

    def Seeker_3(self):
        self.logging.log('===================== 3 =====================')

        def get_ip_details(ip_address=None):
            url = 'https://ipinfo.io/json' if ip_address is None else f'https://ipinfo.io/{ip_address}/json'
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    return json.loads(response.text)
            except requests.RequestException:
                pass
            return None
        # Для конкретного IP (пример)
        details = get_ip_details(self.IP)
        if details:
            self.logging.log(f"\nИнформация для IP {self.IP}:")
            for key, value in details.items():
                self.logging.log(f"{key}: {value}")

    def Seeker_4(self):
        self.logging.log('===================== 4 =====================')

        def get_ipapi_info(ip):
            try:
                response = requests.get(f'https://ipapi.co/{ip}/json/')
                if response.status_code == 200:
                    data = response.json()
                    return data
                else:
                    self.logging.log(str(response.status_code))
            except Exception as e:
                self.logging.log(str(e))
            return None
        info = get_ipapi_info(self.IP)
        if info:
            for k, v in info.items():
                self.logging.log(f"{k}: {v}")

    def Seek(self):
        if self.IP:
            self.logging = my_lib.Log(f'IPs/{self.IP}.IP')
            self.Seeker_3()
            self.Seeker_4()
            self.logging.log('=============================================')
