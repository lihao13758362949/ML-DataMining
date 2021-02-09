'''
集成学习 ensemble.py
输入：splits,metrics,X_test
输出：score（cv_score或）,res,模型（feature_importance，best_iteration）

'''
from sklearn import datasets  
from sklearn import model_selection  
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier  
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import VotingClassifier
import numpy as np



# <Voting> 简单投票法
# 载入数据集
iris = datasets.load_iris()  
# 只要第1,2列的特征
x_data, y_data = iris.data[:, 1:3], iris.target  

# 定义三个不同的分类器
clf1 = KNeighborsClassifier(n_neighbors=1)  
clf2 = DecisionTreeClassifier() 
clf3 = LogisticRegression()  

sclf = VotingClassifier([('knn',clf1),('dtree',clf2), ('lr',clf3)])   
# VotingClassifier(estimators, voting=’hard’, weights=None, n_jobs=None, flatten_transform=True)
# voting：默认hard表示绝对多数投票法，即选择超过半数的票数；若为soft表示相对多数投票法，即选择最多票数。
#VotingRegressor(estimators, weights=None, n_jobs=None) 
for clf, label in zip([clf1, clf2, clf3, sclf],
                      ['KNN','Decision Tree','LogisticRegression','VotingClassifier']):  
  
    scores = model_selection.cross_val_score(clf, x_data, y_data, cv=3, scoring='accuracy')  
    print("Accuracy: %0.2f [%s]" % (scores.mean(), label)) 
   
  
  
  
  
# <简单的平均>
class AveragingModels(BaseEstimator, RegressorMixin, TransformerMixin):
    def __init__(self, models):
        self.models = models
        
    # we define clones of the original models to fit the data in
    def fit(self, X, y):
        self.models_ = [clone(x) for x in self.models]
        
        # Train cloned base models
        for model in self.models_:
            model.fit(X, y)

        return self
    
    #Now we do the predictions for cloned models and average them
    def predict(self, X):
        predictions = np.column_stack([
            model.predict(X) for model in self.models_
        ])
        return np.mean(predictions, axis=1)
        
        
        
        
        
# <用基学习器的预测结果作为输入训练二级学习器>
class StackingAveragedModels(BaseEstimator, RegressorMixin, TransformerMixin):
    def __init__(self, base_models, meta_model, n_folds=5):
        self.base_models = base_models
        self.meta_model = meta_model
        self.n_folds = n_folds
   
    # We again fit the data on clones of the original models
    def fit(self, X, y):
        self.base_models_ = [list() for x in self.base_models]
        self.meta_model_ = clone(self.meta_model)
        kfold = KFold(n_splits=self.n_folds, shuffle=True, random_state=156)
        
        # Train cloned base models then create out-of-fold predictions
        # that are needed to train the cloned meta-model
        out_of_fold_predictions = np.zeros((X.shape[0], len(self.base_models)))
        for i, model in enumerate(self.base_models):
            for train_index, holdout_index in kfold.split(X, y):
                instance = clone(model)
                self.base_models_[i].append(instance)
                instance.fit(X[train_index], y[train_index])
                y_pred = instance.predict(X[holdout_index])
                out_of_fold_predictions[holdout_index, i] = y_pred
                
        # Now train the cloned  meta-model using the out-of-fold predictions as new feature
        self.meta_model_.fit(out_of_fold_predictions, y)
        return self
   
    #Do the predictions of all base models on the test data and use the averaged predictions as 
    #meta-features for the final prediction which is done by the meta-model
    def predict(self, X):
        meta_features = np.column_stack([
            np.column_stack([model.predict(X) for model in base_models]).mean(axis=1)
            for base_models in self.base_models_ ])
        return self.meta_model_.predict(meta_features)
      
      
# 1 <Boosting>
# >能够降低模型的bias，迭代地训练 Base Model，每次根据上一个迭代中预测错误的情况修改训练样本的权重。也即 Gradient Boosting 的原理。比 Bagging 效果好，但更容易 Overfit。
## 1.1 <AdaBoost>
# >提高前一轮弱分类器错误分类样本的权值，降低被正确分类样本的权值。
# >加权投票法组合分类器
AdaBoostRegressor(base_estimator=None, n_estimators=50, learning_rate=1.0, loss=’linear’, random_state=None)
AdaBoostClassifier(base_estimator=None, n_estimators=50, learning_rate=1.0, algorithm=’SAMME.R’, random_state=None)
'''
n_estimators：基学习器数量
base_estimator：基学习器类型，默认`.tree.DecisionTreeRegressor(max_depth=3)`
'''

## 1.2 <boosting tree>（提升树）
# >提升树算法（向前分布算法，逐渐减少残差） 
# >注：提升树算法仅在损失函数为平方误差损失函数时适用



## 1.3 <Gradient Boosting Decision Tree> （GBDT，梯度提升树）
# >一般化的提升树算法
GradientBoostingClassifier(loss=’deviance’, learning_rate=0.1, n_estimators=100, subsample=1.0, criterion=’friedman_mse’, min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0, max_depth=3, min_impurity_decrease=0.0, min_impurity_split=None, init=None, random_state=None, max_features=None, verbose=0, max_leaf_nodes=None, warm_start=False, presort=’auto’, validation_fraction=0.1, n_iter_no_change=None, tol=0.0001)
GradientBoostingRegressor(loss=’ls’, learning_rate=0.1, n_estimators=100, subsample=1.0, criterion=’friedman_mse’, min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0, max_depth=3, min_impurity_decrease=0.0, min_impurity_split=None, init=None, random_state=None, max_features=None, alpha=0.9, verbose=0, max_leaf_nodes=None, warm_start=False, presort=’auto’, validation_fraction=0.1, n_iter_no_change=None, tol=0.0001)

## 1.4 <XGBoost>

## 1.5 <LightGBM>
import numpy as np
import pandas as pd
import lightgbm as lgb

lgb_param = {
    'task' : 'train',
    'boosting_type' : 'gbdt',
    'objective' : 'binary',
    'metric' : {'binary_error'},
    'num_leaves' : 120,
    'learning_rate' : 0.02,
    'feature_fraction' : 0.7,
    'bagging_fraction' : 0.7,
    'bagging_freq' : 5,
    # 'min_data_in_leaf' : 10,
    'verbose' : 0
}

cv_score = []
res = np.zeros(X_test.shape[0])

for idx,(train_idx,val_idx) in enumerate(splits):
    print('-'*50)
    print('iter{}'.format(idx+1))
    X_trn,y_trn = X_train[train_idx],y_train[train_idx]
    X_val,y_val = X_train[val_idx],y_train[val_idx]

    dtrn = lgb.Dataset(X_trn,label=y_trn)
    dval = lgb.Dataset(X_val, label=y_val)

    bst = lgb.train(lgb_param,dtrn,500000,valid_sets=dval,
                    early_stopping_rounds=150,verbose_eval=50)
    preds = bst.predict(X_val,num_iteration=bst.best_iteration)
    lgb_pred[val_idx] = preds

    preds = transform(preds)

    score = accuracy_score(y_val,preds)
    print(score)
    cv_score.append(score)
    res += transform(bst.predict(X_test,num_iteration=bst.best_iteration)) # 输出时要改为0或1

    dfFeature = pd.DataFrame()
    dfFeature['featureName'] = train[feature].columns
    dfFeature['score'] = bst.feature_importance()
    dfFeature = dfFeature.sort_values(by='score',ascending=False)
    dfFeature.to_csv('featureImportance.csv',index=False,sep='\t')
    print(dfFeature)
    
print('offline mean ACC score:',np.mean(cv_score))
    
    
    
    

3. `.BaggingClassifier(base_estimator=None, n_estimators=10, max_samples=1.0, max_features=1.0, bootstrap=True, bootstrap_features=False, oob_score=False, warm_start=False, n_jobs=None, random_state=None, verbose=0)`
4. `.BaggingRegressor(base_estimator=None, n_estimators=10, max_samples=1.0, max_features=1.0, bootstrap=True, bootstrap_features=False, oob_score=False, warm_start=False, n_jobs=None, random_state=None, verbose=0)`

7. `.ExtraTreesClassifier(n_estimators=’warn’, criterion=’gini’, max_depth=None, min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0, max_features=’auto’, max_leaf_nodes=None, min_impurity_decrease=0.0, min_impurity_split=None, bootstrap=False, oob_score=False, n_jobs=None, random_state=None, verbose=0, warm_start=False, class_weight=None)`
8. `.ExtraTreesRegressor(n_estimators=’warn’, criterion=’mse’, max_depth=None, min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0, max_features=’auto’, max_leaf_nodes=None, min_impurity_decrease=0.0, min_impurity_split=None, bootstrap=False, oob_score=False, n_jobs=None, random_state=None, verbose=0, warm_start=False)`

13. `.HistGradientBoostingClassifier(loss=’auto’, learning_rate=0.1, max_iter=100, max_leaf_nodes=31, max_depth=None, min_samples_leaf=20, l2_regularization=0.0, max_bins=256, scoring=None, validation_fraction=0.1, n_iter_no_change=None, tol=1e-07, verbose=0, random_state=None)`：数据量较大时效果比`GradientBoostingClassifier`好得多。
14. `.HistGradientBoostingRegressor(loss=’least_squares’, learning_rate=0.1, max_iter=100, max_leaf_nodes=31, max_depth=None, min_samples_leaf=20, l2_regularization=0.0, max_bins=256, scoring=None, validation_fraction=0.1, n_iter_no_change=None, tol=1e-07, verbose=0, random_state=None)`




# 2 <Bagging>

## RF随机森林
### 随机森林的优点：防过拟合、抗噪声、无需规范化、速度快、
### 随机森林的缺点：某些噪声过大的问题上会过拟合、对取值多的变量有偏好，因此属性权值不可信
# `.RandomForestClassifier(n_estimators=’warn’, criterion=’gini’, max_depth=None, min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0, max_features=’auto’, max_leaf_nodes=None, min_impurity_decrease=0.0, min_impurity_split=None, bootstrap=True, oob_score=False, n_jobs=None, random_state=None, verbose=0, warm_start=False, class_weight=None)`
# `.RandomForestRegressor(n_estimators=’warn’, criterion=’mse’, max_depth=None, min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0, max_features=’auto’, max_leaf_nodes=None, min_impurity_decrease=0.0, min_impurity_split=None, bootstrap=True, oob_score=False, n_jobs=None, random_state=None, verbose=0, warm_start=False)`
from sklearn.ensemble import RandomForestClassifier
clf = RandomForestClassifier(n_estimators=100)
clf.fit(X_train,y_train) 
# 随机森林的可解释性
importances = clf.feature_importances_
#计算随机森林中所有的树的每个变量的重要性的标准差 
std = np.std([tree.feature_importances_ for tree in clf.estimators_],axis=0)
#按照变量的重要性排序后的索引 
indices = np.argsort(importances)[::-1]

### 绘图过程
import matplotlib.pyplot as plt
plt.figure()
plt.figure(figsize=(10,5))
plt.title("Feature importances")
plt.bar(range(X.shape[1]), importances[indices], color="c", yerr=std[indices], align="center")
plt.xticks(fontsize=14)
plt.xticks(range(X.shape[1]), df.columns.values[:-1][indices],rotation=40)
plt.xlim([-1, X.shape[1]])
plt.tight_layout()
plt.show()
     
      

    
  
  
  
  
# 3 <Stacking>
# 先训练初级学习器，然后用预测值来训练次级学习器
from sklearn import datasets
iris = datasets.load_iris()
X, y = iris.data[:, 1:3], iris.target

from sklearn import model_selection
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB 
from sklearn.ensemble import RandomForestClassifier
from mlxtend.classifier import StackingClassifier
import numpy as np

clf1 = KNeighborsClassifier(n_neighbors=1)
clf2 = RandomForestClassifier(random_state=1)
clf3 = GaussianNB()
lr = LogisticRegression()
sclf = StackingClassifier(classifiers=[clf1, clf2, clf3], 
                          meta_classifier=lr)
      
for clf, label in zip([clf1, clf2, clf3, sclf], 
                      ['KNN', 
                       'Random Forest', 
                       'Naive Bayes',
                       'StackingClassifier']):
 
    scores = model_selection.cross_val_score(clf, X, y,cv=3, scoring='accuracy')
    print("Accuracy: %0.2f [%s]" % (scores.mean(), label))

    
from sklearn import linear_model
# 将lgb和xgb和ctb的结果进行stacking
train_stack = np.vstack([oof_lgb,oof_xgb,oof_cb]).transpose()
test_stack = np.vstack([predictions_lgb, predictions_xgb,predictions_cb]).transpose()


folds_stack = RepeatedKFold(n_splits=5, n_repeats=2, random_state=2018)
oof_stack = np.zeros(train_stack.shape[0])
predictions = np.zeros(test_stack.shape[0])

for fold_, (trn_idx, val_idx) in enumerate(folds_stack.split(train_stack,y_train)):
    print("fold {}".format(fold_))
    trn_data, trn_y = train_stack[trn_idx], y_train[trn_idx]
    val_data, val_y = train_stack[val_idx], y_train[val_idx]
    
    clf_3 = linear_model.BayesianRidge()
    #clf_3 =linear_model.Ridge()
    clf_3.fit(trn_data, trn_y)
    
    oof_stack[val_idx] = clf_3.predict(val_data)
    predictions += clf_3.predict(test_stack) / 10
    
print("CV score: {:<8.8f}".format(mean_squared_error(oof_stack, y_train_)))    
    
    
    
    
