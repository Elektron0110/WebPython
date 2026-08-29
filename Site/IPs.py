import requests
import my_lib
import json


class IP_Seeker:
    IP = ''

    def __init__(self, IP: str, BASE: str = '.') -> None:
        self.IP = IP
        self.base = BASE

    def Seeker_3(self):
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
            return [f"\nИнформация для IP {self.IP}:"]+[f"{key}: {value}" for key, value in details.items()]

    def Seeker_4(self):
        def get_ipapi_info(ip):
            try:
                response = requests.get(f'https://ipapi.co/{ip}/json/')
                if response.status_code == 200:
                    data: dict = response.json()
                    return data
                else:
                    return str(response.status_code)
            except Exception as e:
                return str(e)
        info = get_ipapi_info(self.IP)
        if isinstance(info, dict):
            return [f"{k}: {v}" for k, v in info.items()]
        else: return [info]

    def Seek(self):
        if self.IP:
            s3 = self.Seeker_3()
            s4 = self.Seeker_4()
            if s3:
                logging = my_lib.Log(f'{self.base}/IPs/{self.IP}.IP')
                logging.log('===================== 3 =====================')
                for l in s3: logging.log(l)
                logging.log('===================== 4 =====================')
                for l in s4: logging.log(l)
                logging.log('=============================================')


if __name__ == '__main__':
    IP_Seeker(input('IP: ')).Seek()
