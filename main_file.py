import sys
from parser import *
from daemon import *
from ConfigParser import *
import time

filename = sys.argv[1]
config_object2 = read_config(filename)
daemon = RoutingDaemon(config_object2) # creates routing daemon
daemon.create_daemon()
processing = True

def main():
    daemon.add_timer(daemon.update_period[0], "{}".format(daemon.router_id), "update", -1)
    daemon.send_table()
    while processing:
        print(daemon.duration_list)
        have_updated = False
        if daemon.is_input_available(): #If there is an update from a peer router
            for recieved in daemon.available:
                packet, address = recieved.recvfrom(4096)
                data, router_id = daemon.recieve_table(packet)
                for dest in set(data.keys()) - {daemon.router_id}:
                    if data[dest][1] != 16:
                        daemon.remove_timer("timeout", dest)
                        daemon.add_timer(daemon.timeout[0], "refreshed timer", "timeout", dest)
                updated_routes, routes_did_change = daemon.update(data, router_id)
                for time in daemon.duration_list:
                    for route in updated_routes:
                        if time[2] == "garbage" and time[3] == route:
                            daemon.remove_timer(time[2], time[3])
                if routes_did_change:
                    have_updated = True
            daemon.available = set()
        if have_updated:
            # Send triggered update
           daemon.remove_timer("update", -1)
           daemon.send_update()
           daemon.add_timer(daemon.update_period[0], "{}".format(daemon.router_id), "update", -1)   
        dest_list = daemon.routing_table.keys()
        for item in daemon.routing_table:
            if daemon.routing_table[item][0] not in dest_list:
                daemon.routing_table[item] = (daemon.routing_table[item][0], 16)         
        daemon.time_event_handler()                     
        daemon.print_routing_table()
                
if __name__ == "__main__":
    main()

run_rip.py
Displaying run_rip.py.
