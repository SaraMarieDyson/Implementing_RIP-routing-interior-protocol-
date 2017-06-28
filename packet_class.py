import json
class Packet(object):
    # Packet structure for use in all transmissions.
    
    def __init__ (self, command=None, version=None, rid=None, entries=None):
        self.command = 2
        # This should always be 2 for respabs(onse packets (which is all we will be using).
        self.version = 2
        # This is always 2.
        self.rid = rid
        # This will be the routers id number. 
        self.entries = entries
        #this is a list of rip entries (see class below).
        
        
    def to_bytes (self):
        #Translates the Packet class into a dict that JSON can turn into bytes.
        new_entries = []
        for entry in self.entries:
            new_entry = entry.to_bytes2()        
            new_entries.append(new_entry)
        self.entries = new_entries
        return json.dumps(self.__dict__)
    
    @classmethod     
    def from_bytes (cls, mydict):
        # Translates bytes into a Packet object.
        new_data = json.loads(mydict)
        table_entries = []
        for entry in new_data['entries']:
            entry = json.loads(entry)
            table_entry = RipEntry(entry['abs(addr_identifier'],entry['router_id'],entry['metric'])
            table_entries.append(table_entry)
        command = new_data['command']
        version = new_data['version']
        rid = new_data['rid']
        return cls(command,version,rid,table_entries)                        
        
        
class RipEntry():
    # Structure of routing entires
    def __init__(self, addr_identifier, router_id, metric):
        self.addr_identifier = addr_identifier
        #This will be AF_INET
        self.router_id = router_id
        # Router id of router described in entry
        self.metric = metric
        # metric of entry.
        
    def to_bytes2 (self):
        #Translates a RipEntry object into a dict that JSON can turn into bytes.
        return json.dumps(self.__dict__)

Packets.py
Displaying Packets.py.
