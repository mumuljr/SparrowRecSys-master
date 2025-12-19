package com.sparrowrecsys.online.service;

import com.sparrowrecsys.online.config.ModelConfig;
import com.sparrowrecsys.online.datamanager.DataManager;
import org.json.JSONArray;
import org.json.JSONObject;

import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.PrintWriter;

/**
 * Model management service
 */
public class ModelService extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) throws IOException {
        response.setContentType("application/json");
        response.setCharacterEncoding("UTF-8");
        response.setHeader("Access-Control-Allow-Origin", "*");

        PrintWriter out = response.getWriter();
        JSONObject responseJson = new JSONObject();

        try {
            String action = request.getParameter("action");

            if ("list".equals(action)) {
                // Get all available model versions
                JSONArray modelsArray = new JSONArray();
                for (ModelConfig.ModelVersion version : ModelConfig.getAllModelVersions()) {
                    JSONObject modelJson = new JSONObject();
                    modelJson.put("version", version.name());
                    modelJson.put("displayName", version.getDisplayName());
                    modelJson.put("itemEmbFile", version.getItemEmbFile());
                    modelJson.put("userEmbFile", version.getUserEmbFile());
                    // ========== 新增：返回NCF得分文件路径（仅新增，不影响原有字段） ==========
                    modelJson.put("ncfScoreFile", version.getNcfScoreFile());
                    // ========== 新增结束 ==========
                    modelJson.put("isCurrent", version == ModelConfig.getCurrentModelVersion());
                    modelsArray.put(modelJson);
                }

                responseJson.put("success", true);
                responseJson.put("models", modelsArray);
                responseJson.put("currentModel", ModelConfig.getCurrentModelVersion().name());

            } else if ("switch".equals(action)) {
                // Switch model version
                String versionName = request.getParameter("version");
                if (versionName != null) {
                    try {
                        ModelConfig.ModelVersion newVersion = ModelConfig.ModelVersion.valueOf(versionName);

                        // Get model file path
                        String webRoot = getServletContext().getRealPath("/");
                        if (webRoot == null) {
                            webRoot = this.getClass().getResource("/webroot/").getPath();
                        }
                        if (!webRoot.endsWith("/")) {
                            webRoot += "/";
                        }
                        String modelDataPath = webRoot + "modeldata/";

                        // ========== 新增：区分NCF模型，加载得分文件（仅新增分支，不改动原有逻辑） ==========
                        if (ModelConfig.ModelVersion.NCF.equals(newVersion)) {
                            // NCF模型：调用扩展的重载方法，加载Emb + 得分文件
                            DataManager.getInstance().reloadEmbeddings(
                                    modelDataPath,
                                    newVersion.getItemEmbFile(),
                                    newVersion.getUserEmbFile(),
                                    newVersion.getNcfScoreFile()
                            );
                        } else {
                            // 标准/大数据集模型：调用原有方法，仅加载Emb（完全保留实验手册逻辑）
                            DataManager.getInstance().reloadEmbeddings(
                                    modelDataPath,
                                    newVersion.getItemEmbFile(),
                                    newVersion.getUserEmbFile()
                            );
                        }
                        // ========== 新增结束 ==========

                        // Update current model version
                        ModelConfig.setCurrentModelVersion(newVersion);

                        responseJson.put("success", true);
                        responseJson.put("message", "Successfully switched to " + newVersion.getDisplayName());
                        responseJson.put("currentModel", newVersion.name());

                    } catch (Exception e) {
                        responseJson.put("success", false);
                        responseJson.put("message", "Failed to switch model: " + e.getMessage());
                    }
                } else {
                    responseJson.put("success", false);
                    responseJson.put("message", "Model version not specified");
                }

            } else {
                responseJson.put("success", false);
                responseJson.put("message", "Invalid action: " + action);
            }

        } catch (Exception e) {
            responseJson.put("success", false);
            responseJson.put("message", "Server error: " + e.getMessage());
            e.printStackTrace();
        }

        out.println(responseJson.toString());
        out.close();
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) throws IOException {
        doGet(request, response);
    }
}