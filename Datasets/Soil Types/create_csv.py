import os
clay=os.listdir('./test/clay')
for i in clay:
    print('/test/Clay/',i, ', clay',sep='')

sand=os.listdir('./test/Sand')
for i in sand:
    print('/test/Sand/',i, ', sand',sep='')

silt=os.listdir('./test/Silt')
for i in silt:
    print('/test/lit/',i, ', silt',sep='')

gravel=os.listdir('./test/Gravel')
for i in gravel:
    print('/test/Gravel/',i, ', gravel',sep='')

loam=os.listdir('./test/Loam')
for i in loam:
    print('/test/Loam/',i, ', loam',sep='')