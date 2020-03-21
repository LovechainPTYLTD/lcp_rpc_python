from crypto import HDPrivateKey, HDPublicKey, HDKey
import base64
import binascii
from bitstring import BitArray
import hashlib
import codecs
import pickle
import collections
class keyManagement(object):
    """
    generate keys for the LCP network.
    """
    @staticmethod
    def generateMasterKey(mnemonic, password=""):
        """
        Params:
            password <string> (optional)
        Returns:
            MasterKey <MasterKey>
        """
        return MasterKey(mnemonic, password)

    @staticmethod
    def exportKey(key,keyname,password):
            #encrypt object first
        outputFile = open('{}_encrypted.pkl'.format(keyname), 'wb')
        password = password
        pickle.dump(key,outputFile)
        outputFile.close()

    @staticmethod
    def importKey(filename):
        #password and decryption
        #make sure the file is loaded..check key integrity
        importedFile = open(filename,'rb')
        key = pickle.load(importedFile)
        return key

    @staticmethod
    def encrypt(data,password):
        pass

class MasterKey(object):
    """
    master key that generates a DeviceKey and WalletKeys. this is the root Key
    """
    def __init__(self, mnemonic, passphrase):
        self.key = HDPrivateKey.master_key_from_mnemonic(mnemonic, passphrase)
        self.mnemonic = mnemonic 
        #self.key, self.mnemonic = HDPrivateKey.master_key_from_entropy(password)

    #generate master key from mnemonic

    @classmethod
    def generate_from_entropy(cls, passphrase=""):
        key, mnemonic = HDPrivateKey.master_key_from_entropy(passphrase)
        return cls(mnemonic,passphrase)

    @property
    def fingerprint(self):
        return self.fingerprint

    def generateDeviceKey(self):
        keys = HDPrivateKey.from_path(self.key,"m/1'")
        return DeviceKey(keys[-1])

    def generateWalletKey(self,accountIndex=0):
        keys = HDPrivateKey.from_path(self.key,"m/44'/0'/{}'".format(accountIndex))
        return WalletKey(keys[-1])


class PrivateKey(object):
    """
    SuperClass for device and wallet keys
    """
    def __init__(self,key):
        self.key = key

    @property
    def publicKey(self):
        """
        returns:
        public_key <HDPublicKey>
        """
        return self.key.public_key

    @property
    def masterFingerprint(self):
        return self.key.parent_fingerprint

    def sign(self,message):
        return self.key.sign(message)


class DeviceKey(PrivateKey):
    """
    used to log into LCP network
    """
    def __init__(self,key):
        super().__init__(key)


class WalletKey(PrivateKey):
    """
    to send and receive coins.
    """
    def __init__(self,key):
        super().__init__(key)

    def generateChildWalletKey(self,index):
        return WalletKey(HDPrivateKey.from_parent(self.key,index))

    def generateAddressKey(self,index=0):
        """
        an AddressKey is an HDPublicKey that can be used to generate Addresses
        but can not sign transactions.
        params:
            index <hexadecimal> : value less than 0x80000000
        """
        return AddressKey(HDPrivateKey.from_parent(self.key,index).public_key)
       


class AddressKey(object):
    """
    just an unhardened public key used to generate public keys that will be used
    in releaseConditions that are hashed into addresses.
    """
    def __init__(self,key):
        self.key = key

    @property
    def compressedBytes(self):
        return self.key.compressed_bytes

    def generateChildKey(self,index=0):
        """
        an AddressKey is an HDPublicKey that can be used to generate Addresses
        but can not sign transactions.
        params:
            index <hexadecimal> : value less than 0x80000000
        """
        return HDPublicKey.from_parent(self.key,index)


class Addresses(object):

    @staticmethod
    def generateWalletAddress(publicKey,index, change=0):
        """
        generate an address from a releaseCondition and its checksum.
        does not generate addresses for harden keys
        conceptually a DEFINITION is boolean expression
        param:
        publicKey <HDPublicKey>
        index <Int>:  index of the key relative to master
        change <Int>(restricted: 0 or 1): is this a change address or otherwise.
        returns:
        address <string>
        """
        path = str(change)+"/"+str(index)
        derivedPubKey = publicKey.from_path(publicKey,path)
        b64PubKey = base64.b64encode(derivedPubKey[-1].compressed_bytes)
        releaseCondition = ["sig"]
        releaseCondition.append({"pubkey":b64PubKey.decode("utf-8")})
        #testCondition = ["sig",{"pubkey":"Ald9tkgiUZQQ1djpZgv2ez7xf1ZvYAsTLhudhvn0931w"}]
        releaseConditionString = Addresses._stringUtil(releaseCondition)
        addressHash = Addresses._generateHash(bytes(releaseConditionString,"utf8"))
        addressCore = Addresses._generateAddressCore(addressHash)
        return addressCore


    @staticmethod
    def generateDeviceAddress(publickKeyBytes):
        """
        generates a device address
        param:
        deviceKey <DeviceKey>

        returns:
        deviceAddress <string>
        """
        b64deviceKeyBytes = base64.b64encode(publickKeyBytes)
        b64deviceKeyStr = b64deviceKeyBytes.decode("utf-8")
        preImageString = Addresses._stringUtil(b64deviceKeyStr)
        keyHash = Addresses._generateHash(preImageString.encode("utf-8"))
        addressCore = Addresses._generateAddressCore(keyHash)
        deviceAddress = '0' + addressCore
        return deviceAddress


    @staticmethod
    def _generateAddressCore(hash_digest):
        """
        output core part that device and wallet addresses have in common
        params
        hash <byte>
        returns
        mixedData <bytes>
        """
        truncatedHash = hash_digest[4:]
        checksum = Addresses._generateChecksum(truncatedHash)
        mixedData = Addresses._mixData(truncatedHash,checksum)
        base32AddressCore = base64.b32encode(mixedData)
        return base32AddressCore.decode("utf-8")


    @staticmethod
    def _generateHash(data,algorithm="ripemd160"):
        """
        generates a hash digest
        param:
        data <Byte> :  data to be hashed
        algorithm <String> : ripemd160 or sha256
            ripemd160 - device addresses
            sha256 -receiving addresses
        returns:
        <bytes>
        """
        hashDigest = hashlib.new(algorithm, data).digest()
        return hashDigest


    @staticmethod
    def _generateChecksum(data):
        """
        byteball custom checksum function
        Param
        data <byte>
        Return
        checksum <byte>
        """
        digest = hashlib.sha256(data).digest()
        checksum = bytes([digest[5],digest[13],digest[21],digest[29]])
        return checksum


    @staticmethod
    def _mixData(digest, checksumBytes):
        """
        mixes data with checksum
        the original function from byteball manipulates string data and returns
        a string. this function manipulates Bits and returns a Bits

        params
        digest <String>
        checksumBytes <Bytes>
        returns
        mixedData <BitArray>
        """

        def _bytesToBinary(bytesData):
            """
            <bytes> -- > binary<string>
            returns
            <string>
            """
            binaryArray = []
            bitsArray = BitArray(bytesData)
            for index in range(len(bitsArray)):
                binaryArray.append(bitsArray[index].bin)
            return "".join(binaryArray)

        def _binaryToBytes(binaryString):
            """
            binaryData<string> --> <bytes>
            returns
            bytesData<bytes>
            raises
            - checksum length not 32
            - bad length
            """
            byteLength = len(binaryString)
            bytesData = bytearray()
            binaryStringArray = [binaryString[i:i+8] for i in range(0, byteLength, 8)]
            for index in range(len(binaryStringArray)):
                bytesData.append(int(binaryStringArray[index],2))
            return bytesData

        data = BitArray(digest)
        checksum = BitArray(checksumBytes)
        if len(checksum) != 32:
            raise Exception('checksum length is not 32')
        combinedLength = len(data) + len(checksum)
        if combinedLength == 160:
            offsets = Addresses._calculateOffsets(160)
        elif combinedLength == 288:
            offsets = Addresses._calculateOffsets(288)
        else:
            raise Exception("bad length")

        start = 0
        mixedDataBitArray = []#BitArray()
        dataBinary = data.bin#_bytesToBinary(data)
        checksumBinary = checksum.bin#_bytesToBinary(checksumBytes)
        checksumBits = list(checksumBinary)
        for index in range(len(offsets)):
            end = offsets[index] - index
            mixedDataBitArray.append(dataBinary[start:end])
            mixedDataBitArray.append(checksumBits[index])
            start = end

        if start < len(dataBinary):
            mixedDataBitArray.append(dataBinary[start:])

        mixedDataBinaryString = "".join(mixedDataBitArray)
        mixedDataBytes = _binaryToBytes(mixedDataBinaryString)
        return mixedDataBytes


    @staticmethod
    def _calculateOffsets(length):
        """
        calculate offset to be used in the mixing of checksum and clean data
        param:
        length <Int> : 160 or 288
        160 for device
        288 for wallet
        returns:
        offsets <Array (Int)>
        raises:
        unsupported length
        wrong number of checksum bits
        """
        if length != 160 and length != 288:
            raise Exception("unsupported length")

        PI = "14159265358979323846264338327950288419716939937510"
        relativeOffsets = [int(num) for num in list(PI)]
        index = 0
        offset = 0
        offsets = []
        for x in range(length):
            if relativeOffsets[x] == 0:
                continue
            offset += relativeOffsets[x]
            if length == 288:
                offset += 4
            if offset >= length:
                break
            offsets.append(offset)
            index += 1

        if index != 32:
            raise Exception("wrong number of checksum bits")

        return offsets


    @staticmethod
    def _stringUtil(preImage):
        """
        standardizes strings for hashing
        param:
            preImage <string,Number, boolean, object>:
            the preImage before it is sent to the hash function
        returns:
            stringPreImage <string>
        raises:
        - empty list
        -empty object
        """

        def _prependAndFlatten(element):
            """
            prepends values and flattens object so they have no nesting.
            """
            def _thisIs(archType):
                return isinstance(element,(archType))

            if (element is None):
                raise Exception("stringUtil preImage can not be None")
            elif (_thisIs(int)):
                componentsArray.extend(["n",element])
            elif (_thisIs(str)):
                componentsArray.extend(["s",element])
            elif (_thisIs(bool)):
                componentsArray.extend(["b",element])
            elif (_thisIs(list)):
                if len(element) == 0:
                    raise Exception("empty list")
                componentsArray.append("[")
                for elements in element:
                    _prependAndFlatten(elements)
                componentsArray.append("]")
            elif (_thisIs(dict)):
                if len(element) == 0 :
                    raise Exception("empty list")
                orderedDict = collections.OrderedDict(sorted(element.items()))
                for key in orderedDict:
                    if(key is None):
                        raise Exception("empty object")
                    componentsArray.append(key)
                    _prependAndFlatten(element[key])

        componentsArray = []
        stringJoinChar = "\u0000"
        _prependAndFlatten(preImage)
        return stringJoinChar.join(componentsArray)


