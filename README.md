# LCP RPC Server (in Python)
***must use at least Python 3***

conda is not necessary but prefered. 
create a conda enviroment

` conda create -n [environment name] python=3.7.4 pip=19.2.3 `

 other version of python and pip may also work but these are known to definitely work.

pip install requirements -r requirements.txt

## to start

python lcp_rpc.py [mnemonic phrase] [password]

## Commands

to send commands use the format:

` [server address]:5000/[commannd] `

example:

http://127.0.0.1:5000/get_witnesses

### /get_witnesses

### /send_transaction

### /get_balances

### /get_transaction_info

### /get_main_chain_index

### /get_transaction_history

### /prepare_transaction_header