import pandas as pd
import numpy as np
from gensim.models import Word2Vec
from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix
import logging
import os
from tqdm import tqdm

# 设置日志
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

OUTPUT_DIR = "../src/main/resources/webroot/modeldata"
DATASET_PATH = "ml-25m/ratings.csv"

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
#                  Item2Vec 训练部分（保留原样）
# ============================================================

def train_item2vec_large_dataset():
    print("🚀 开始训练大数据集 Item2Vec 模型...")

    # 读取数据
    print("📖 读取评分数据...")
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"❌ 未找到数据集文件: {DATASET_PATH}")

    ratings = pd.read_csv(DATASET_PATH)
    print(f"总评分数: {len(ratings):,}")

    # 筛选活跃用户与热门电影
    print("🔄 数据预处理...")
    user_counts = ratings["userId"].value_counts()
    movie_counts = ratings["movieId"].value_counts()

    active_users = user_counts[user_counts >= 20].index
    popular_movies = movie_counts[movie_counts >= 50].index

    filtered_ratings = ratings[
        (ratings["userId"].isin(active_users)) &
        (ratings["movieId"].isin(popular_movies))
        ].copy()

    print(f"筛选后评分数: {len(filtered_ratings):,}")

    # 创建序列
    print("📝 创建用户观影序列...")
    filtered_ratings = filtered_ratings.sort_values(["userId", "timestamp"])

    user_sequences = []
    for user_id in tqdm(filtered_ratings["userId"].unique()):
        seq = filtered_ratings[filtered_ratings["userId"] == user_id]["movieId"].astype(str).tolist()
        if len(seq) >= 5:
            user_sequences.append(seq)

    print(f"创建了 {len(user_sequences):,} 个电影序列")

    # 训练 Word2Vec
    print("🤖 开始训练 Word2Vec ...")
    model = Word2Vec(
        sentences=user_sequences,
        vector_size=128,
        window=5,
        min_count=5,
        workers=4,
        epochs=10,
        sg=1
    )

    # 保存电影 embedding
    item2vec_path = os.path.join(OUTPUT_DIR, "item2vecEmb_large.csv")
    print(f"💾 保存电影 embedding 到: {item2vec_path}")

    with open(item2vec_path, "w") as f:
        for movie_id in model.wv.index_to_key:
            emb = " ".join(map(str, model.wv[movie_id]))
            f.write(f"{movie_id}:{emb}\n")

    return model, filtered_ratings


# ============================================================
#       ⭐  改进：使用稀疏矩阵 + SVD（不会爆内存） ⭐
# ============================================================

def train_user_embeddings_large_dataset(filtered_ratings):
    print("🚀 使用稀疏矩阵训练用户 Embedding（Sparse SVD）...")

    # 获取唯一的用户与电影
    users = filtered_ratings["userId"].unique()
    movies = filtered_ratings["movieId"].unique()

    print(f"用户数: {len(users)}, 电影数: {len(movies)}")

    user_to_index = {u: i for i, u in enumerate(users)}
    movie_to_index = {m: i for i, m in enumerate(movies)}

    rows, cols, data = [], [], []

    print("📦 构建 CSR 稀疏矩阵（不会爆内存）...")
    for row in tqdm(filtered_ratings.itertuples(), total=len(filtered_ratings)):
        rows.append(user_to_index[row.userId])
        cols.append(movie_to_index[row.movieId])
        data.append(row.rating)

    # 构建稀疏用户-电影矩阵
    matrix = csr_matrix((data, (rows, cols)),
                        shape=(len(users), len(movies)))

    print("✔ 稀疏矩阵构建完成！大小：", matrix.shape)

    # SVD 降维
    print("🔍 开始 SVD 降维 (128 维)...")
    svd = TruncatedSVD(n_components=128, random_state=42)
    user_embeddings = svd.fit_transform(matrix)

    # 保存结果
    output_path = os.path.join(OUTPUT_DIR, "userEmb_large.csv")
    print(f"💾 保存用户 embedding 到: {output_path}")

    with open(output_path, "w") as f:
        for i, user_id in enumerate(users):
            emb = " ".join(map(str, user_embeddings[i]))
            f.write(f"{user_id}:{emb}\n")

    print(f"🎉 保存了 {len(users)} 个用户 embedding")


# ============================================================
#                           主程序
# ============================================================

def main():
    print("=" * 60)
    print("🎬 SparrowRecSys 大规模模型训练启动")
    print("=" * 60)

    model, filtered = train_item2vec_large_dataset()
    train_user_embeddings_large_dataset(filtered)

    print("\n🎉 训练完成！")


if __name__ == "__main__":
    main()
