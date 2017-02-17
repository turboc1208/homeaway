import appdaemon.appapi as appapi
import datetime
from utils import *
             
class homeaway(appapi.AppDaemon):

  def initialize(self):
    # self.LOGLEVEL="DEBUG"
    self.log("homeaway App")
    self.rooms={"master":{"occupants":["device_tracker.scox1209_scox1209","device_tracker.turboc1208_cc1208"],
                          "lights":{"light.master_light_switch":"off", "light.master_floor_light":"off",
                                    "switch.master_fan":"off", "switch.master_toilet_fan":"off",
                                    "switch.master_toilet_light":"off"}},
                "sam":{"occupants":["device_tracker.scox0129_sc0129"],
                       "lights":{"light.sam_fan_switch":"off","light.sam_light_switch":"off",
                                 "switch.sam_toilet_light":"off","switch.sam_toilet_fan":"off","switch.sam_vanity_switch":"off"}}}
    
    #self.run_minutely(self.timer_handler,datetime.datetime.now())
    self.run_every(self.timer_handler,datetime.datetime.now(),15*60)
    self.checkHomeState()

  def timer_handler(self,kwargs):
    self.checkHomeState()

  def checkHomeState(self):
    self.log("everyone_home={} anyone_home={} noone_home={}".format(self.everyone_home(),self.anyone_home(),self.noone_home()))
    self.log("rooms={}".format(self.rooms))
    if not self.everyone_home():
      # lets see who is not home
      self.trackers = self.my_get_trackers()
      self.log("---------trackers={}".format(self.trackers))
      for room in self.rooms:
        if not self.room_occupants_home(self.rooms[room]["occupants"]):
          self.log("room {} occupants {} are not home".format(room,self.rooms[room]["occupants"]))
          # turn out room lights
          self.log("room {} lights {}".format(room,self.rooms[room]["lights"]))
          for light in self.rooms[room]["lights"]:
            if self.rooms[room]["lights"][light]=="off":
              self.log("turning off {}".format(light))
              self.turn_off(light)
            else:
              self.log("turning on {}".format(light))
              self.turn_on(light)
        else:
          self.log("room {} occupants {} are home".format(room,self.rooms[room]["occupants"]))
    else:
      self.log("everyone is home")

  def room_occupants_home(self,occupants):
    home=False
    for occupant in occupants:
      if self.trackers[occupant]["state"]=="house":
        home=True
    return home

  def my_get_trackers(self):
    return(self.get_state("device_tracker"))

  def find_my_room(self,tracker):
    myroom=[]
    for room in self.rooms:
      if tracker in self.rooms[room]["occupants"]:
        myroom.append(room)
    self.log("myroom={}".format(myroom))
    return myroom



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


