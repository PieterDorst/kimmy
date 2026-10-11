import json,struct,numpy as np
CT={5126:np.float32,5123:np.uint16,5125:np.uint32,5121:np.uint8}
NC={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def load(path):
    f=open(path,'rb').read()
    l=struct.unpack('<I',f[12:16])[0]; j=json.loads(f[20:20+l])
    o=20+l; bl=struct.unpack('<I',f[o:o+4])[0]; b=f[o+8:o+8+bl]
    return j,b
def acc(j,b,i):
    a=j['accessors'][i]; bv=j['bufferViews'][a['bufferView']]
    n=NC[a['type']]; dt=CT[a['componentType']]
    st=bv.get('byteStride'); off=bv.get('byteOffset',0)+a.get('byteOffset',0)
    if st and st!=n*np.dtype(dt).itemsize:
        raw=np.frombuffer(b,np.uint8,a['count']*st,off).reshape(-1,st)[:,:n*np.dtype(dt).itemsize]
        return np.frombuffer(raw.tobytes(),dt).reshape(a['count'],n)
    return np.frombuffer(b,dt,a['count']*n,off).reshape(a['count'],n).copy()
