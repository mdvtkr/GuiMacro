import pyautogui
import pyperclip
from subprocess import *
import math
from PIL import Image
import time
from tedious import intent_logger
import enum

info, dbg, err, logger = intent_logger.get(__name__)

from pynput.keyboard import Key, Controller as Keyboard
from pynput.mouse import Button as MouseButton, Controller as Mouse

class Direction(enum.Enum):
    left = 0
    right = 1

class Base:
    def __init__(self, cwd, confidence=0.999, region=None, main_display=None):
        self.cwd = cwd
        self.set_default(confidence=confidence, region=region)
        self.main_display = main_display

        # get screen size (pixel basis)
        tmp = pyautogui.screenshot()
        self.scr_size = (tmp.width, tmp.height)
        self.viewport_size = pyautogui.size()
        self.pixel_ratio = (self.scr_size[0]/self.viewport_size[0], self.scr_size[1]/self.viewport_size[1])
        info(f'screen info - size: {self.scr_size} / viewport: {self.viewport_size} / pixel ratio: {self.pixel_ratio}')

        self.resource_path, self.resource_scale_ratio = self.__get_preferred_resource()

    def __get_preferred_resource(self):
        resource_root = (self.cwd/'res')

        info(f'resouce resolution')
        dist = 10000000
        preferred = None
        for resolution in resource_root.iterdir():
            if not resolution.is_dir():
                continue
            # the name of folder should be width_height format
            res_size = tuple(map(int, resolution.name.split('_')))
            info(res_size, 1)

            cur_dist = math.dist(self.scr_size, res_size)
            if cur_dist < dist:
                dist = cur_dist
                preferred = res_size
        if preferred:
            info(f'preferred resource resolution: {preferred}', 2)
            return resource_root/f'{preferred[0]}_{preferred[1]}', None if dist==0.0 else (self.scr_size[0]/preferred[0], self.scr_size[1]/preferred[1])
        else:
            return preferred, None
    
    def set_default(self, confidence=0.999, region=None):
        self.confidence = confidence
        self.region = region

    def _open_application(self, name):
        info(f'open application: {name}')
        cmd = ['open', '-a', name]
        self._execute_shell(cmd)

    def _execute_shell(self, args):
        dbg(f'shell command: ' + " ".join(args))
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
                    dbg(f'[{sampling.name}|{confidence}] {pos}', 2)
                except:
                    dbg(f'[{sampling.name}|{confidence}] error', 2)
        # img.save(self.resource_path/'tmp'/img_name) ####

    def _find_image(self, img_name, confidence=None, region=None, retry=1):
        dbg(f'searching image: {img_name}')
        for i in range(0, retry):
            file = self.resource_path/img_name
            try:
                img = Image.open(str(file.absolute()))
                if self.resource_scale_ratio:
                    img = img.resize((round(img.width*self.resource_scale_ratio[0]), round(img.height*self.resource_scale_ratio[1])), Image.Resampling.LANCZOS)
                return pyautogui.locateCenterOnScreen(img, confidence=confidence if confidence else self.confidence, region=region if region else self.region)
            except Exception as e:
                err(f'cannot find image: {img_name} ({i+1}/{retry}) ({type(e).__name__})', 1)
        return None
    
    def __adjust_pixel_ratio(self, pos):
        return (int(pos.x / self.pixel_ratio[0]), int(pos.y / self.pixel_ratio[1]))
        
    def _click(self, pos):
        pos = self.__adjust_pixel_ratio(pos)
        dbg(f'click: {pos}')
        pyautogui.click(pos[0], pos[1], button=pyautogui.LEFT)

    def _doubleClick(self, pos):
        pos = self.__adjust_pixel_ratio(pos)
        dbg(f'doubleClick: ({pos})')
        pyautogui.doubleClick(pos[0], pos[1], button=pyautogui.LEFT)

    def _input(self, val):
        dbg(f'input: {val}')
        pyperclip.copy(val)
        self._paste()

    def _hotkey(self, val):
        dbg(f'hotkey: {val}')
        pyautogui.hotkey(val)
    
    def _paste(self):
        with pyautogui.hold("command"): 
            time.sleep(1)
            pyautogui.press("v")

    def toggle_fullscreen(self):
        dbg('toggle fullscreen')
        mouse = Mouse()
        mouse.position = (100, 100)
        mouse.click(MouseButton.left)
        keyboard = Keyboard()
        with keyboard.pressed(Key.cmd_l):
            with keyboard.pressed(Key.ctrl_l):
                keyboard.press('f')
                keyboard.release('f')        

    def move_to_left_display(self):
        """ macos: custom move widow shortcut must be registred: ctrl+command+shift+arrow """
        info('move to left window')
        keyboard = Keyboard()
        with keyboard.pressed(Key.cmd_l):
            with keyboard.pressed(Key.shift):
                with keyboard.pressed(Key.ctrl_l):
                    keyboard.press(Key.left)
                    keyboard.release(Key.left)

    def move_to_right_display(self):
        """ macos: custom move widow shortcut must be registred: ctrl+command+shift+arrow """
        info('move to right window')
        keyboard = Keyboard()
        with keyboard.pressed(Key.cmd_l):
            with keyboard.pressed(Key.shift):
                with keyboard.pressed(Key.ctrl_l):
                    keyboard.press(Key.right)
                    keyboard.release(Key.right)