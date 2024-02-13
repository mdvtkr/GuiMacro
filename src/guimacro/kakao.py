import time
from guimacro import Base
from tedious import intent_logger

info, dbg, err = intent_logger.get(__name__)

class KakaoTalk(Base):
    def __init__(self, cwd, confidence=0.999, region=None, secret_path='secret/kakaotalk'):
        super().__init__(cwd, confidence=confidence, region=region)
        
        secret = self.cwd/secret_path
        with secret.open('rt') as f:
            id = f.readline().strip()
            pw = f.readline().strip()

        self.open()
        self.__login(id, pw)

    def __login(self, id, pw):
        info('login')
        pos = self._find_image('kakao_btn_confirm.png')
        if pos:
            self._click(pos)    # clear popup.

        pos = self._find_image('kakao_btn_qrlogin.png')    # login check
        if not pos: 
            info('already logged in', 1)
        else:
            info('login required', 1)
            pos = self._find_image('kakao_input_id.png', retry=3)
            if pos:
                self._click(pos)
                self._input(id)
            pos = self._find_image('kakao_input_pw.png', retry=3)
            self._click(pos)
            self._input(pw)

            pos = self._find_image('kakao_btn_login.png')
            self._click(pos)

            while pos != None:
                info('login waiting...', 2)
                time.sleep(5)
                pos = self._find_image('kakao_signing_in.png')
            info('logged in', 1)

    def open_chatroom(self, chatroom_name_imgs:list):
        for name in chatroom_name_imgs:
            pos = self._find_image(name)
            if pos:
                self._click(pos)
                self._doubleClick(pos)
                time.sleep(3)
                return True
        return False
    
    def focus_input(self):
        pos = self._find_image('kakao_chatroom_input.png')
        if not pos:
            return False
        self._click(pos)
        return True

    def send_msg(self, chatroom_names:list, msgs):
        """
        chatroom_name: list of image file names
          - active, inactive image pair is recommanded.
        msg: message to send in chatroom
        return: None
        """

        if not self.open_chatroom(chatroom_names):
            err('failed to open chatroom: ' + ', '.join(chatroom_names), 2)
            return False

        if not self.focus_input():
            err('failed to focus input position', 2)
            self._hotkey('esc')    # close opened chatroom
            return False
            
        for msg in msgs:
            self._input(msg)
            self._hotkey('enter')

        time.sleep(2)
        self._hotkey('esc')
        return True
    
    def open(self):
        dbg('open kakaotalk')
        self._open_application('kakaotalk')
        time.sleep(5)  # wait until application is shown

    def close(self):
        dbg('close kakaotalk')
        self.open()
        self._hotkey('esc')
        time.sleep(3)
        self._hotkey('esc')



