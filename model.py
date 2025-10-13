import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
import lightgbm as lgb

data = pd.read_csv('final.csv')
X = data[['남은 시간', '학습 진도율', '가중치']]
y = data['우선순위 점수']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

lgbm = lgb.LGBMRegressor(random_state=42)
lgbm.fit(X_train, y_train)
print('모델훈련완료')

pred = lgbm.predict(X_test)

rmse = np.sqrt(mean_squared_error(y_test, pred))
print(f'예측 성능 RMSE : {rmse}')