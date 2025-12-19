# 保存为 generate_ncf_scores.py
import pandas as pd
import numpy as np
import os
import tensorflow as tf
from sklearn.preprocessing import LabelEncoder

# ---------------------- 核心配置（仅需确认这1个路径） ----------------------
# 你的项目根目录（python_embedding的上级目录）
PROJECT_ROOT = "D:/xksj/final project/code/SparrowRecSys-master/SparrowRecSys-master"
# -----------------------------------------------------------------------

# 自动推导所有文件路径（无需手动改）
MODEL_PATH = os.path.join(PROJECT_ROOT, "src/main/resources/webroot/modeldata/ncf_model.h5")
USER_MAPPING_PATH = os.path.join(PROJECT_ROOT, "src/main/resources/webroot/modeldata/user_mapping.npy")
ITEM_MAPPING_PATH = os.path.join(PROJECT_ROOT, "src/main/resources/webroot/modeldata/item_mapping.npy")
RATINGS_PATH = os.path.join(PROJECT_ROOT, "python_embedding/ml-25m/ratings.csv")  # 假设ratings在python_embedding下
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "src/main/resources/webroot/modeldata/ncf_predict_scores.csv")

# ===================== 路径检查（关键：避免文件找不到） =====================
def check_file_exists(file_path, file_desc):
    if not os.path.exists(file_path):
        print(f"❌ 找不到{file_desc}，路径：{file_path}")
        print("请确认文件是否存在，或修改PROJECT_ROOT路径！")
        exit(1)
    print(f"✅ 找到{file_desc}：{file_path}")

# 检查必要文件
check_file_exists(MODEL_PATH, "NCF模型文件(ncf_model.h5)")
check_file_exists(USER_MAPPING_PATH, "用户映射文件(user_mapping.npy)")
check_file_exists(ITEM_MAPPING_PATH, "物品映射文件(item_mapping.npy)")
check_file_exists(RATINGS_PATH, "评分数据文件(ratings.csv)")

# ===================== 加载模型和数据 =====================
print("\n加载NCF模型和映射关系...")
model = tf.keras.models.load_model(MODEL_PATH)
user_mapping = np.load(USER_MAPPING_PATH, allow_pickle=True).item()
item_mapping = np.load(ITEM_MAPPING_PATH, allow_pickle=True).item()

# 构建编码器
user_encoder = LabelEncoder()
user_encoder.classes_ = np.array(list(user_mapping.keys()))
item_encoder = LabelEncoder()
item_encoder.classes_ = np.array(list(item_mapping.keys()))

# 加载评分数据（仅用于过滤已交互物品）
print("\n加载评分数据...")
ratings = pd.read_csv(RATINGS_PATH)
user_counts = ratings['userId'].value_counts()
movie_counts = ratings['movieId'].value_counts()
active_users = user_counts[user_counts >= 20].index
popular_movies = movie_counts[movie_counts >= 50].index
filtered_ratings = ratings[
    (ratings['userId'].isin(active_users)) &
    (ratings['movieId'].isin(popular_movies))
].copy()
user_interacted_items = filtered_ratings.groupby('userId')['movieId'].apply(set).to_dict()

# ===================== 生成预测得分（快速采样，避免耗时） =====================
print("\n生成NCF预测得分（采样10%用户，约1分钟完成）...")
predict_scores = []
# 采样10%用户（测试用，全量可改0.5或1.0）
sampled_users = np.random.choice(user_encoder.classes_, size=int(len(user_encoder.classes_)*0.1), replace=False)

for i, user_id in enumerate(sampled_users):
    if i % 100 == 0:
        print(f"进度：{i}/{len(sampled_users)} 用户")
    
    # 转换用户ID为模型输入索引
    try:
        user_idx = user_encoder.transform([user_id])[0]
    except:
        continue
    
    # 候选物品：排除已交互的，取前500个（减少计算量）
    interacted = user_interacted_items.get(user_id, set())
    candidate_items = [item_id for item_id in item_encoder.classes_ if item_id not in interacted][:500]
    if not candidate_items:
        continue
    
    # 批量预测得分
    item_indices = item_encoder.transform(candidate_items)
    user_indices = np.full_like(item_indices, user_idx)
    scores = model.predict([user_indices, item_indices], batch_size=5000, verbose=0)
    
    # 保存得分（格式：userID_itemID:score）
    for item_id, score in zip(candidate_items, scores):
        predict_scores.append(f"{user_id}_{item_id}:{float(score[0])}")

# ===================== 保存文件 =====================
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(predict_scores))

print(f"\n🎉 生成完成！")
print(f"📄 文件路径：{OUTPUT_PATH}")
print(f"📊 共生成 {len(predict_scores)} 条用户-物品预测得分")