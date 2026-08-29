from datetime import datetime
import os
from time import sleep

if os.path.isdir('Site'):
    file = open('Site/Alexis.log', 'r', encoding='utf-8').readlines()


    def mprint(object: dict[str, list]):
        string = ''
        keys = [key for key in object]
        m_len = max([len(key) for key in keys])
        for key in keys:
            half = (m_len-len(key))//2
            half+0 if (m_len-len(key))%2 else 0
            if object[key] == []: object[key] = ['']
            string += f'{half*' '}{key}{(half+(1 if (m_len-len(key))%2 else 0))*' '} | {object[key][0]}'+'\n'
            if len(object[key]) > 1: string += '\n'.join([f'{m_len*' '} | {value}' for value in object[key][1:]])+'\n'
        print(string)
        return string

    print([f for f in os.listdir('Site/IPs')[1:-2] if len(open(f'Site/IPs/{f}', 'r', encoding='utf-8').readlines()) < 7])
    for f in [f for f in os.listdir('Site/IPs')[1:-2]
        if len(open(f'Site/IPs/{f}', 'r', encoding='utf-8').readlines()) < 7]: os.remove(f'Site/IPs/{f}')


    print([f for f in os.listdir('Site/IPs')[1:-2] if ('RU' not in open(f'Site/IPs/{f}', 'r', encoding='utf-8').read()) and (f[:-3] not in [f2[:-4] for f2 in os.listdir('Site/IPs/I')])])
    for f in [f for f in os.listdir('Site/IPs')[1:-2]
            if ('RU' not in open(f'Site/IPs/{f}', 'r', encoding='utf-8').read()) and
            (f[:-3] not in [f2[:-4] for f2 in os.listdir('Site/IPs/I')])]: os.system(f'copy Site\\IPs\\{f} Site\\IPs\\I\\{f[:-3]}.txt')
    # datetime.fromtimestamp(os.path.getctime(f"Site\\IPs\\{f}")).strftime("%Y.%m.%d")

    counter: dict[str, list[str]] = {}
    for f in os.listdir('Site/IPs/I'):
        i = '/'.join([l.split(": ")[1][:-1] for l in open(f'Site/IPs/I/{f}', 'r', encoding='utf-8').readlines()
                    if l.startswith(('city:', 'region:', 'country:'))][:3][::-1])
        if i not in counter: counter[i] = []
        counter[i] += [f'{l.split('  ')[0][1:-1]} | {l.split('  ')[2][l.split('  ')[2].find(' ')+1:-1]}'
                    for l in file if f[:-4] in l]
    open('CS.txt', 'w', encoding='utf-8').write(mprint({k: v for k, v in counter.items() if k}))

if os.path.isdir('IPs'):
    from IPs import IP_Seeker
    file = open('Alexis.log', 'r', encoding='utf-8').readlines()

    print([i+1 for i in range(len(file)) if len(file[i]) < 23 and file[i][22]!=file[i][21]])

    a = list({line.split('  ')[1] for line in file
        if (line[23].isdigit() and line.split('  ')[1] not in [f2[:-4] for f2 in os.listdir('Site/IPs')])})
    a.sort()
    print(len(a))
    for ip in a:
        IP_Seeker(ip, 'Site').Seek()
        sleep(10)