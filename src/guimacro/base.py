import pyautogui
import pyperclip
from subprocess import *
from pathlib import Path

_print = print
print = lambda x, indent=0: _print("  "*indent + str(x).replace('\n', '\n'+"  "*indent), flush=True)

class Base:
    def __init__(self, cwd):
        self.cwd = cwd

    def _open_application(self, name):
        cmd = ['open', '-a', name]
        self._execute_shell(cmd)

    def _execute_shell(self, args):
        print(f'shell command: ' + " ".join(args))
        process = Popen(list(args), stdout=PIPE, stderr=PIPE)
        ret = []
        while process.poll() is None:
            line = process.stdout.readline()
            if isinstance(line, bytes):
                line = str(line, 'utf-8')
            if line != '' and line.endswith('\n'):
                ret.append(line[:-1])
        stdout, stderr = process.communicate()
        if isinstance(stdout, bytes):
            stdout = str(stdout, 'utf-8')
        if isinstance(stderr, bytes):
            stderr = str(stderr, 'utf-8')
        ret += stdout.split('\n')
        if stderr != '':
            ret += stderr.split('\n')
        ret.remove('')
        return ret

    def _find_image(self, img_name, retry=1):
        for i in range(0, retry):
            file = (self.cwd/'res')/img_name
            try:
                return pyautogui.locateCenterOnScreen(str(file.absolute()))
            except:
                print(f'cannot find image: {img_name} ({i+1}/{retry})')
        return None
        
    def _click(self, pos):
        # print(f'click: ({pos.x},{pos.y})')
        pyautogui.click(pos.x, pos.y, button=pyautogui.LEFT)

    def _doubleClick(self, pos):
        # print(f'doubleClick: ({pos.x},{pos.y})')
        pyautogui.doubleClick(pos.x, pos.y, button=pyautogui.LEFT)

    def _input(self, val):
        pyperclip.copy(val)
        self._paste()

    def _hotkey(self, val):
        pyautogui.hotkey(val)
    
    def _paste(self):
        pyautogui.hotkey('command', 'v')