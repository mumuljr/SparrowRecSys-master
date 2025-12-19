package com.sparrowrecsys.online;

import com.sparrowrecsys.online.config.ModelConfig;
import com.sparrowrecsys.online.datamanager.DataManager;
import com.sparrowrecsys.online.service.*;
import org.eclipse.jetty.server.Server;
import org.eclipse.jetty.servlet.DefaultServlet;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.eclipse.jetty.util.resource.Resource;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.URL;

/***
 * Recsys Server, end point of online recommendation service
 */
public class RecSysServer {

    public static void main(String[] args) throws Exception {
        new RecSysServer().run();
    }

    //recsys server port number
    private static final int DEFAULT_PORT = 6010;

    public void run() throws Exception{

        int port = DEFAULT_PORT;
        try {
            port = Integer.parseInt(System.getenv("PORT"));
        } catch (NumberFormatException ignored) {}

        //set ip and port number
        InetSocketAddress inetAddress = new InetSocketAddress("0.0.0.0", port);
        Server server = new Server(inetAddress);

        //get index.html path
        URL webRootLocation = this.getClass().getResource("/webroot/index.html");
        if (webRootLocation == null)
        {
            throw new IllegalStateException("Unable to determine webroot URL location");
        }

        //set index.html as the root page
        URI webRootUri = URI.create(webRootLocation.toURI().toASCIIString().replaceFirst("/index.html$","/"));
        System.out.printf("Web Root URI: %s%n", webRootUri.getPath());

        // ========== 原有逻辑完全保留：加载标准模型的初始数据 ==========
        DataManager.getInstance().loadData(webRootUri.getPath() + "sampledata/movies.csv",
                webRootUri.getPath() + "sampledata/links.csv",webRootUri.getPath() + "sampledata/ratings.csv",
                webRootUri.getPath() + "modeldata/item2vecEmb.csv",
                webRootUri.getPath() + "modeldata/userEmb.csv",
                "i2vEmb", "uEmb");

        // ========== 新增（可选）：初始加载NCF得分文件（若默认启动NCF模型） ==========
        // 说明：若默认模型是STANDARD，此段可注释；若想默认启动NCF，取消注释并调整路径
        /*
        String modelDataPath = webRootUri.getPath() + "modeldata/";
        try {
            // 切换到NCF模型（可选）
            ModelConfig.setCurrentModelVersion(ModelConfig.ModelVersion.NCF);
            // 加载NCF的Emb + 得分文件
            DataManager.getInstance().reloadEmbeddings(
                modelDataPath,
                ModelConfig.ModelVersion.NCF.getItemEmbFile(),
                ModelConfig.ModelVersion.NCF.getUserEmbFile(),
                ModelConfig.ModelVersion.NCF.getNcfScoreFile()
            );
            System.out.println("Initial NCF model loaded successfully!");
        } catch (Exception e) {
            System.out.println("Failed to load initial NCF model (ignore if not needed): " + e.getMessage());
        }
        */
        // ========== 新增结束 ==========

        //create server context
        ServletContextHandler context = new ServletContextHandler();
        context.setContextPath("/");
        context.setBaseResource(Resource.newResource(webRootUri));
        context.setWelcomeFiles(new String[] { "index.html" });
        context.getMimeTypes().addMimeMapping("txt","text/plain;charset=utf-8");

        //bind services with different servlets（原有注册逻辑完全保留）
        context.addServlet(DefaultServlet.class,"/");
        context.addServlet(new ServletHolder(new MovieService()), "/getmovie");
        context.addServlet(new ServletHolder(new UserService()), "/getuser");
        context.addServlet(new ServletHolder(new SimilarMovieService()), "/getsimilarmovie");
        context.addServlet(new ServletHolder(new RecommendationService()), "/getrecommendation");
        context.addServlet(new ServletHolder(new RecForYouService()), "/getrecforyou");
        context.addServlet(new ServletHolder(new ModelService()), "/getmodel"); // 已注册ModelService，无需改动

        //set url handler
        server.setHandler(context);
        System.out.println("RecSys Server has started.");

        //start Server
        server.start();
        server.join();
    }
}