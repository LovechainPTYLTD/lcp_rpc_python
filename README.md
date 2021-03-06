# LCP RPC Server (in Python)
***must use at least Python 3***

conda is not necessary but prefered. 
create a conda enviroment

` conda create -n [environment name] python=3.7.4 pip=19.2.3 `

 other version of python and pip may also work but these are known to definitely work.

pip install requirements -r requirements.txt


## to start

input mnemonic phrase in LCPConstants.py file

python lcp_rpc.py [password]

## Commands

to send commands use the format:


` [server address]:5000/[command] `


example:


http://127.0.0.1:5000/get_witnesses


### /get_witnesses


` curl http://localhost:5000/get_witnesses `


### /send_transaction

``` 
curl -d '{
   "last_ball":"MHbriaJFqc2Wxj/UBWSOk6EpLNlnfe71aXWsOdVMz8U=",
   "last_ball_unit":"7yjsGAO3C1s5bmXePNy+JLD5XJvxX2BFmN3HpCYWp0w=",
   "parent_units":[
      "0O9uvGcF/sbVnTdfZkbfJcJVuQvVE6aIWk2f7SDZZnA="
   ],
   "witness_list_unit":"FxtHGkOHjv7aXajkg00/22Xp7VVXZEvT5cXfe8BSZEQ=",
   "alt":"1",
   "messages":[
      {
         "app":"payment",
         "payload_location":"inline",
         "payload_hash":"pXVXZVN5MRXhJZtHyGtadSu3DSnuKiUm8espRwBg7rs="
      }
   ],
   "version":"1.0",
   "authors":[
      {
         "authentifiers":{
            "r":"yPSkwrAQB0gZhN7JsYGb18+xaDcTWdnJQTkQTOl0A1U65wEKM+u172iBWJxQq+TDNhiNnzEQ6kea4QUEbt3TmA=="
         },
         "address":"3CVF7WEVOTUW5L3FTQOQL4P5J3D6IYOK"
      }
   ]
}' http://localhost:5000/send_transaction

```

post a transaction to the hub

### /get_address_history

curl -d "3CVF7WEVOTUW5L3FTQOQL4P5J3D6IYOK" http://localhost:5000/get_balances

get the history of transactions for a particular address 

### /get_balances

```
curl -d '["3CVF7WEVOTUW5L3FTQOQL4P5J3D6IYOK"]' http://localhost:5000/get_balances
```
determine the balance of an array of addresses

### /get_transaction_info

``` 
curl -d '0O9uvGcF/sbVnTdfZkbfJcJVuQvVE6aIWk2f7SDZZnA=' http://localhost:5000/get_transaction_info
```

get information related to a particular transaction and not a particular address


### /get_main_chain_index


` curl http://localhost:5000/get_main_chain_index `


### /get_transaction_history

```
curl -d '["3CVF7WEVOTUW5L3FTQOQL4P5J3D6IYOK"]' http://localhost:5000/get_transaction_history
```

### /prepare_transaction_header

```
curl http://localhost:5000/get_header_info
```

### /watch_address

```
curl '3CVF7WEVOTUW5L3FTQOQL4P5J3D6IYOK' http://localhost:5000/prepare_transaction_header
```

watch an address for changes. the hub will notify the light client.