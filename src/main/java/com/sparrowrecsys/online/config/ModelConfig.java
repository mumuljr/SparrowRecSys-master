package com.sparrowrecsys.online.config;

/**
 * Model configuration class
 */
public class ModelConfig {
    // Available model versions
    public enum ModelVersion {
        // 原有枚举保留，仅为NCF新增得分文件参数（其他模型传空字符串）
        STANDARD("Standard Version", "item2vecEmb.csv", "userEmb.csv", ""),
        LARGE("Large Dataset Version", "item2vecEmb_large.csv", "userEmb_large.csv", ""),
        NCF("NCF Version", "ncf_itemEmb_large.csv", "ncf_userEmb_large.csv", "ncf_predict_scores.csv");

        // 原有字段完全保留
        private final String displayName;
        private final String itemEmbFile;
        private final String userEmbFile;
        // 新增：NCF得分文件路径（仅NCF模型使用）
        private final String ncfScoreFile;

        // 扩展构造方法（兼容原有参数，新增ncfScoreFile）
        ModelVersion(String displayName, String itemEmbFile, String userEmbFile, String ncfScoreFile) {
            this.displayName = displayName;
            this.itemEmbFile = itemEmbFile;
            this.userEmbFile = userEmbFile;
            // 仅新增这一行赋值，无其他改动
            this.ncfScoreFile = ncfScoreFile;
        }

        // 原有getter完全保留（保证实验手册逻辑不被破坏）
        public String getDisplayName() { return displayName; }
        public String getItemEmbFile() { return itemEmbFile; }
        public String getUserEmbFile() { return userEmbFile; }
        // 新增：获取NCF得分文件路径的方法（仅新增，不修改原有方法）
        public String getNcfScoreFile() { return ncfScoreFile; }
    }

    // 原有静态变量+方法完全保留
    private static ModelVersion currentModelVersion = ModelVersion.STANDARD;

    public static ModelVersion getCurrentModelVersion() {
        return currentModelVersion;
    }

    public static void setCurrentModelVersion(ModelVersion version) {
        currentModelVersion = version;
    }

    public static ModelVersion[] getAllModelVersions() {
        return ModelVersion.values();
    }
}