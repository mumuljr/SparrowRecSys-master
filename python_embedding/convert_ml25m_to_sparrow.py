import pandas as pd
import numpy as np
import os
from datetime import datetime
def convert_movielens_data():
    """
    转换MovieLens 25M数据为SparrowRecSys格式
    """
    print("=== MovieLens 25M 数据转换开始 ===")
    # 读取原始数据
    print("读取原始数据...")
    ratings_raw = pd.read_csv('ml-25m/ratings.csv')
    movies_raw = pd.read_csv('ml-25m/movies.csv')
    links_raw = pd.read_csv('ml-25m/links.csv')
    print(f"原始数据规模:")
    print(f"  评分: {len(ratings_raw):,} 条")
    print(f"  电影: {len(movies_raw):,} 部")
    print(f"  用户: {ratings_raw['userId'].nunique():,} 个")
    # 筛选高质量电影（至少100次评分）
    print("\\n筛选高质量电影...")
    movie_rating_counts = ratings_raw['movieId'].value_counts()
    min_ratings = 100
    qualified_movies = movie_rating_counts[movie_rating_counts >= min_ratings].index
    print(f"筛选条件: 至少{min_ratings}次评分")
    print(f"符合条件的电影: {len(qualified_movies)} 部")
    # 过滤数据
    movies_filtered = movies_raw[movies_raw['movieId'].isin(qualified_movies)]
    ratings_filtered = ratings_raw[ratings_raw['movieId'].isin(qualified_movies)]
    links_filtered = links_raw[links_raw['movieId'].isin(qualified_movies)]
    # 重新映射movieId (从1开始连续)
    print("\\n重新映射电影ID...")
    movie_id_mapping = {old_id: new_id for new_id, old_id in 
                       enumerate(movies_filtered['movieId'].unique(), 1)}
    # 应用映射
    movies_filtered['movieId'] = movies_filtered['movieId'].map(movie_id_mapping)
    ratings_filtered['movieId'] = ratings_filtered['movieId'].map(movie_id_mapping)
    links_filtered['movieId'] = links_filtered['movieId'].map(movie_id_mapping)
    # 重新映射userId (从1开始连续)
    print("重新映射用户ID...")
    user_id_mapping = {old_id: new_id for new_id, old_id in 
                      enumerate(ratings_filtered['userId'].unique(), 1)}
    ratings_filtered['userId'] = ratings_filtered['userId'].map(user_id_mapping)
    # 排序数据
    movies_filtered = movies_filtered.sort_values('movieId')
    ratings_filtered = ratings_filtered.sort_values(['userId', 'movieId'])
    links_filtered = links_filtered.sort_values('movieId')
    # 输出统计
    print(f"\\n=== 转换后数据统计 ===")
    print(f"电影数量: {len(movies_filtered):,}")
    print(f"评分记录: {len(ratings_filtered):,}")
    print(f"用户数量: {ratings_filtered['userId'].nunique():,}")
    print(f"平均每部电影评分: {len(ratings_filtered) / len(movies_filtered):.1f} 次")
    return movies_filtered, ratings_filtered, links_filtered
def save_sparrow_format(movies_df, ratings_df, links_df):
    """
    保存为SparrowRecSys格式
    """
    print("\\n=== 保存数据文件 ===")
    # 创建输出目录
    output_dir = 'sparrow_data'
    os.makedirs(output_dir, exist_ok=True)
    # 保存movies.csv (SparrowRecSys格式)
    movies_output = movies_df[['movieId', 'title', 'genres']].copy()
    movies_output.to_csv(f'{output_dir}/movies.csv', index=False)
    print(f"已保存: {output_dir}/movies.csv ({len(movies_output)} 行)")
    # 保存ratings.csv (SparrowRecSys格式) 
    ratings_output = ratings_df[['userId', 'movieId', 'rating', 'timestamp']].copy()
    ratings_output.to_csv(f'{output_dir}/ratings.csv', index=False)
    print(f"已保存: {output_dir}/ratings.csv ({len(ratings_output)} 行)")
    # 保存links.csv (包含TMDB/IMDB链接)
    links_output = links_df[['movieId', 'imdbId', 'tmdbId']].copy()
    links_output.to_csv(f'{output_dir}/links.csv', index=False)
    print(f"已保存: {output_dir}/links.csv ({len(links_output)} 行)")
    # 生成统计报告
    with open(f'{output_dir}/conversion_report.txt', 'w') as f:
        f.write(f"MovieLens 25M 到 SparrowRecSys 数据转换报告\\n")
        f.write(f"转换时间: {datetime.now()}\\n\\n")
        f.write(f"原始数据规模:\\n")
        f.write(f"  电影: 62,424 部\\n")
        f.write(f"  评分: 25,000,095 条\\n\\n")
        f.write(f"转换后数据规模:\\n")
        f.write(f"  电影: {len(movies_output):,} 部\\n")
        f.write(f"  评分: {len(ratings_output):,} 条\\n")
        f.write(f"  用户: {ratings_output['userId'].nunique():,} 个\\n\\n")
        f.write(f"筛选条件: 每部电影至少100次评分\\n")
        f.write(f"数据质量: 高质量电影数据集\\n")
def main():
    """主函数"""
    try:
        # 检查输入文件
        required_files = ['ml-25m/movies.csv', 'ml-25m/ratings.csv', 'ml-25m/links.csv']
        for file in required_files:
            if not os.path.exists(file):
                print(f"错误: 找不到文件 {file}")
                print("请先下载并解压 MovieLens 25M 数据集")
                return
        # 执行转换
        movies_df, ratings_df, links_df = convert_movielens_data()
        save_sparrow_format(movies_df, ratings_df, links_df)
        print("\\n=== 数据转换完成 ===")
        print("下一步: 将sparrow_data/目录下的文件复制到SparrowRecSys项目")
    except Exception as e:
        print(f"转换过程中出错: {e}")
        import traceback
        traceback.print_exc()
if __name__ == "__main__":
    main()