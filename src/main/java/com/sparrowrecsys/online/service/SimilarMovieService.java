package com.sparrowrecsys.online.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sparrowrecsys.online.datamanager.DataManager;
import com.sparrowrecsys.online.datamanager.Movie;
import com.sparrowrecsys.online.recprocess.SimilarMovieProcess;

import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;

/**
 * SimilarMovieService, recommend similar movies given by a specific movie
 */
public class SimilarMovieService extends HttpServlet {

    protected void doGet(HttpServletRequest request,
                         HttpServletResponse response) throws IOException {

        response.setContentType("application/json");
        response.setStatus(HttpServletResponse.SC_OK);
        response.setCharacterEncoding("UTF-8");
        response.setHeader("Access-Control-Allow-Origin", "*");

        try {
            int movieId = Integer.parseInt(request.getParameter("movieId"));
            int size = Integer.parseInt(request.getParameter("size"));
            String model = request.getParameter("model");

            // 1️⃣ 主流程：基于模型的相似电影
            List<Movie> movies =
                    SimilarMovieProcess.getRecList(movieId, size, model);

            // 2️⃣ 兜底逻辑：LARGE / NCF 模型 embedding 覆盖不足
            if (movies == null || movies.isEmpty()) {
                System.out.println("[WARN] SimilarMovie empty, fallback to popular movies.");

                movies = DataManager.getInstance()
                        .getMovies(size, "rating");
            }

            // 3️⃣ 返回 JSON
            ObjectMapper mapper = new ObjectMapper();
            response.getWriter().println(mapper.writeValueAsString(movies));

        } catch (Exception e) {
            e.printStackTrace();
            response.getWriter().println("[]");
        }
    }
}
