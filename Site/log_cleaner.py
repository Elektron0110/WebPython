import os

for file in [file for file in os.listdir() if file.endswith('.log')]:
    last_line = ''

    f = open(file, 'r', encoding='utf-8').readlines()
    s = open(file + '.new', 'w', encoding='utf-8')

    for line in f:
        if line.split('  ')[2:] == last_line.split('  ')[2:]:
            print(f.index(line), line)
            continue
        s.write(line)
        last_line = line
