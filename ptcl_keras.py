# -*- coding: utf-8 -*-
"""
Created on Mon Mar 29 11:30:37 2021

@author: 박태혁
"""

import Ptcl
import time
import numpy as np
#from google.colab import drive
#drive.mount('/gdrive', force_remount=True) 

data = Ptcl.Ptcl('./ptcls/ptcl_UTLZ_1706271379062.csv')
X_train_org,X_test_org,y_train,y_test = data.load_ptcl(10000,
    ['card_no', 
     'dvsn_cd', 
     'card_tpbz_nm', 
     'buy_sum',
     'apv_dt', 
     #'mest_nm',
     #'user_no', 
     #'dow', 
     #'x', 
     #'y', 
     #'apv_tm',    
     ])
print("데이터 로드 완료.................")
start = time.time()

from sklearn.preprocessing import StandardScaler
ss = StandardScaler()
ss.fit(X_train_org)
X_train = ss.transform(X_train_org)
X_test = ss.transform(X_test_org)

from keras import models, layers, regularizers
feature_len = X_train.shape[1]
label_len = y_train.shape[1]
model = models.Sequential()
reg_factor = 0.00005
model.add(layers.Dense(label_len*64,
                       kernel_initializer='lecun_normal',
                       #kernel_regularizer=regularizers.l1_l2(l1=reg_factor, l2=reg_factor),
                       activation='relu', 
                       input_shape=(feature_len,)))
model.add(layers.Dropout(0.3))
model.add(layers.Dense(label_len*32, 
                       kernel_initializer='lecun_normal',
                       #kernel_regularizer=regularizers.l1_l2(l1=reg_factor, l2=reg_factor),
                       activation='relu', 
                       input_shape=(feature_len,)))
model.add(layers.Dropout(0.3))
model.add(layers.Dense(label_len, 
                       activation='softmax'))

model.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics=['accuracy'])

val_len = int(len(X_train)/10)
x_val = X_train[:val_len]
partial_x_train = X_train[val_len:]

y_val = y_train[:val_len]
partial_y_train = y_train[val_len:]

print("학습시작.................")
history = model.fit(partial_x_train, partial_y_train, 
                    epochs=100, batch_size=512, 
                    validation_data=(x_val, y_val), verbose=1)

print("수행시간 : ", time.time() - start)

import tensorflowjs as tfjs
tfjs.converters.save_keras_model(model, '.')

import matplotlib.pyplot as plt

acc = history.history['accuracy']
val_acc = history.history['val_accuracy']

epochs = range(1, len(acc) + 1)

plt.plot(epochs, acc, 'bo', label='Training acc')
plt.plot(epochs, val_acc, 'b', label='Validation acc')
plt.title('Training and validation accuracy')
plt.xlabel('Epochs')
plt.ylabel('accuracy')
plt.legend()
#plt_text = data.file_path
#plt.text(20, 100, plt_text)
plt.show()

print("훈련데이터 갯수:{0}".format(len(X_train)))
print("훈련특성 갯수:{0}".format(X_train.shape[1]))

test_loss, test_acc = model.evaluate(X_test, y_test)

pr = model.predict(X_test)
ptcl_result = data.ptcl_org.loc[X_test_org.index, :]
ptcl_result['pr_1_rate'] = np.amax(pr, 1)
amax = np.eye(pr.shape[1])[pr.argmax(axis=1).reshape(-1)]
ptcl_result['pr_1'] = data.enc.inverse_transform(amax)

acc = (ptcl_result[ptcl_result['tran_kind_nm'] == 
                   ptcl_result['pr_1']]).shape[0] / ptcl_result.shape[0]
print("1개 정확도 : {:.2f}%".format(acc*100))

pr2 = pr*(1-amax)
ptcl_result['pr_2_rate'] = np.amax(pr2, 1)
amax = np.eye(pr2.shape[1])[pr2.argmax(axis=1).reshape(-1)]
ptcl_result['pr_2'] = data.enc.inverse_transform(amax)

acc = ((ptcl_result[ptcl_result['tran_kind_nm'] == ptcl_result['pr_1']]).shape[0] 
    +  (ptcl_result[ptcl_result['tran_kind_nm'] == ptcl_result['pr_2']]).shape[0]) / ptcl_result.shape[0]
print("2개 정확도 : {:.2f}%".format(acc*100))

pr3 = pr2*(1-amax)
ptcl_result['pr_3_rate'] = np.amax(pr3, 1)
amax = np.eye(pr3.shape[1])[pr3.argmax(axis=1).reshape(-1)]
ptcl_result['pr_3'] = data.enc.inverse_transform(amax)

acc = ((ptcl_result[ptcl_result['tran_kind_nm'] == ptcl_result['pr_1']]).shape[0]
    +  (ptcl_result[ptcl_result['tran_kind_nm'] == ptcl_result['pr_2']]).shape[0]
    +  (ptcl_result[ptcl_result['tran_kind_nm'] == ptcl_result['pr_3']]).shape[0]) / ptcl_result.shape[0]
print("3개 정확도 : {:.2f}%".format(acc*100))



ptcl_result.to_csv('ptcl_result.csv', encoding='utf-8') 