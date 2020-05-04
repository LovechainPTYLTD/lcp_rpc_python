from LCPHDkeys import keyManagement as keys
from LCPHDkeys import Addresses as addresses
from crypto import HDPrivateKey as hdprivate
import LCPconstants
import base64

masterKey = keys.generateMasterKey(LCPconstants.MNEMONIC,password="")
walletKey = masterKey.generateWalletKey()
addressKey = walletKey.generateAddressKey(0)
pbKeyBytes = walletKey.key.public_key.compressed_bytes
pbKeyBytesHex = pbKeyBytes.hex()
print("wallet pub key bytes in hex\n",pbKeyBytesHex)
pbKeyb64 = base64.b64encode(pbKeyBytes)
print("wallet public key base64\n",pbKeyb64)

addressKey = addressKey.key.public_key.compressed_bytes


testString = "nignog"
testStringBytes = bytearray(testString,"utf-8")
testStringSHA256 = addresses._generateHash(testStringBytes,algorithm="sha256")
print("test string sha256 hash,\n ",testStringSHA256)

signedTestString = walletKey.key.sign(testStringSHA256,do_hash=False).__bytes__()
b64sig = base64.b64encode(signedTestString)

signatureStr = str(b64sig,"utf-8")
print("signature b64 str \n ", signatureStr)
print("signature hex,\n ",signedTestString.hex())