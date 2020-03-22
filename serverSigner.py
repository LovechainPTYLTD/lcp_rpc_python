from LCPHDkeys import keyManagement as keys
import sys
import base64
from LCPHDkeys import Addresses as addresses

masterKey = keys.generateMasterKey("glory donate cheese direct soda recycle tenant crystal curious dance paper pyramid")
dKey = masterKey.generateDeviceKey()
def getSignature(challenge):#put this in a seperate file
    print('this is the challenge \n',challenge,type(challenge))
    pbKeyBytes = dKey.key.public_key.compressed_bytes
    pbKeyb64 = base64.b64encode(pbKeyBytes)
    challengeObject = {"challenge":challenge,"pubkey":str(pbKeyb64,"utf-8")}
    challengeObjectStr = addresses._stringUtil(challengeObject)
    challengeBytes = bytearray(challengeObjectStr,"utf-8")
    challengeSHA256 = addresses._generateHash(challengeBytes,algorithm="sha256")
    signedChallenge = dKey.key.sign(challengeSHA256,do_hash=False).__bytes__()
    b64sig = base64.b64encode(signedChallenge)
    signatureStr = str(b64sig,"utf-8")

    return signatureStr, str(pbKeyb64,"utf-8")

signature, pubkey = getSignature(sys.argv[1])
loginMessage = {'challenge':sys.argv[1],'pubkey':pubkey,'signature':signature}
print(loginMessage)

#print(getSignature(sys.argv[0]))