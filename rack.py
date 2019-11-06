from collections import defaultdict, namedtuple

import heapq
import re

class Cabinet():

    def __init__(self, name=None, width=600, length=600, height=2000, max_unit=48):
        self.width = width
        self.length = length
        self.height = height
        self.max_unit = max_unit
        self.name = name
        self.place = [ None for i in range(max_unit)]


class Room():

    def __init__(self, name, cabinets=None, distribution_area=None, col_span=1000, unit_width=1000, unit_length=600):
        self.name = name
        self.cabinets = cabinets
        self.distribution_area = distribution_area
        self.col_span = col_span
        self.unit_width = unit_width
        self.unit_length = unit_length
        self.distribution_graph = defaultdict(lambda:dict())
        self.distribution_area_to_grpah()
        
    def _wring_path(self, start_cabinet, target_cabinet, head_cabinet=None, *args):
        if head_cabinet is not None:
            #确保head_cabinet和起始cabinet是在同一列
            if start_cabinet//100 != head_cabinet//100:
                raise ValueError("Start cabinet and head cabinet not in same columon.")

            #TODO: 目标机柜和起始机柜在同一列的情况，忽略head_cabinet
            distance_1, path_segment_1 = self._dijkstra(start_cabinet, head_cabinet)
            distance_2, path_segment_2 = self._dijkstra(head_cabinet, target_cabinet)   
            path_segment_1.extend(path_segment_2[1:]) 
            path_segment =  path_segment_1       
            return distance_1+distance_2, path_segment

        return self._dijkstra(start_cabinet, target_cabinet)
    
    def wiring_path(self, start_cabinet, target_cabinet, head_cabinet=None, *args):
        #start,target,head cabinet is index of cabinet array, like (x,y)
        #start_cabinet = (x, y)
        #target_cabinet = (m, n)
        _start_cabinet = start_cabinet[0]*100 + start_cabinet[1]
        _target_cabinet = target_cabinet[0]*100 + target_cabinet[1]
        if head_cabinet is not None:
            _head_cabinet = head_cabinet[0]*100 + head_cabinet[1]
        else:
            _head_cabinet = head_cabinet

        return self._wring_path(_start_cabinet, _target_cabinet, _head_cabinet, *args)

    def distribution_area_to_grpah(self):
        #distribution_area 是包含列与列之间的过道的走线桥架，1表示有桥架经过，0表示无桥架经过
        #distribution_area 必须以机柜列开始
        if self.distribution_area is None:
            return 
        max_row_idx, max_col_idx = len(self.distribution_area), len(self.distribution_area[0])
        for row_idx, row in enumerate(self.distribution_area):
            #去除掉非机柜列
            #if row_idx%2 == 0:
            #    continue
            for col_idx, node in enumerate(row):
                node_name = row_idx*100 + col_idx
                if node != 0 :
                    #below node
                    if (row_idx+1) < max_row_idx and self.distribution_area[row_idx+1][col_idx] != 0:
                        below_node_name = (row_idx+1)*100 + col_idx
                        self.distribution_graph[node_name][below_node_name] = 1

                    #upon node
                    if (row_idx-1) >= 0 and self.distribution_area[row_idx-1][col_idx] != 0:
                        upon_node_name = (row_idx-1)*100 + col_idx
                        self.distribution_graph[node_name][upon_node_name] = 1
                        
                    #left node
                    if (col_idx-1) >= 0 and self.distribution_area[row_idx][col_idx-1] != 0:
                        left_node_name = row_idx*100 + col_idx-1
                        self.distribution_graph[node_name][left_node_name] = 1
                        
                    #right node
                    if (col_idx+1) < max_col_idx and self.distribution_area[row_idx][col_idx+1] != 0:
                        right_node_name = row_idx*100 + col_idx+1
                        self.distribution_graph[node_name][right_node_name] = 1                      


    def _dijkstra(self, orgin, destination):
        
        Route = namedtuple("Route", "distance path")
        routes = []
        for neighbor, distance in self.distribution_graph[orgin].items():
            heapq.heappush(routes, Route(distance=distance, path=[orgin, neighbor]))

        visited = set()
        visited.add(orgin)

        while routes:
            distance, path = heapq.heappop(routes)
            neighbor = path[-1]

            if neighbor in visited:
                continue

            if neighbor is destination:
                return distance, path

            # Tentative distances to all the unvisited neighbors
            for _neighbor in self.distribution_graph[neighbor]:
                if _neighbor not in visited:
                    # Total spent so far plus the distance of getting there
                    new_distance = distance + self.distribution_graph[neighbor][_neighbor]
                    new_path  = path + [_neighbor]
                    routes.append(Route(new_distance, new_path))

            visited.add(neighbor)

        return None, None


    def shortest_path(self, orgin, destination, padding=0):
        orgin_row_idx = orgin//100
        orgin_col_idx = orgin - orgin_row_idx
        cross_col_num = 0

        distance, path = self._dijkstra(orgin, destination)

        if distance is not None and path is not None:
            target_node = path[-1]
            cross_col_num = target_node - target_node//100 - orgin_col_idx

        new_distance = (distance + 1)*self.unit_length + distance*self.unit_width + cross_col_num*self.col_span + padding

        return new_distance, path

class Wiring():
    def __init__(self):
        self.local_room = ""
        self.local_cabinet = ""
        self.local_unit = ""
        self.local_virtual_device_name = ""
        self.local_pyhsical_device_name = ""
        self.local_virtual_port = ""
        self.local_physical_port = ""
        self.remote_room = ""
        self.remote_cabinet = ""
        self.remote_unit = ""
        self.remote_virtual_device_name = ""
        self.remote_pyhsical_device_name = ""
        self.remote_virtual_port = ""
        self.remote_physical_port = ""
        self.carrier_link_type = ""
        self.carrier_link_lenght = 0
        self.carrier_link_path = None        


class NetWorkInfra():

    def __init__(self, name, room, topology):
        self.name = name
        self.room = room
        self.topology = None
        self.cabinet_cluster = None

    
    def wiring(self):
        links = self.topology.links()
        if links is None:
            return

        for (local_node, local_phy_devices_num, local_ports, remote_node, remote_phy_devices_num, remote_ports)  in links:
            local_cabinet = local_node.member[local_phy_devices_num].cabinet
            remote_cabinet = remote_node.member[remote_phy_devices_num].cabinet

            distance, wiring_path = self.room.wiring_path(start_cabinet=local_cabinet, target_cabinet=remote_cabinet)
        
            #根据物理端口修改堆叠后的端口名字
            #入F1/1/1 替换成 F2/1/1
            local_virtual_ports = list()
            if local_phy_devices_num > 1:
                for port in local_ports:
                    local_virtual_ports.append(re.sub("\d/", str(local_phy_devices_num)+"/", port, count=1))
            else:
                local_virtual_ports = local_ports

            remote_virtual_ports = list()
            if remote_phy_devices_num > 1:
                for port in remote_ports:
                    remote_virtual_ports.append(re.sub("\d/", str(remote_phy_devices_num)+"/", port, count=1))
            else:
                remote_virtual_ports = remote_ports
            

            carrier_link = Wiring()
            carrier_link.local_room = self.room.name
            carrier_link.local_cabinet = local_cabinet
            carrier_link.local_unit = local_node.member[local_phy_devices_num].unit
            carrier_link.local_virtual_device_name = local_node.name
            carrier_link.local_pyhsical_device_name = local_node.member[local_phy_devices_num].name
            carrier_link.local_virtual_port = local_virtual_ports
            carrier_link.local_physical_port = local_ports
            carrier_link.remote_room = self.room.name
            carrier_link.remote_cabinet = remote_cabinet
            carrier_link.remote_unit = remote_node.member[remote_phy_devices_num].unit
            carrier_link.remote_virtual_device_name = remote_node.name
            carrier_link.remote_pyhsical_device_name = remote_node.member[remote_phy_devices_num].name
            carrier_link.remote_virtual_port = remote_virtual_ports
            carrier_link.remote_physical_port = remote_ports
            carrier_link.carrier_link_type = None
            carrier_link.carrier_link_lenght = distance
            carrier_link.carrier_link_path = wiring_path

            yield carrier_link

        return


    def address_assign(self):
        pass

    def materiel(self):
        pass

    def server_links(self):
        pass

    def switch_config(self, type=None):
        pass

class Hierarchical():
    # layer from bottom to top

    def __init__(self):
        self.layers = list()
        self.depth = 0

    def add(self, layer):
        self._init_layers(layer)
        self.layers.append(layer)
        self.depth += 1

    def _init_layers(self, layer):
        if self.layers is []:
            return None       

        current_layer = self.layers[-1]

        # Case PartialLayer
        if current_layer is PartialLayer:
            if current_layer.node_count != layer.node_count:
                raise ValueMismatch("PartialLayer node num is mismatch with '%s' and '%s'" % (current_layer.node_count, layer.node_count))

        if layer.downlink is None:
            layer.downlink = current_layer.uplink

        elif current_layer.uplink != layer.downlink:
            raise ValueMismatch("Parameter 'uplink' and 'downlink' should be equal.")

        return None
        
    def links(self):
        if self.depth <= 1:
            return None

        _links = []

        for idx, layer in enumerate(self.layers[:-1]):
            if not layer.nodes:
                raise ValueError("Layer.nodes should not be null value.") 
            
            next_layer = self.layers[idx+1]

            remote_phy_devices_count = 0
            for node in next_layer:
                remote_phy_devices_count += len(node.member)

            loop_epoch = 0
            for idx_i, local_node in enumerate(layer.nodes):
                local_phy_devices = local_node.member

                if layer is PartialLayer:
                    remote_node = next_layer.nodes[idx_i].member
                    remote_phy_devices = remote_node.member
                    remote_phy_devices_num = len(remote_phy_devices)

                    remote_used_port_num = 0
                    for idx_y, local_phy_device in enumerate(local_phy_devices):
                        local_used_port_num = 0

                        local_ports = local_phy_device.uplink_ports
                        port_num_per_device = len(local_ports)/remote_phy_devices_num

                        for i in range(remote_phy_devices_num):
                            _links.append(( local_node,
                                            idx_y,
                                            local_phy_device.uplink_ports[local_used_port_num:port_num_per_device],
                                            remote_node,
                                            i,
                                            remote_phy_devices[i].downlink_ports[remote_used_port_num:port_num_per_device])
                                            )
                            local_used_port_num += port_num_per_device

                        remote_used_port_num += port_num_per_device


                if layer is MeshLayer:

                    for idx_y, local_phy_device in enumerate(local_phy_devices):
                        local_used_port_num = 0
                        for remote_node in next_layer.nodes:
                            remote_phy_devices = remote_node.member
                            remote_phy_devices_num = len(remote_phy_devices)
                            
                            port_num_per_remote_device = layer.uplink/len(local_phy_devices)/remote_phy_devices_num
                            remote_used_port_unmber = next_layer.downlink/remote_phy_devices_num * loop_epoch
                            for i in range(remote_phy_devices_num):
                                _links.append(( local_node,
                                                idx_y,
                                                local_phy_device.uplink_ports[local_used_port_num:port_num_per_remote_device],
                                                remote_node,
                                                i,
                                                remote_phy_devices[i].downlink_ports[remote_used_port_unmber:port_num_per_remote_device])
                                                )
                                
                                local_used_port_num += port_num_per_remote_device
                        
                            loop_epoch += 1
        return _links

class Layer():

    def __init__(self, node_count=0, uplink=0, downlink=None, nodes=None, name=None, inner_layer=None):
        if nodes is not None:
            nodes_num = len(nodes)
            if nodes_num != 0:
                self.node_count = nodes_num
            elif nodes_num == 0:
                raise ValueError("Parameter 'nodes' should not be 0 length.") 

            else:
                self.node_count = node_count

        self.uplink = uplink
        self.downlink = downlink
        self.nodes = nodes
        self.name = name
        self.inner_layer = inner_layer

    def set_nodes(self, nodes):
        if not nodes:
            raise ValueError("Parameter 'nodes' expects null value.") 

        nodes_num = len(nodes)

        if nodes_num != self.node_count:
            raise ValueError("Parameter 'nodes' should not be 0 length.") 

        if nodes_num != self.node_count:
            raise ValueMismatch("Length of 'nodes' is not equal to expected num '%s'." % self.node_count) 

        self.nodes = nodes


class PartialLayer(Layer):
    pass

class MeshLayer(Layer):
    pass


class VirtualDevice():
    def __init__(self, name, ip=None, role=None, service=None, member=None, soft_version=None, patch_version=None):
        self.name = name
        self.ip = ip
        self.role = role
        self.service = service
        self.member = member
        self.soft_version = soft_version
        self.patch_version = patch_version

    
class PhysicalDevice():
    def __init__(self, manufacturer=None, series=None, model=None, serial_no=None, cabinet=None, cabinet_name=None, unit=None, uplink_ports=None, downlink_ports=None):
        self.manufacturer = manufacturer
        self.series = series
        self.model = model
        self.serial_no = serial_no
        self.uplink_ports = uplink_ports
        self.downlink_ports = downlink_ports
        self.cabinet = cabinet
        self.cabinet_name = cabinet_name
        self.unit = unit

class ValueMismatch(Exception):
    pass



def device_placement(cabinets_array, cabinet_parameter=None, netdevice_placement=None):
    #cabinet_parameter, dict contains cabinet physical information
    # netdevice_placement like :
    #{
    #    "cabinet": [
    #        {
    #            "device_role": "LC",
    #            "device_name": "LC-1"
    #            "device_index" : 1,
    #            "manufacturer": "H3C",
    #            "uplink_ports": [],
    #            "downlink_ports" :[],    
    #        },
    #        {
    #            "device_role": "LA",
    #            "device_name": "LA-1"
    #            "device_index" : 1,
    #            "manufacturer": "H3C",
    #            "uplink_ports": [],
    #            "downlink_ports" :[],    
    #        },
    #    ]
    #}
    if cabinet_parameter is not None:
        width = cabinet_parameter["width"]
        length = cabinet_parameter["length"]
        height = cabinet_parameter["height"]
        max_unit = cabinet_parameter["max_unit"]
        access_count = cabinet_parameter["access_count"]
    else:
        width = 600
        length = 600
        height = 2000
        max_unit = 48
        access_count = 12

    cabinets = {}
    net_devices = {}
    server_devices = {}
    exclusive_cabinet = set()
    for row_idx, row in enumerate(cabinets_array):
        for col_idx, item in enumerate(row):
            cabinet_idx = row_idx*100 + col_idx

            if item == "":
                continue
            cabinet_name = item.strip()
            
            if cabinet_name not in cabinets:
                cabinets[cabinet_name] = Cabinet(cabinet_name, width, length, height, max_unit)

            if cabinet_name in netdevice_placement:
                for dev_idx, netdev in enumerate(netdevice_placement[cabinet_name]):
                    dev_name = netdev["device_name"]
                    dev_role = netdev["device_role"]

                    #独占柜子做标记，后面不放服务器
                    if dev_role in ("LC", "DCI", "WC"):
                        exclusive_cabinet.add(cabinet_name)

                    if dev_name not in net_devices:
                        net_devices[dev_name] = VirtualDevice(name=dev_name, 
                                                            role=dev_role
                                                            )
                    if net_devices[dev_name].member is None:
                        net_devices[dev_name].member = list()
                        if dev_role == "LC":
                            _unit = 1
                        else :
                            _unit = (max_unit - 1)- dev_idx 
                        _dev = PhysicalDevice(  cabinet=cabinet_idx, 
                                                cabinet_name=cabinet_name, 
                                                unit=_unit,
                                                uplink_ports=netdev["uplink_ports"],
                                                downlink_ports=netdev["downlink_ports"]
                                                )

                        net_devices[dev_name].member.append(_dev)
                        cabinets[cabinet_name].place[_unit] = _dev

            #网络设备独占的柜子不放服务器
            if cabinet_name in exclusive_cabinet:
                continue

            #规划服务器
            for idx in range(access_count):
                dev_name = "SRV" + str(cabinet_idx) + str(idx+1)
                if dev_name not in server_devices:
                    server_devices[dev_name] = VirtualDevice(name=dev_name, role=dev_name)
                if server_devices[dev_name].member is None:
                    server_devices[dev_name].member = list()
                    _dev = PhysicalDevice(cabinet=cabinet_idx, 
                                        cabinet_name=cabinet_name, 
                                        unit=idx+1,
                                        uplink_ports=["NIC1", "NIC2"]
                                        )
                    server_devices[dev_name].member.append(_dev)
                    cabinets[cabinet_name].place[idx+1] = _dev
    #
    #对成员设备排序
    #按照ascii 字符串排序，小的设备作为slot1，大的作为slot2
    #
    for _, virtual_device in net_devices.items():
        virtual_device.member.sort(key=lambda x: x.cabinet_name)
            
    return cabinets, net_devices, server_devices

if __name__ == "__main__":
    cabinets_columns = [["170", "171", "172", "173", "174", "175", "176", "177", "178", "179", "180", "181", "182", "183", "184", "185/LC", "186", "187", "188", "189"], 
["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",],
["150", "151", "152", "153", "154", "155", "156", "157", "158", "159", "160", "161", "162", "163", "164", "165", "166", "167", "168", "169"], 
["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",],
["130", "131", "132", "133", "134", "135", "136", "137", "138", "139", "140", "141", "142", "143", "144", "145/LC", "146", "147", "148", "149"]]

    distribution_area = [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]

    netdevice_placement_placement = {
        "157": [
            {
                "device_role": "LC",
                "device_name": "LC",
                "device_index" : 1,
                "manufacturer": "H3C",
                "uplink_ports": ["F1/0/49", "F1/0/50"],
                "downlink_ports" :None,    
            },
            {
                "device_role": "MNG",
                "device_name": "MNG-1",
                "device_index" : 1,
                "manufacturer": "H3C",
                "uplink_ports": ["G1/0/49"],
                "downlink_ports" :None,    
            },
        ],

        "177": [
            {
                "device_role": "LA",
                "device_name": "LA-1",
                "device_index" : 1,
                "manufacturer": "H3C",
                "uplink_ports": ["F1/0/49", "F1/0/50"],
                "downlink_ports" :None,    
            },
            {
                "device_role": "MNG",
                "device_name": "MNG-2",
                "device_index" : 1,
                "manufacturer": "H3C",
                "uplink_ports": ["G1/0/49"],
                "downlink_ports" :None,    
            },
        ],

        "137": [
            {
                "device_role": "LA",
                "device_name": "LA-2",
                "device_index" : 2,
                "manufacturer": "H3C",
                "uplink_ports": ["F1/0/49", "F1/0/50"],
                "downlink_ports" :None,      
            },
            {
                "device_role": "MNG",
                "device_name": "MNG-2",
                "device_index" : 2,
                "manufacturer": "H3C",
                "uplink_ports": ["G1/0/49"],
                "downlink_ports" :None,    
            },
        ],
    }
    #room = Room("02", cabinets=cabinets_columns, distribution_area=distribution_area)

    #distance, path = room.wiring_path(start_cabinet=(0,0), target_cabinet=(2,10), head_cabinet=(0, 19))

    cabinets, netdevice_placements, server_devices = device_placement(cabinets_array=cabinets_columns, netdevice_placement=netdevice_placement_placement)
