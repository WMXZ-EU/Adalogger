def sign_extend(x):
    y=memoryview(x)
    y1=y.cast('L')
    for i in range(len(y1)): y1[i] <<=1

    sign_bit=1<<30
    mask=sign_bit-1
    for ii in range(len(x)):
        x[ii] = (x[ii] & mask) - (x[ii] & sign_bit)

def buffer_extract(x,y,j=0):
    x_mv=memoryview(x)
    y_mv=memoryview(y)
    for i in range(len(y)):
        y[i]=x[2*i+j]
