import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
def analyze_dataset():
    print("=== MovieLens 25M 数据集分析 ===")
    # 读取数据
    ratings = pd.read_csv('ml-25m/ratings.csv')
    movies = pd.read_csv('ml-25m/movies.csv')
    links = pd.read_csv('ml-25m/links.csv')
    print(f"评分数据: {len(ratings):,} 条记录")
    print(f"电影数据: {len(movies):,} 部电影")
    print(f"用户数量: {ratings['userId'].nunique():,} 个用户")
    # 评分分布
    print("\\n=== 评分统计 ===")
    print(ratings['rating'].describe())
    # 电影评分次数分布
    movie_counts = ratings['movieId'].value_counts()
    print(f"\\n平均每部电影评分次数: {movie_counts.mean():.1f}")
    print(f"评分最多的电影: {movie_counts.iloc[0]} 次")
    print(f"评分最少的电影: {movie_counts.iloc[-1]} 次")
    # 筛选条件推荐（用于减少数据规模）
    min_ratings = 100  # 最少评分次数
    qualified_movies = movie_counts[movie_counts >= min_ratings]
    print(f"\\n至少{min_ratings}次评分的电影: {len(qualified_movies)} 部")
    return qualified_movies.index.tolist()
if __name__ == "__main__":
    qualified_movies = analyze_dataset()
    print(f"\\n推荐使用 {len(qualified_movies)} 部高质量电影进行训练")