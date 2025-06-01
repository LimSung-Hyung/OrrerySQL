import importlib

class LangPack:
    def __init__(self):
        self._current = None
        self.set_language('en')

    def set_language(self, code):
        if code == 'ko':
            mod = importlib.import_module('language.ko')
        else:
            mod = importlib.import_module('language.en')
        self._current = mod
        for k in dir(mod):
            if not k.startswith('__'):
                setattr(self, k, getattr(mod, k))

lang = LangPack() 