def file_to_list(name: str, sep: str = '\n', code='utf-8',
                 sort=True) -> list[str]:
    """Эта функция упращает превращение файла в список значений, разделённых в файле опледелённым разделителем."""
    f = open(name, 'r', encoding=code)
    f = f.read().split(sep)
    if sort:
        f.sort()
    return f


class Log:
    def __init__(self, file: str = 'logger.log') -> None:
        self.file, self.comm = file, "open(file, 'a', encoding='utf-8')"

    def log(self, string: str, slice: str = ' ',
            fw: str = '', fp: str = '') -> str:
        eval(self.comm, {'file': self.file}).write(
            string + ((slice + fw) if fw else '') + '\n')
        print(string + ((slice + fp) if fp else ''))
        return f'Added: {string + ((slice + fw) if fw else '')}\nPrint: {string + ((slice + fp) if fw else '')}'

    def __str__(self) -> str:
        return f'Logger to {self.file}.'
