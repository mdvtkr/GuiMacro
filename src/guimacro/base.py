import pyautogui
import pyperclip
from subprocess import *
from pathlib import Path
import math
from PIL import Image

_print = print
print = lambda x, indent=0: _print("  "*indent + str(x).replace('\n', '\n'+"  "*indent), flush=True)

class Base:
    def __init__(self, cwd, confidence=0.999, region=None):
        self.cwd = cwd
        self.set_default(confidence=confidence, region=region)

        # get screen size (pixel basis)
        tmp = pyautogui.screenshot()
        self.scr_size = (tmp.width, tmp.height)
        self.viewport_size = pyautogui.size()
        self.pixel_ratio = (self.scr_size[0]/self.viewport_size[0], self.scr_size[1]/self.viewport_size[1])
        print(f'screen info - size: {self.scr_size} / viewport: {self.viewport_size} / pixel ratio: {self.pixel_ratio}')

        self.resource_path, self.resource_scale_ratio = self.__get_preferred_resource()

    def __get_preferred_resource(self):
        resource_root = (self.cwd/'res')

        print(f'resouce resolution')
        dist = 10000000
        preferred = None
        for resolution in resource_root.iterdir():
            if not resolution.is_dir():
                continue
            # the name of folder should be width_height format
            res_size = tuple(map(int, resolution.name.split('_')))
            print(res_size, 1)

            cur_dist = math.dist(self.scr_size, res_size)
            if cur_dist < dist:
                dist = cur_dist
                preferred = res_size
        if preferred:
            print(f'preferred resource resolution: {preferred}', 2)
            return resource_root/f'{preferred[0]}_{preferred[1]}', None if dist==0.0 else (self.scr_size[0]/preferred[0], self.scr_size[1]/preferred[1])
        else:
            return preferred, None
    
    def set_default(self, confidence=0.999, region=None):
        self.confidence = confidence
        self.region = region

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
    
    def __scale_testing(self, org_img):
        ### test
        # (self.resource_path/'tmp').mkdir(exist_ok=True) ####
        samplings = [Image.Resampling.HAMMING,
                    Image.Resampling.BOX,
                    Image.Resampling.BILINEAR,
                    Image.Resampling.BICUBIC,
                    Image.Resampling.LANCZOS, 
                    Image.Resampling.NEAREST]
        for sampling in samplings:
            img = org_img.resize((round(org_img.width*self.resource_scale_ratio[0]), round(org_img.height*self.resource_scale_ratio[1])), sampling)
            for confidence in [0.899, 0.999]:
                try:
                    pos = pyautogui.locateCenterOnScreen(img, confidence=confidence)
                    print(f'[{sampling.name}|{confidence}] {pos}', 2)
                except:
                    print(f'[{sampling.name}|{confidence}] error', 2)
        # img.save(self.resource_path/'tmp'/img_name) ####

    def _find_image(self, img_name, confidence=None, region=None, retry=1):
        for i in range(0, retry):
            file = self.resource_path/img_name
            try:
                img = Image.open(str(file.absolute()))
                if self.resource_scale_ratio:
                    img = img.resize((round(img.width*self.resource_scale_ratio[0]), round(img.height*self.resource_scale_ratio[1])), Image.Resampling.LANCZOS)
                return pyautogui.locateCenterOnScreen(img, confidence=confidence if confidence else self.confidence, region=region if region else self.region)
            except Exception as e:
                print(f'cannot find image: {img_name} ({i+1}/{retry}) ({type(e).__name__})')
        return None
    
    def __adjust_pixel_ratio(self, pos):
        return (int(pos.x / self.pixel_ratio[0]), int(pos.y / self.pixel_ratio[1]))
        
    def _click(self, pos):
        pos = self.__adjust_pixel_ratio(pos)
        print(f'click: {pos}')
        pyautogui.click(pos[0], pos[1], button=pyautogui.LEFT)

    def _doubleClick(self, pos):
        pos = self.__adjust_pixel_ratio(pos)
        print(f'doubleClick: ({pos})')
        pyautogui.doubleClick(pos[0], pos[1], button=pyautogui.LEFT)

    def _input(self, val):
        print(f'input: {val}')
        pyperclip.copy(val)
        self._paste()

    def _hotkey(self, val):
        pyautogui.hotkey(val)
    
    def _paste(self):
        pyautogui.hotkey('command', 'v')