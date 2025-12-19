@echo off
echo ==============================
echo 🚀 SparrowRecSys 大数据模型训练自动化脚本
echo ==============================

REM 1. 创建虚拟环境
echo 📦 创建虚拟环境 venv ...
python -m venv venv

REM 2. 激活虚拟环境
echo 🔥 激活虚拟环境 ...
call venv\Scripts\activate

REM 3. 安装依赖
echo 📥 安装依赖 ...
pip install --upgrade pip
pip install pandas numpy gensim scikit-learn tqdm

REM 4. 运行训练脚本
echo 🎬 开始训练模型 ...
python train_large.py

echo 🎉 训练完成！
pause
