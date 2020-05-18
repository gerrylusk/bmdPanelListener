#! /usr/bin/python3
##
## This will listen for Blackmagic router panels to connect and when
##    the panel changes an "output" it will send out an Eventmaster aux change.
##
## It's cobbled together from sample code with some goofy hacks thrown in.
##   feel free to use it as you like
##    and improve it as necessary.
##
##

EMhost = '192.168.0.175' # the address of the EM processor to change its auxes
myHost = '0.0.0.0' # my own address to listen. Also used for EM subscription
BMDport = 9990     # the port on which the panel talks
vRouting = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] # This holds the routing table

import socket
import socketserver
import threading
import json           # used in getEMauxes and sendEMaux for EventMaster
import urllib.request # used in getEMauxes and sendEMaux for EventMaster 

def EMrpc(host, method, params):
  EMurl = "http://" + host + ":9999"
  EMdata = '{"params":' + params + ', "method":"' + method + '", "id":"1234", "jsonrpc":"2.0"}'
  EMrequest = urllib.request.Request(EMurl, EMdata.encode(), {'Content-Type': 'application/json'})
  EMresponse = urllib.request.urlopen(EMrequest).read()
  try:
    return(json.loads(EMresponse)['result']['response'])
  except:
    return(json.loads(EMresponse))

def getEMauxes(): # Populate the routing table with the auxes found in EM
  global vRouting
  response = EMrpc(EMhost, 'listDestinations', '{"type":2}')
  EMdests = response['AuxDestination']
  print("Getting ", len(EMdests), " auxes from EM.")
  for aux in range(len(EMdests)):
    response = EMrpc(EMhost, 'listAuxContent', '{"id":' + str(aux) + '}')
    EMauxName = response['Name']
    EMauxPGM  = response['PgmLastSrcIndex']
    print(aux, EMauxName, EMauxPGM)
    if EMauxPGM != -1: vRouting[aux] = int(EMauxPGM)
  EMsubscribe()
  return()
  
def sendEMaux(auxID, source): # send the route change to the EM aux
  global vRouting
  print("Changing AUX ", auxID, "to ", source)
  response = EMrpc(EMhost, 'changeAuxContent', '{"id":' + str(auxID) + ', "PgmLastSrcIndex":' + str(source) + '}')
  print(response)
  return()

def EMsubscribe(): # subscribe to changes so we know when something else changes an aux
  if myHost != "0.0.0.0":
    print("Subscribing to aux change notices.\n")
    response = EMrpc(EMhost, 'subscribe', '{"hostname":"' + myHost + '", "port":"9990", "notification":["AUXDestChanged"]}')
    print(response)
  else:
    print("Can't subscribe to EM changes if my address is ", myHost)
  return()

def EMunsubscribe(): # unsubscribe from the EM notice
  if myHost != "0.0.0.0":
    print("Unubscribing to aux change notices.\n")
    response = EMrpc(EMhost, 'subscribe', '{"hostname":"' + myHost + '", "port":"9990", "notification":["AUXDestChanged"]}')
    print(response)
  else:
    print("Can't unsubscribe to EM changes if my address is ", myHost)
  return()

def vOutputMessage(vRouting): # turn the routing table in to an output message to send to the panel
  msg = "VIDEO OUTPUT ROUTING:\n"
  for out in range(len(vRouting)):
    msg += str(out)+" "+str(vRouting[out])+"\n"
  msg += "\n"
  return(msg)

class MyTCPClientHandler(socketserver.StreamRequestHandler):

  def handle(self):
    global vRouting
    print("Connection from: ", self.client_address)
    if self.client_address[0] == EMhost:
      print("It's EventMaster!")
    else:
      msg = "PROTOCOL PREAMBLE:\nVersion: 2.5\n\nVIDEOHUB DEVICE:\nDevice present: true\nModel name: Blackmagic Compact Videohub\nFriendly name: XP 40x40\nUnique ID: a1b2c3d4e5f6\nVideo inputs: 40\nVideo processing units: 0\nVideo outputs: 16\nVideo monitoring outputs: 0\nSerial ports: 0\n\nINPUT LABELS:\n0 Input 1\n1 Input 2\n2 Input 3\n3 Input 4\n4 Input 5\n5 Input 6\n6 Input 7\n7 Input 8\n8 Input 9\n9 Input 10\n10 Input 11\n11 Input 12\n12 Input 13\n13 Input 14\n14 Input 15\n15 Input 16\n16 Input 17\n17 Input 18\n18 Input 19\n19 Input 20\n20 Input 21\n21 Input 22\n22 Input 23\n23 Input 24\n24 Input 25\n25 Input 26\n26 Input 27\n27 Input 28\n28 Input 29\n29 Input 30\n30 Input 31\n31 Input 32\n32 Input 33\n33 Input 34\n34 Input 35\n35 Input 36\n36 Input 37\n37 Input 38\n38 Input 39\n39 Input 40\n\nOUTPUT LABELS:\n0 Output 1\n1 Output 2\n2 Output 3\n3 Output 4\n4 Output 5\n5 Output 6\n6 Output 7\n7 Output 8\n8 Output 9\n9 Output 10\n10 Output 11\n11 Output 12\n12 Output 13\n13 Output 14\n14 Output 15\n15 Output 16\n16 Output 17\n17 Output 18\n18 Output 19\n19 Output 20\n20 Output 21\n21 Output 22\n22 Output 23\n23 Output 24\n24 Output 25\n25 Output 26\n26 Output 27\n27 Output 28\n28 Output 29\n29 Output 30\n30 Output 31\n31 Output 32\n32 Output 33\n33 Output 34\n34 Output 35\n35 Output 36\n36 Output 37\n37 Output 38\n38 Output 39\n39 Output 40\n\n"+vOutputMessage(vRouting)
      print("It must be a BMD panel. Sending preamble.")
      self.request.sendall(msg.encode())

    while True : 
      data = self.request.recv(1024)
      dataItems = data.splitlines()
      if data and dataItems[0] == b'PING:':
        msg = "ACK\n\n"+vOutputMessage(vRouting)
      elif data and dataItems[0] == b'VIDEO OUTPUT ROUTING:':
        out = int(dataItems[1].split()[0])
        source = int(dataItems[1].split()[1])
        vRouting[out] = source
        msg = "ACK\n\n"+vOutputMessage(vRouting)
        sendEMaux(out, source)
      elif data and dataItems[0] == b'POST / HTTP/1.1':
        print("Got a POST.") # assuming it's EM telling us something has changed
        data = b''
        getEMauxes()
      else:
        msg = "default\n"

      if data:
        print("Server received data:", data)
        print("Sending ", msg)
        self.request.sendall(msg.encode())

if __name__ == "__main__":
  getEMauxes()
  TCPServerInstance = socketserver.ThreadingTCPServer((myHost, BMDport), MyTCPClientHandler)
  TCPServerInstance.serve_forever()  

