from quart import Quart, request, Response
from LCPNetwork import Connection
import asyncio
from blinker import signal
from LCPHDkeys import keyManagement as keys
from LCPHDkeys import Addresses as walletAddresses
import json
import LCPconstants

class Listener(object):
    
    def __init__(self):
        self.data_received = False
        self.marker = asyncio.Event()

    def setData(self,source, data):
        self.source = source
        self.data = data
        self.marker.set()
        
    def getData(self):
        if(self.data):
            return self.data

app = Quart(__name__)
wsConn = Connection()

@app.before_serving
async def startup():
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(wsConn.startConnection())
    

@app.route('/get_hub_challenge')
async def get_hub_challenge():
    
    return wsConn.challenge


@app.route('/send_challenge',methods=['POST'])
async def send_challenge():
    logged_in_listener = Listener()
    login_challenge_bytes = await request.get_data()
    transaction = login_challenge_bytes.decode("utf-8")
    print("this is the challenge ", transaction)
    await wsConn.handleLoginChallenge(transaction,logged_in_listener.setData)
    await logged_in_listener.marker.wait()
    transaction_info = logged_in_listener.marker.getData()
    return str(transaction_info) +"\n"


@app.route('/get_witnesses')
async def get_witnesses():
    witness_listener = Listener()
    await wsConn.getWitnesses(witness_listener.setData)
    await witness_listener.marker.wait()
    witnesses = witness_listener.getData()
    return str(witnesses) + "\n"


@app.route('/send_transaction',methods=['POST'])
async def send_transaction():
    transaction_listener = Listener()
    transaction_bytes = await request.get_data()
    transaction = transaction_bytes.decode("utf-8")
    print("this is the transaction ", transaction)
    await wsConn.sendTransaction(transaction, transaction_listener.setData)
    await transaction_listener.marker.wait()
    transaction_info = transaction_listener.getData()
    return str(transaction_info) +"\n"


@app.route('/get_balances',methods=['POST'])
async def get_balances():
    balance_listener = Listener()
    addresses_bytes = await request.get_data()
    addresses_string = addresses_bytes.decode("utf-8")
    addresses_list = json.loads(addresses_string)
    #print("this is the balance ", type(addresses_list))
    await wsConn.getAddressBalance(addresses_list, balance_listener.setData)
    await balance_listener.marker.wait()
    balance_info = balance_listener.getData()
    return str(balance_info) + "\n"


@app.route('/get_transaction_info',methods=['POST'])
async def get_transaction_info():
    transaction_id_info_listener = Listener()
    transaction_id_info_bytes = await request.get_data()
    transaction_id_string = transaction_id_info_bytes.decode("utf-8")
    await wsConn.getTransactionIdInfo(transaction_id_string,transaction_id_info_listener.setData)
    await transaction_id_info_listener.marker.wait()
    transaction_id_info = transaction_id_info_listener.getData()
    return str(transaction_id_info) +"\n"


@app.route('/get_main_chain_index')
async def get_index():
    index_info_listener = Listener()
    await wsConn.getMainChainIndex(index_info_listener.setData)
    await index_info_listener.marker.wait()
    index = index_info_listener.getData()
    return str(index)+"\n"

@app.route('/get_transaction_history',methods=['POST'])
async def get_transaction_history():

    def verify_parameters(transaction_info):
        pass 

    transaction_history_listener = Listener()
    transaction_query_bytes = await request.get_data()
    transaction_query_string = transaction_query_bytes.decode("utf-8")
    transaction_query_dict = json.loads(transaction_query_string)
    transaction_query_dict["witnesses"] = LCPconstants.WITNESSES
    await wsConn.getTransactionHistory(transaction_query_dict,transaction_history_listener.setData)
    await transaction_history_listener.marker.wait()
    transaction_history = transaction_history_listener.getData()
    return str(transaction_history) +"\n"


@app.route('/prepare_transaction_header')
async def prepare_transaction_header():
    transaction_header_info_listener = Listener()
    await wsConn.prepareTransactionHeader(LCPconstants.WITNESSES,transaction_header_info_listener.setData)
    await transaction_header_info_listener.marker.wait()
    transacion_header = transaction_header_info_listener.getData()
    return str(transacion_header) + "\n"

app.run()