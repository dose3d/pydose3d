from abc import ABC, abstractmethod
import logging

logging.basicConfig(format='%(levelname)s::%(name)s:%(message)s', level=logging.INFO)

class Svc(ABC):

    def __init__(self, svc_name):
        self.svc_name = svc_name
        self.logger = logging.getLogger(f"{svc_name}")
        super().__init__()
    
    def name(self):
        return self.svc_name

    def log(self):
        return self.logger

    def set_log_level(self,level):
        logging.getLogger(f"{self.svc_name}").setLevel(level)
    
    def set_verbose_level(self, level):
        if level==1:
            self.set_log_level(logging.INFO)
        if level==2:
            self.set_log_level(logging.DEBUG)