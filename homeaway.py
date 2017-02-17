import appdaemon.appapi as appapi
from utils import *
             
class homeaway(appapi.AppDaemon):

  def initialize(self):
    # self.LOGLEVEL="DEBUG"
    self.log("homeaway App")

  def log(self,msg,level="INFO"):
    obj,fname, line, func, context, index=inspect.getouterframes(inspect.currentframe())[1]
    super(homeaway,self).log("{} - ({}) {}".format(func,str(line),msg),level)

def set_house_state(self,entity,state):
    if self.entity_exists(entity):
      self.select_option(entity,state)
      retval=self.get_state(entity)
    else:
      retval=None
    return(retval)

def get_house_state(self,entity):
    if self.entity_exists(entity):
      state=self.get_state(entity)
      self.log("house state={}".format(state),"DEBUG")
    else:
      state=None
    return(state)


