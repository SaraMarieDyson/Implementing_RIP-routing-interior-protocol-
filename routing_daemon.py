from ConfigParser import *
from Packets import *
from BellmanFord import*
import socket
import select
import struct
import json 
import time
import random


class RoutingDaemon(object):
    """
    Routing Daemon class that collects processed infomation from the parser.
    Also collects info provided from routing table. Has input and ouput port for
    sending and receiving to neighbouring routers. Will recieve information if a 
    router/link in the network goes down and handle this (split horizon with poisson reverse?)
    The routing Daemon class sends info and recieves info and updates accordingly.
    
    Attributes:
    config_object -- initialises processed objects from config file
    router_id -- the id of the router
    input_ports -- list of the router's input ports
    output_ports -- list of output ports from the config parser
    in_sockets -- list of input sockets
    outputs -- dictionary of output sockets
    available -- set of sockets that are available for listening
    duration_list -- list of all timer events.
    
    Methods:
    send_table -- sends routing table to peer routers each 30 sec or when there's a triggered update
    serialize -- serialises the routing table entries and preforms poison reverse.
    recieve_table -- recieves tables from peer routers.
    update -- updates the routing table if there is a topological change.
    create_daemon -- binds sockets to input and output ports
    is_input_available -- a method that listens to a socket and checks if there's data waiting, has a wait time.
    read_data -- grabs data in available set and decodes the message
    add_timer -- adds timers to the duration array and calculates each timer.
    get_time_out -- calculates the next timer to end.
    remove_timer -- removes a timer once the time has ended.
    get_expired_timers -- grabs the timer that has ended.
    time_event_handler -- handles timers.
    """    

    def __init__(self, config_object):
        self.config_object = config_object
        self.router_id = self.config_object.id
        self.input_ports = self.config_object.inputs
        self.output_ports = self.config_object.outputs
        self.update_period = (int(random.uniform(self.config_object.period * 0.8, self.config_object.period * 1.2)), "Update timer: {} seconds.".format(self.config_object.period), "update")
        self.timeout = (self.config_object.timeout, "Timeout timer: {} seconds".format(self.config_object.timeout), "timeout", self.router_id)
        self.garbage = (self.config_object.garbage, "Garbage timer: {} seconds.".format(self.config_object.garbage), "garbage", self.router_id)
        self.in_sockets = []
        self.outputs = [output.port for output in self.output_ports]
        self.routing_table = {self.router_id:(self.router_id, 0)}
        self.edges = {output.id:output.metric for output in self.output_ports}
        self.available = set()      
        self.duration_list = [] 
        
    def send_table(self):
        """send a table to all of the peer routers. Put into packet format first."""
        sender_sock = self.in_sockets[0]
        for output in self.output_ports:
            data = self.serialize(self.routing_table, output.id)
            sender_sock.sendto(data, ('127.0.0.1', output.port))

    def serialize(self, routing_table, destination):
        """serilize the entries. Carry out poison reverse"""
        table_dict = self.routing_table
        sending_dict = table_dict.copy()
        for key,value in sending_dict.items():  #poison reverse
            if value[0] == destination:
                sending_dict[key] = (value[0], 16)  #poison reverse         
        entries = []
        for key in sending_dict.keys():
            entry = RipEntry('AF_INET', key, sending_dict[key][1])
            entries.append(entry)        
        table_packet = Packet(2,2,self.router_id,entries)
        serialised = table_packet.to_bytes()
        return serialised       
    
    def recieve_table(self, packet):
        """recieves table and infomation from peer routers. Will handle if a 
        router and/or link goes down. Turns from packet into routing table"""
        new_packet = Packet.from_bytes(packet)	
        if new_packet.command == 2 and new_packet.version == 2:
            table_dict = {}
            sender_id = new_packet.rid
            for entry in new_packet.entries:
                table_dict[entry.router_id] = (sender_id, entry.metric)  
            return table_dict, sender_id    
        
    def update(self, recieved_table_dict, source_of_rec):
        """updates routing table using Bellman Ford, if entries in the routing table 
        are different to the recieved updates from peer routers"""
        new_routing_table, updated_dests = BellmanFord(self.routing_table, recieved_table_dict, source_of_rec, self.edges) 
        if new_routing_table != self.routing_table:
            changed = True
            self.routing_table = new_routing_table
        else:
            changed = False
        return updated_dests, changed
        
    def create_daemon(self):
        """binds input port to a socket"""
        for inputs in self.input_ports:
            soc_name = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            soc_name.bind(('127.0.0.1', inputs))
            self.in_sockets.append(soc_name)
            print('Listening at {}'.format(soc_name.getsockname()))
            
            
    def is_input_available(self):
        """Checks if input is available and sets a wait time"""
        wait_time = self.get_time_out()[0]
        if wait_time == None:
            available = select.select(self.in_sockets, [], [])[0]
        else:
            wait_time = abs(wait_time)
        #print(wait_time)
        available = select.select(self.in_sockets, [], [], wait_time)[0] #takes three lists of file descriptors, give array of input sockets to listen with timeout for 100ms
        #available = select.select(self.in_sockets, [], [], 0.5)[0] #hack solution
        for in_socket in available:
            self.available.add(in_socket) # add the binded ports into the set, available for listening.
        return len(self.available) > 0 # input is available if we have at least one input socket in available    
    
    def read_data(self):
        """read entries that are available and decodes them"""
        try:
            sock = self.available.pop() #poping off the items ready to read in the available set.
            data = sock.recv(4096) # buffsize needs to be a small power of 2 -> max amount of data to be recv at once
            decode, sender_id = self.recieve_table(data) # returns a tuple -> decode the message
            return decode, sender_id
        except KeyError: # If there's nothing to be read -> raise an error.     
            return None          
             
    def add_timer(self, duration, timer_message, timer_id, router_id):
        """Calculates the duration for eachtimer and appends them to the duration list"""
        print "Adding timer with duration", duration
        current_time = int(time.time()) # grab the current time
        end_time = current_time + duration  # calculate the remaining time
        self.duration_list.append((end_time, timer_message, timer_id, router_id)) # append the time to the duration list
        
    def get_time_out(self):
        """Grabs each time event from the duration list, when it's fired."""
        print(self.duration_list)
        next_event = None
        for end_time, message, timer_id, router_id in self.duration_list:
            if not next_event or (end_time < next_event[0] and end_time >= int(time.time())): # do the comparison 
                next_event = (end_time, message, timer_id, router_id) # assign the next time event
        current_time = int(time.time()) # grab the current time
        if next_event is None: # no more timer events
            return None
        return (next_event[0] - current_time, next_event[1], next_event[2], next_event[3]) #timer counts down to next event
    
    def remove_timer(self, timer_type, router_id):
        """Removes timers that expire""" 
        find_id = None
        for i, event in enumerate(self.duration_list): # find the timer id
            if event[3] == router_id and event[2] == timer_type: 
                find_id = i
        if find_id is not None: 
            self.duration_list.pop(find_id)  #remove timer id
        
    def get_expired_timers(self):
        """grabs the timers that have finished for processing""" 
        tids = set()
        now = int(time.time())
        for end_time, message, timer_id, router_id in self.duration_list:
            if end_time <= now:
                tids.add((timer_id, message, timer_id, router_id))
        return tids
        
    def time_event_handler(self):
        """a method for handling timer events, when to start each timer."""
        fired = self.get_expired_timers()
        for timed_out, message, timer_id, router_id in fired:
            self.remove_timer(timer_id, router_id)
            if timer_id == "update": # update timer has timed out
                print(timer_id)
                self.send_table() #send the update routing table.
                self.add_timer(self.update_period[0], "{}".format(self.router_id), "update", -1) #restart the update timer
            elif timer_id == "timeout" : #timed out with no table from peer router
                print(timer_id)
                self.routing_table[router_id] = (self.routing_table[router_id][0], 16) #send the routing table with metric->16
                self.send_table()
                self.add_timer(self.garbage[0],"Garbage Timer", "garbage", router_id)#start garbage.
            elif timer_id == "garbage":
                print(timer_id)
                del self.routing_table[router_id] # delete the entry
                self.update(self.routing_table,self.router_id) # update table

    def print_routing_table(self):
        print("-"*43)        
        print("Routing table for Router {}".format(self.router_id))
        print("-"*43)
        print('|{:>12} |{:>12} |{:>12} |'.format('Destination','Next Hop','Cost'))
        print("-"*43)
        for key, value in self.routing_table.items():
            print('|{:>12} |{:>12} |{:>12} |'.format(key,value[0],value[1]))
        print('')
