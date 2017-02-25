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
import my_appapi as appapi
from datetime import datetime, timedelta
             
class homeaway(appapi.my_appapi):

  def initialize(self):
    # self.LOGLEVEL="DEBUG"
    try:
      self.log("homeaway App")
    except IndexError:
      self.restart_app()
      self.exit()
      
    # setup room structure
    # {"room":{["list of device trackers associated with this room. Get names from Home Assistant"],"lights":{"device name":"on/off",etc:etc}}}
    #
    self.home_location=[]
    self.home_location=eval(self.args["homelocation"])
    self.log("homelocation={}".format(self.home_location))
    self.rooms={"master":{"occupants":["device_tracker.scox1209_scox1209","device_tracker.turboc1208_cc1208"],
                          "away":{"lights":{"light.master_light_switch":"off", "light.master_floor_light":"off",
                                    "switch.master_fan":"off", "switch.master_toilet_fan":"off",
                                    "switch.master_toilet_light":"off"}},
                          "home":{"lights":None}},
                "sam":{"occupants":["device_tracker.scox0129_sc0129"],
                       "away":{"lights":{"light.sam_fan_switch":"off","light.sam_light_switch":"off",
                                 "switch.sam_toilet_light":"off","switch.sam_toilet_fan":"off","switch.sam_vanity_switch":"off"}},
                       "home":{"lights":None}},
                "wholehouse":{"occupants":["device_tracker.scox1209_scox1209","device_tracker.turboc1208_cc1208","device_tracker.scox0129_sc0129","device_tracker.ccox0605_ccox0605"],
                              "away":{"lights":{"group.whole_house":"off"}},
                              "home":{"lights":None}},
                "charlie":{"occupants":{"device_tracker.ccox0605_ccox0605"},
                           "away":{"lights":{"light.charile_light_switch":"off","light.charlie_fan_switch":"125"}},
                           "home":{"lights":{"light.charlie_fan_switch":"255"}}}}
    
    self.tzoffset=-6
    # Setup Callback
    #self.run_minutely(self.timer_handler,datetime.datetime.now())          # for debugging
    self.run_every(self.timer_handler,datetime.now()+timedelta(minutes=15),15*60)
    self.listen_state(self.homeaway_state_changed,"device_tracker")

    self.checkHomeState("initialize")  # Lets see what our condition is now rather than waiting 15 minutes.

  # Timer handle just calls checkHomeState so check home state can be called from other places as well
  def timer_handler(self,kwargs):
    self.checkHomeState("timer")                                                   # check the house state by default every 15 minutes

  def homeaway_state_changed(self,entity,attribute,old,new,kwargs):
    if not new==old:                                                         # it wasn't a non movement state change we actually moved
      if (new in self.home_location) or (old in self.home_location):            # either new or old were at the home/house location
        if not((new in self.home_location) and (old in self.home_location)):    # both new and old were not at the home/house  we didn't just switch between home and house
          self.log("{} just either got home or left home".format(entity))
          self.checkHomeState("state")                                             # someone actually came home or left home so check the house state

  # most of the work is done here
  def _checklocationstate(self,location,occupants):
    anyonehome=False
    everyonehome=True
    noonehome=True
    occupants=self.rooms["wholehouse"]["occupants"]
    for person in occupants:
      personlocation=self.get_state(person)
      #self.log("person {} is {}".format(person,personlocation))
      if ((personlocation in location) if isinstance(location,list) else  (personlocation == location)):
        anyonehome=True   
        noonehome=False
      else:
        everyonehome=False
    return (anyonehome,noonehome,everyonehome) 

  def anyone_home(self):
    anyonehome,noonehome,everyonehome=self._checklocationstate(self.home_location,self.rooms["wholehouse"]["occupants"])
    return anyonehome
  
  def everyone_home(self):
    anyonehome,noonehome,everyonehome=self._checklocationstate(self.home_location,self.rooms["wholehouse"]["occupants"])
    return everyonehome

  def noone_home(self):
    anyonehome,noonehome,everyonehome=self._checklocationstate(self.home_location,self.rooms["wholehouse"]["occupants"])
    return noonehome    
  
  def checkHomeState(self,source):
    anyonehome,noonehome,everyonehome=self._checklocationstate(self.home_location,self.rooms["wholehouse"]["occupants"])

    self.log("everyone_home={} anyone_home={} noone_home={}".format(self.everyone_home(),self.anyone_home(),self.noone_home()))
    #self.log("rooms={}".format(self.rooms))

    #self.log("{} state = {} vs {} ".format("light.den_fan_light",
    #                                       datetime.strptime(self.get_state("light.den_fan_light","all")["last_updated"],
    #                                                         "%Y-%m-%dT%H:%M:%S.%f+00:00")+timedelta(hours=self.tzoffset),
    #                                       datetime.now()))

    if not self.everyone_home():             # if anyone is gone then lets see if we have a room to turn off lights in
      self.trackers = self.my_get_trackers() # get current status of all device_trackers

      # lets go through each room one at a time and check to see if the occupants are home
      for room in self.rooms:
        if not self.room_occupants_home(self.rooms[room]["occupants"]):  # if the room occupants are not home
          self.log("room {} occupants {} are not home".format(room,self.rooms[room]["occupants"]))
          light_list=self.build_light_list(self.rooms[room]["away"]["lights"])
          for light in light_list:                       # loop through the rooms lights
            # what is the last time the lights state was changed
            last_update=datetime.strptime(self.get_state(light,"all")["last_updated"],"%Y-%m-%dT%H:%M:%S.%f+00:00")+timedelta(hours=self.tzoffset)
            if (last_update+timedelta(minutes=15)) < datetime.now():      # was the light state changed over (last update + 15 min)  ago
              if light_list[light]=="off":                 # if the light should be off
                if self.get_state(light)=="on":
                  self.log("turning off {}".format(light))
                  self.turn_off(light)                                       # turn off the light
              elif light_list[light]=="on":
                if self.get_state(light)=="off":
                  self.log("turning on {}".format(light))                    # if the light should be on
                  self.turn_on(light)                                        # turn on the light
              else:
                try:
                  dim=int(light_list[light])
                except ValueError:
                  self.log("Transfering to unknown light state {}".format(light))
                if self.get_state(light)=="on":
                  self.log("adjusting power to {}".format(dim))
                  self.turn_on(light,brightness=dim)
            else:                                         # it has not been 15 minutes since the last time the light was manually turned on
              self.log("light {} was last turned on at {} which is less than 15 minutes ago so leave it on".format(light,last_update))
        else:
          self.log("room {} occupants {} are home".format(room,self.rooms[room]["occupants"]))
          if source=="home":                               # deal with any ligths to turn on as a result of someone coming home. ignore if due to timer
            light_list=self.build_light_list(self.rooms[room]["home"]["lights"])
            for light in light_list:                       # loop through the rooms lights
              # what is the last time the lights state was changed
              if light_list[light]=="off":                 # if the light should be off
                if self.get_state(light)=="on":
                  self.log("turning off {}".format(light))
                  self.turn_off(light)                                       # turn off the light
              elif light_list[light]=="on":
                if self.get_state(light)=="off":
                  self.log("turning on {}".format(light))                    # if the light should be on
                  self.turn_on(light)                                        # turn on the light
              else:                                                          # it wasn't an on or off command so it should be a power setting for a dimmer.
                try:
                  dim=int(light_list[light])
                except ValueError:
                  self.log("Transfering to unknown light state {}".format(light))
                if self.get_state(light)=="on":                              # only adjust the power setting if the light is already on.
                  self.log("adjusting power to {}".format(dim))
                  self.turn_on(light,brightness=dim)
    else:
      self.log("everyone is home")
  
  # build a list of lights to turn off doing it this way to account for a group being part of the lights
  def build_light_list(self,lights):
    out_list={}
    for light in lights:
      devtyp, devname = self.split_entity(light)
      if devtyp=="group":
        self.log("we have a group {}".format(light))
        for group_light in self.get_state(light,attribute='all')["attributes"]["entity_id"]:
          out_list[group_light]=lights[light]
      else:
        out_list[light]=lights[light]
    return out_list


  # if any of the rooms occupants are home, return true, if no occupants are home, reutrn false
  def room_occupants_home(self,occupants):
    home=False
    for occupant in occupants:
      if (self.trackers[occupant]["state"]=="house") or (self.trackers[occupant]["state"]=="home"):
        home=True
    return home
 
  # my version of Appdaemon's get_trackers returns a full dictionary for each tracker
  def my_get_trackers(self):
    return(self.get_state("device_tracker"))
