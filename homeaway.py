#################################
#
# homeaway.py
# Written by Chip Cox  17FEB2017
# Purpose - handle turning off lights by room as people leave the house
################################
#
# Date         Initials Description
# 17FEB2017	CC 	Initial release
#
#################################
import appdaemon.appapi as appapi
import datetime
from utils import *
             
class homeaway(appapi.AppDaemon):

  def initialize(self):
    # self.LOGLEVEL="DEBUG"
    self.log("homeaway App")
    # setup room structure
    # {"room":{["list of device trackers associated with this room. Get names from Home Assistant"],"lights":{"device name":"on/off",etc:etc}}}
    #
    self.rooms={"master":{"occupants":["device_tracker.scox1209_scox1209","device_tracker.turboc1208_cc1208"],
                          "lights":{"light.master_light_switch":"off", "light.master_floor_light":"off",
                                    "switch.master_fan":"off", "switch.master_toilet_fan":"off",
                                    "switch.master_toilet_light":"off"}},
                "sam":{"occupants":["device_tracker.scox0129_sc0129"],
                       "lights":{"light.sam_fan_switch":"off","light.sam_light_switch":"off",
                                 "switch.sam_toilet_light":"off","switch.sam_toilet_fan":"off","switch.sam_vanity_switch":"off"}}}
    
    # Setup Callback
    #self.run_minutely(self.timer_handler,datetime.datetime.now())          # for debugging
    self.run_every(self.timer_handler,datetime.datetime.now(),15*60)

    self.checkHomeState()  # Lets see what our condition is now rather than waiting 15 minutes.

  # Timer handle just calls checkHomeState so check home state can be called from other places as well
  def timer_handler(self,kwargs):
    self.checkHomeState()

  # most of the work is done here
  def checkHomeState(self):
    self.log("everyone_home={} anyone_home={} noone_home={}".format(self.everyone_home(),self.anyone_home(),self.noone_home()))
    #self.log("rooms={}".format(self.rooms))
    if not self.everyone_home():             # if anyone is gone then lets see if we have a room to turn off lights in
      self.trackers = self.my_get_trackers() # get current status of all device_trackers

      # lets go through each room one at a time and check to see if the occupants are home
      for room in self.rooms:
        if not self.room_occupants_home(self.rooms[room]["occupants"]):  # if the room occupants are not home
          self.log("room {} occupants {} are not home".format(room,self.rooms[room]["occupants"]))
          for light in self.rooms[room]["lights"]:                       # loop through the rooms lights
            if self.rooms[room]["lights"][light]=="off":                 # if the light should be off
              self.log("turning off {}".format(light))
              self.turn_off(light)                                       # turn off the light
            else:
              self.log("turning on {}".format(light))                    # if the light should be on
              self.turn_on(light)                                        # turn on the light
        else:
          self.log("room {} occupants {} are home".format(room,self.rooms[room]["occupants"]))
    else:
      self.log("everyone is home")

  # if any of the rooms occupants are home, return true, if no occupants are home, reutrn false
  def room_occupants_home(self,occupants):
    home=False
    for occupant in occupants:
      if self.trackers[occupant]["state"]=="house":
        home=True
    return home
 
  # my version of Appdaemon's get_trackers returns a full dictionary for each tracker
  def my_get_trackers(self):
    return(self.get_state("device_tracker"))


  # my log message overrides the AppDaemon one
  def log(self,msg,level="INFO"):
    obj,fname, line, func, context, index=inspect.getouterframes(inspect.currentframe())[1]
    super(homeaway,self).log("{} - ({}) {}".format(func,str(line),msg),level)

  # set the house state based on input_select in HA
def set_house_state(self,entity,state):
    if self.entity_exists(entity):
      self.select_option(entity,state)
      retval=self.get_state(entity)
    else:
      retval=None
    return(retval)

  # get get house state based on input_select in HA
def get_house_state(self,entity):
    if self.entity_exists(entity):
      state=self.get_state(entity)
      self.log("house state={}".format(state),"DEBUG")
    else:
      state=None
    return(state)


