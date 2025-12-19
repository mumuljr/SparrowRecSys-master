import pandas as pd
import numpy as np
import logging
import sys
import os
import tensorflow as tf
from tensorflow.keras import layers, Model, optimizers, losses, metrics
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.utils import shuffle

# 设置日志
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

# 设置随机种子确保可复现
np.random.seed(42)
tf.random.set_seed(42)

# 检查GPU是否可用
physical_devices = tf.config.list_physical_devices('GPU')
if physical_devices:
    try:
        tf.config.experimental.set_memory_growth(physical_devices[0], True)
        print(f"✅ GPU可用: {physical_devices}")
    except Exception as e:
        print(f"⚠️ GPU设置警告: {e}")
else:
    print("ℹ️ 使用CPU训练")


class NCFModel:
    """NCF模型实现类（Neural Collaborative Filtering）"""

    def __init__(self, num_users, num_items, embedding_dim=128, dropout_rate=0.2):
        """
        初始化NCF模型
        :param num_users: 用户数量
        :param num_items: 物品数量
        :param embedding_dim: 嵌入维度
        :param dropout_rate: Dropout率
        """
        self.num_users = num_users
        self.num_items = num_items
        self.embedding_dim = embedding_dim
        self.dropout_rate = dropout_rate
        self.model = self._build_model()

    def _build_mlp_part(self, user_input, item_input):
        """构建MLP部分网络"""
        # MLP嵌入层
        user_mlp_embedding = layers.Embedding(
            input_dim=self.num_users,
            output_dim=self.embedding_dim,
            embeddings_initializer='he_normal',
            embeddings_regularizer=tf.keras.regularizers.l2(1e-6),
            name='user_mlp_embedding'
        )(user_input)
        item_mlp_embedding = layers.Embedding(
            input_dim=self.num_items,
            output_dim=self.embedding_dim,
            embeddings_initializer='he_normal',
            embeddings_regularizer=tf.keras.regularizers.l2(1e-6),
            name='item_mlp_embedding'
        )(item_input)

        # 展平
        user_flat = layers.Flatten()(user_mlp_embedding)
        item_flat = layers.Flatten()(item_mlp_embedding)

        # 拼接
        concat = layers.Concatenate()([user_flat, item_flat])

        # MLP层
        mlp = layers.Dense(512, activation='relu', kernel_initializer='he_normal')(concat)
        mlp = layers.Dropout(self.dropout_rate)(mlp)
        mlp = layers.BatchNormalization()(mlp)

        mlp = layers.Dense(256, activation='relu', kernel_initializer='he_normal')(mlp)
        mlp = layers.Dropout(self.dropout_rate)(mlp)
        mlp = layers.BatchNormalization()(mlp)

        mlp = layers.Dense(128, activation='relu', kernel_initializer='he_normal')(mlp)
        mlp = layers.Dropout(self.dropout_rate)(mlp)
        mlp = layers.BatchNormalization()(mlp)

        return mlp

    def _build_gmf_part(self, user_input, item_input):
        """构建GMF（Generalized Matrix Factorization）部分网络"""
        # GMF嵌入层
        user_gmf_embedding = layers.Embedding(
            input_dim=self.num_users,
            output_dim=self.embedding_dim,
            embeddings_initializer='he_normal',
            embeddings_regularizer=tf.keras.regularizers.l2(1e-6),
            name='user_gmf_embedding'
        )(user_input)
        item_gmf_embedding = layers.Embedding(
            input_dim=self.num_items,
            output_dim=self.embedding_dim,
            embeddings_initializer='he_normal',
            embeddings_regularizer=tf.keras.regularizers.l2(1e-6),
            name='item_gmf_embedding'
        )(item_input)

        # 元素级乘法
        gmf = layers.Multiply()([user_gmf_embedding, item_gmf_embedding])
        gmf = layers.Flatten()(gmf)

        return gmf

    def _build_model(self):
        """构建完整的NCF模型（GMF + MLP）"""
        # 输入层
        user_input = layers.Input(shape=(1,), name='user_input')
        item_input = layers.Input(shape=(1,), name='item_input')

        # 构建GMF和MLP部分
        gmf_output = self._build_gmf_part(user_input, item_input)
        mlp_output = self._build_mlp_part(user_input, item_input)

        # 拼接GMF和MLP输出
        concat = layers.Concatenate()([gmf_output, mlp_output])

        # 输出层
        output = layers.Dense(1, activation='sigmoid', kernel_initializer='glorot_normal')(concat)

        # 构建模型
        model = Model(inputs=[user_input, item_input], outputs=output)

        # 编译模型
        model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss=losses.BinaryCrossentropy(),
            metrics=[
                metrics.AUC(name='auc'),
                metrics.BinaryAccuracy(name='accuracy')
            ]
        )

        return model

    def train(self, train_data, val_data, epochs=20, batch_size=2048):
        """
        训练模型
        :param train_data: 训练数据 (users, items, labels)
        :param val_data: 验证数据 (users, items, labels)
        :param epochs: 训练轮数
        :param batch_size: 批次大小
        """
        # 准备训练数据
        train_users, train_items, train_labels = train_data
        val_users, val_items, val_labels = val_data

        # 回调函数
        callbacks = [
            EarlyStopping(
                monitor='val_auc',
                patience=3,
                mode='max',
                restore_best_weights=True
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=2,
                min_lr=1e-6
            ),
            ModelCheckpoint(
                'ncf_model_best.h5',
                monitor='val_auc',
                save_best_only=True,
                mode='max'
            )
        ]

        # 训练模型
        history = self.model.fit(
            x=[train_users, train_items],
            y=train_labels,
            validation_data=([val_users, val_items], val_labels),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            shuffle=True,
            verbose=1
        )

        return history

    def save_model(self, path='../src/main/resources/webroot/modeldata/ncf_model'):
        """保存模型"""
        # 创建目录
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # 保存完整模型
        self.model.save(f'{path}.h5')
        print(f"✅ 模型已保存至: {path}.h5")

        # 保存模型配置
        config = {
            'num_users': self.num_users,
            'num_items': self.num_items,
            'embedding_dim': self.embedding_dim,
            'dropout_rate': self.dropout_rate
        }
        np.save(f'{path}_config.npy', config)
        print(f"✅ 模型配置已保存至: {path}_config.npy")

    def load_embeddings(self):
        """提取并返回用户和物品嵌入向量"""
        # 获取嵌入层权重
        user_gmf_emb = self.model.get_layer('user_gmf_embedding').get_weights()[0]
        item_gmf_emb = self.model.get_layer('item_gmf_embedding').get_weights()[0]
        user_mlp_emb = self.model.get_layer('user_mlp_embedding').get_weights()[0]
        item_mlp_emb = self.model.get_layer('item_mlp_embedding').get_weights()[0]

        # 融合GMF和MLP嵌入
        user_embeddings = np.concatenate([user_gmf_emb, user_mlp_emb], axis=1)
        item_embeddings = np.concatenate([item_gmf_emb, item_mlp_emb], axis=1)

        return user_embeddings, item_embeddings


def prepare_ncf_data():
    """准备NCF训练数据（处理ml-25m数据集）"""
    print("📖 读取评分数据...")
    ratings = pd.read_csv('ml-25m/ratings.csv')
    print(f"总评分数: {len(ratings):,}")
    print(f"用户数: {ratings['userId'].nunique():,}")
    print(f"电影数: {ratings['movieId'].nunique():,}")

    # 数据预处理 - 筛选活跃用户和热门电影
    print("🔄 数据预处理...")

    # 用户评分统计
    user_counts = ratings['userId'].value_counts()
    movie_counts = ratings['movieId'].value_counts()

    # 筛选标准: 用户至少20个评分，电影至少50个评分
    active_users = user_counts[user_counts >= 20].index
    popular_movies = movie_counts[movie_counts >= 50].index

    # 筛选数据
    filtered_ratings = ratings[
        (ratings['userId'].isin(active_users)) &
        (ratings['movieId'].isin(popular_movies))
        ].copy()

    print(f"筛选后评分数: {len(filtered_ratings):,}")
    print(f"筛选后用户数: {filtered_ratings['userId'].nunique():,}")
    print(f"筛选后电影数: {filtered_ratings['movieId'].nunique():,}")

    # 标签编码（将用户ID和电影ID转换为连续索引）
    print("🔢 标签编码用户和物品ID...")
    user_encoder = LabelEncoder()
    item_encoder = LabelEncoder()

    filtered_ratings['user_idx'] = user_encoder.fit_transform(filtered_ratings['userId'])
    filtered_ratings['item_idx'] = item_encoder.fit_transform(filtered_ratings['movieId'])

    # 将评分转换为隐式反馈（NCF通常用于推荐，使用二分类）
    # 评分>=3视为正样本，否则为负样本
    filtered_ratings['label'] = (filtered_ratings['rating'] >= 3).astype(int)

    # 统计正负样本数量
    positive_samples = filtered_ratings[filtered_ratings['label'] == 1]
    negative_samples = filtered_ratings[filtered_ratings['label'] == 0]

    pos_count = len(positive_samples)
    neg_count = len(negative_samples)

    print(f"\n📊 样本分布:")
    print(f"正样本数量: {pos_count:,}")
    print(f"负样本数量: {neg_count:,}")
    print(f"正负样本比例: 1:{neg_count / pos_count:.2f}")

    # 改进的负采样逻辑 - 处理负样本不足的情况
    print("🎲 负采样处理...")
    if neg_count >= pos_count:
        # 负样本充足，采样与正样本数量相同的负样本
        negative_samples = negative_samples.sample(
            n=pos_count,
            random_state=42,
            replace=False
        )
        print(f"✅ 负样本充足，采样 {pos_count:,} 个负样本")
    else:
        # 负样本不足，有两种处理方式：
        # 1. 使用所有负样本，同时对正样本下采样
        print(f"⚠️ 负样本不足（{neg_count} < {pos_count}），调整样本数量")
        # 对正样本下采样到负样本数量
        positive_samples = positive_samples.sample(
            n=neg_count,
            random_state=42,
            replace=False
        )
        print(f"✅ 正样本下采样至 {neg_count:,} 个")

    # 合并正负样本
    train_data = pd.concat([positive_samples, negative_samples])
    train_data = shuffle(train_data, random_state=42)

    # 划分训练集和验证集
    print("📊 划分训练集和验证集...")
    train_df, val_df = train_test_split(
        train_data,
        test_size=0.1,
        random_state=42,
        stratify=train_data['label']  # 分层采样，保持正负样本比例
    )

    print(
        f"训练集大小: {len(train_df):,} (正样本: {train_df['label'].sum()}, 负样本: {len(train_df) - train_df['label'].sum()})")
    print(
        f"验证集大小: {len(val_df):,} (正样本: {val_df['label'].sum()}, 负样本: {len(val_df) - val_df['label'].sum()})")

    # 准备训练数据
    train_users = train_df['user_idx'].values
    train_items = train_df['item_idx'].values
    train_labels = train_df['label'].values

    # 准备验证数据
    val_users = val_df['user_idx'].values
    val_items = val_df['item_idx'].values
    val_labels = val_df['label'].values

    # 获取编码后的用户和物品数量
    num_users = len(user_encoder.classes_)
    num_items = len(item_encoder.classes_)

    # 保存编码器映射关系
    print("💾 保存用户和物品ID映射...")
    # 创建目录（如果不存在）
    os.makedirs('../src/main/resources/webroot/modeldata/', exist_ok=True)

    user_mapping = dict(zip(user_encoder.classes_, range(num_users)))
    item_mapping = dict(zip(item_encoder.classes_, range(num_items)))

    # 保存映射关系
    np.save('../src/main/resources/webroot/modeldata/user_mapping.npy', user_mapping)
    np.save('../src/main/resources/webroot/modeldata/item_mapping.npy', item_mapping)

    return (train_users, train_items, train_labels), \
        (val_users, val_items, val_labels), \
        num_users, num_items, user_encoder, item_encoder


def save_ncf_embeddings(ncf_model, user_encoder, item_encoder):
    """保存NCF生成的用户和物品嵌入向量"""
    print("💾 提取并保存NCF嵌入向量...")

    # 获取嵌入向量
    user_embeddings, item_embeddings = ncf_model.load_embeddings()

    # 保存用户embeddings
    user_emb_list = []
    for idx, original_user_id in enumerate(user_encoder.classes_):
        embedding = ' '.join(map(str, user_embeddings[idx]))
        user_emb_list.append(f"{original_user_id}:{embedding}")

    # 创建目录（如果不存在）
    os.makedirs('../src/main/resources/webroot/modeldata/', exist_ok=True)

    with open('../src/main/resources/webroot/modeldata/ncf_userEmb_large.csv', 'w', encoding='utf-8') as f:
        f.write('\n'.join(user_emb_list))

    # 保存物品embeddings
    item_emb_list = []
    for idx, original_item_id in enumerate(item_encoder.classes_):
        embedding = ' '.join(map(str, item_embeddings[idx]))
        item_emb_list.append(f"{original_item_id}:{embedding}")

    with open('../src/main/resources/webroot/modeldata/ncf_itemEmb_large.csv', 'w', encoding='utf-8') as f:
        f.write('\n'.join(item_emb_list))

    print(f"✅ 保存了 {len(user_emb_list):,} 个用户embeddings")
    print(f"✅ 保存了 {len(item_emb_list):,} 个物品embeddings")


def main():
    print("=" * 60)
    print("🎬 SparrowRecSys NCF模型训练")
    print("=" * 60)

    try:
        # 1. 准备数据
        train_data, val_data, num_users, num_items, user_encoder, item_encoder = prepare_ncf_data()

        # 2. 创建NCF模型
        print("🤖 创建NCF模型...")
        ncf_model = NCFModel(
            num_users=num_users,
            num_items=num_items,
            embedding_dim=128,
            dropout_rate=0.2
        )

        # 打印模型结构
        print("\n📋 模型结构:")
        ncf_model.model.summary()

        # 3. 训练模型
        print("\n🚀 开始训练NCF模型...")
        history = ncf_model.train(
            train_data=train_data,
            val_data=val_data,
            epochs=20,
            batch_size=2048
        )

        # 4. 保存模型
        print("\n💾 保存NCF模型...")
        ncf_model.save_model()

        # 5. 提取并保存嵌入向量
        save_ncf_embeddings(ncf_model, user_encoder, item_encoder)

        # 6. 打印训练结果
        print("\n📊 训练结果:")
        print(f"最佳验证AUC: {max(history.history['val_auc']):.4f}")
        print(f"最佳验证准确率: {max(history.history['val_accuracy']):.4f}")

        print("\n🎉 NCF模型训练完成！")
        print("生成的文件:")
        print("  - ncf_model.h5: NCF完整模型")
        print("  - ncf_model_config.npy: 模型配置参数")
        print("  - ncf_userEmb_large.csv: NCF用户embeddings")
        print("  - ncf_itemEmb_large.csv: NCF物品embeddings")
        print("  - user_mapping.npy: 用户ID映射关系")
        print("  - item_mapping.npy: 物品ID映射关系")

    except Exception as e:
        print(f"❌ 训练过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()