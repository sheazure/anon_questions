key = "1001011010110101010101111010101101"

def for_ref(fr, key):
    fr = bin(int(fr))[2:]
    fr = "0"*(32-len(fr)) + fr
    fr = int(fr,2)
    return fr^key

encrypt = for_ref(1414141414,int(key,2))
decrypt = for_ref(encrypt, int(key, 2))
