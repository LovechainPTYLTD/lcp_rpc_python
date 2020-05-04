import ast
import asyncio
import websockets
import json
from LCPHDkeys import keyManagement as keys
from LCPHDkeys import Addresses as addresses
from crypto import HDPrivateKey as hdprivate
import base64
import copy
import logging
import os
from blinker import signal
import sys
import LCPconstants
#forward errors
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
log = logging.getLogger(__name__)

"""
light get updates and also heartbeat
"""
class Connection(object):

    def __init__(self):
        self.witness_list_received_signal = signal('witness_list_received')
        self.transaction_status_received_signal = signal('transaction_status_recieved')
        self.balance_info_received_signal = signal('balance_info_received')
        self.transaction_id_data_received_signal = signal('transaction_id_data_received')
        self.index_info_recieved_signal = signal('index_info_received')
        self.address_history_received_signal = signal('address_history_received')
        self.header_info_received_signal = signal('header_received')
        self.logged_in_status_signal = signal('logged_in_info')
        self.watch_address_feedback_signal = signal('watched_address_feedback')
        self.challenge = None
       
       
    async def startConnection(self,uri="ws://bikihub.lovecoinplus.com"): #ws://13.59.6.90

        self._connection = websockets.connect(uri)
        self.websocket = await self._connection.__aenter__()
        #self.challenge_received_signal.connect(challenge_listener)
        if(self.websocket): 
            while True:
                message = await self.websocket.recv()
                await self.on_message(message)


    async def on_message(self, incomingMessage):
        print("routing\n")
        toBeRouted = json.loads(incomingMessage)
        if toBeRouted is None :
            pass
            
        elif (toBeRouted[0] == "justsaying"):
            await self.manageJustSaying(toBeRouted)

        elif (toBeRouted[0] == "request"):
            print("incoming request \n",toBeRouted[1])
            await self.manageRequests(toBeRouted[1])

        elif (toBeRouted[0] == "response"):
            await self.manageResponse(toBeRouted)
            

    async def manageResponse(self, messageFromHub):
        message = messageFromHub[1]
        print("this is the message \n",message)
        if(isinstance(message["response"],list)):
            self.witness_list_received_signal.send('witness_list',data=message["response"])

        elif(isinstance(message["response"],dict)):
            responseObjectKeys = message["response"].keys()
            if("unstable_mc_joints" in responseObjectKeys):#message["response"]["unstable_mc_joints"]
                print("address_history_received \n",message["response"])
                self.address_history_received_signal.send("transaction_info",data=message['response']['joints'])
            elif("parent_units" in responseObjectKeys):#message["response"]["parent_units"]
                self.header_info_received_signal.send('header_info',data=message['response'])
            elif("error" in responseObjectKeys):
                #self.transaction_status_received_signal.send('transaction_error',data=message['response'])
                print(message['response'])
            elif("accepted" in responseObjectKeys):
                self.transaction_status_received_signal.send('transaction accepted',data=message['response'])
            self.balance_info_received_signal.send('balance_info', data=message['response'])

        elif(isinstance(message["response"],int)):
            self.index_info_recieved_signal.send('index_info',data=message['response'])


    async def manageJustSaying(self, messageFromHub):
        message = messageFromHub[1]
        if (message["subject"] == "hub/challenge"):
            self.challenge = message["body"]
            print(message)
            print("managing hub challenge ")
            print(self.challenge)
            #self.challenge_received_signal.send("challenge_received",data=self.challenge)
            signature,pubkey = self.getSignature(self.challenge)
            loginMessage = {"challenge":self.challenge,"pubkey":pubkey,"signature":signature}
            await self.handleLoginChallenge(loginMessage) 

        elif(message["subject"]=="joint"):
            self.transaction_id_data_received_signal.send('transaction_id_info',data=message['body'])
        else:
            print(messageFromHub)


    async def handleHeartbeat(self, tag):
        print("sending heartbeat with tag ",tag,"\n")
        await self.sendResponse("heartbeat",tag)


    async def manageRequests(self,messageFromHub):
        print("this the message from the hub:\n ",messageFromHub)
        if(messageFromHub["command"]=="heartbeat"):
            print("heartbeat request received. managing \n")
            await self.handleHeartbeat(messageFromHub["tag"])
 

    async def sendJSmessage(self,route,content):
        message = {"subject":route,"body":content}
        messageArray = ["justsaying",message]
        messageStr = json.dumps(messageArray)
        await self.websocket.send(messageStr)


    async def sendRequest(self, command, params = None):
        
        message = {"command":command}
        if(params != None):
            message["params"] = params

        elif(command=="heartbeat"):
            message["tag"] = params

        messageArray = ["request",message]
        print("message array \n",messageArray)
        messageStr = json.dumps(messageArray)
        await self.websocket.send(messageStr)


    async def sendResponse(self,command,info):
        
        if(command=="heartbeat"):
            message={"command":"heartbeat"}
            message["tag"]= info
        messageArray = ["response",message]
        messageStr = json.dumps(messageArray)
        await self.websocket.send(messageStr)


    async def sendTransaction(self, transaction,transaction_status_listener):
        self.transaction_status_received_signal.connect(transaction_status_listener)
        unitObject = {"unit":transaction}
        #print("transaction to send")
        response = await self.sendRequest("post_joint", unitObject)


    def getSignature(self,challenge):
        masterKey = keys.generateMasterKey(LCPconstants.MNEMONIC,password="")
        dKey = masterKey.generateWalletKey()
        pbKeyBytes = dKey.key.public_key.compressed_bytes
        ba = pbKeyBytes.hex()
        print("pub key bytes in hex\n",ba)
        pbKeyb64 = base64.b64encode(pbKeyBytes)
        print("public key base64\n",pbKeyb64)
        challengeObject = {"challenge":challenge,"pubkey":str(pbKeyb64,"utf-8")}
        challengeObjectStr = addresses._stringUtil(challengeObject)
        challengeBytes = bytearray(challengeObjectStr,"utf-8")
        challengeSHA256 = addresses._generateHash(challengeBytes,algorithm="sha256")
        signedChallenge = dKey.key.sign(challengeSHA256,do_hash=False).__bytes__()
        b64sig = base64.b64encode(signedChallenge)
        signatureStr = str(b64sig,"utf-8")

        return signatureStr, str(pbKeyb64,"utf-8")

    
    async def handleLoginChallenge(self, loginMessage):
        #self.logged_in_status_signal.connect(logged_in_listener)
        await self.sendJSmessage("hub/login",loginMessage)


    async def getWitnesses(self,witness_list_listener):
        self.witness_list_received_signal.connect(witness_list_listener)
        await self.sendRequest("get_witnesses")
    

    async def getTransactionIdInfo(self,transaction_id, transaction_id_info_listener):
        self.transaction_id_data_received_signal.connect(transaction_id_info_listener)
        await self.sendRequest("get_joint",transaction_id)


    async def getAddressBalance(self, addresses_list, balance_listener):
        self.balance_info_received_signal.connect(balance_listener)
        await self.sendRequest("light/get_balances",addresses_list)


    async def getMainChainIndex(self, index_info_listener):
        self.index_info_recieved_signal.connect(index_info_listener)
        await self.sendRequest("get_last_mci")


    async def getAddressHistory(self, addresses, address_history_listener):
        print("addresses\n",addresses)
        self.address_history_received_signal.connect(address_history_listener)
        transaction_query_params = {"addresses":addresses,"witnesses":LCPconstants.WITNESSES,"last_stable_mci":0}
        print("transaction history params\n ",transaction_query_params)
        await self.sendRequest("light/get_history",transaction_query_params)
        

    async def prepareTransactionHeader(self, witness_list, transaction_header_listener):
        self.header_info_received_signal.connect(transaction_header_listener)
        params = {"witnesses":witness_list}
        await self.sendRequest('light/get_parents_and_last_ball_and_witness_list_unit',params)


    async def watchAddress(self, address_string, watched_address_listener):
        self.watch_address_feedback_signal.connect(watched_address_listener)
        await self.sendJSmessage('light/new_address_to_watch',address_string)
    







