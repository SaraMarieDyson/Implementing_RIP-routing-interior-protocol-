def BellmanFord(table_dict, recieved_table_dict, source_of_routing_table, neighbour_edges):
   #Finds the least cost paths from this router to every other router in the graph. 
   updated_dests = []
   for dest_vertex in recieved_table_dict:
      if recieved_table_dict[dest_vertex][1] < 16:
         updated_dests.append(dest_vertex) #The routes to these destinations have been updated. 
         
      if source_of_routing_table in neighbour_edges: # A neighbour has sent us their information
         table_dict[source_of_routing_table] = (source_of_routing_table, neighbour_edges[source_of_routing_table]) #The cost to a neighbour in contact with us never changes.
         
      if dest_vertex not in table_dict and recieved_table_dict[dest_vertex][1] != 16: #We have no information on this vertex yet
         table_dict[dest_vertex] = (source_of_routing_table, min(recieved_table_dict[dest_vertex][1] + table_dict[source_of_routing_table][1], 16)) #We add the vertex to our routing table, along with its information.
            
      elif dest_vertex in table_dict: #We already have information on this vertex
         if recieved_table_dict[dest_vertex][0] == table_dict[dest_vertex][0] and recieved_table_dict[dest_vertex][0] < 16: # Routes have same next hop
            table_dict[dest_vertex] = (recieved_table_dict[dest_vertex][0], min(recieved_table_dict[dest_vertex][1] + table_dict[source_of_routing_table][1],16)) #We update this cost based on the information recieved.
         elif table_dict[dest_vertex][1] > recieved_table_dict[dest_vertex][1] + table_dict[source_of_routing_table][1]: # The new route has a lower cost than our current route.
            table_dict[dest_vertex] = (source_of_routing_table, min(recieved_table_dict[dest_vertex][1] + table_dict[source_of_routing_table][1], 16)) #We update our table to reflect the new route to this vertex.
            
         
   return table_dict, updated_dests
