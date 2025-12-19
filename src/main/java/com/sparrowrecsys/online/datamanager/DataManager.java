package com.sparrowrecsys.online.datamanager;

import com.sparrowrecsys.online.util.Config;
import com.sparrowrecsys.online.util.Utility;

import java.io.File;
import java.util.*;

/**
 * DataManager is an utility class, takes charge of all data loading logic.
 */
public class DataManager {
    //singleton instance
    private static volatile DataManager instance;
    HashMap<Integer, Movie> movieMap;
    HashMap<Integer, User> userMap;
    //genre reverse index for quick querying all movies in a genre
    HashMap<String, List<Movie>> genreReverseIndexMap;

    // ========== 新增：NCF得分存储（仅新增，无其他改动） ==========
    // 存储NCF预测得分，key格式：userId_movieId，value：预测得分
    private Map<String, Double> ncfPredictScores = new HashMap<>();

    private DataManager(){
        this.movieMap = new HashMap<>();
        this.userMap = new HashMap<>();
        this.genreReverseIndexMap = new HashMap<>();
        instance = this;
    }

    public static DataManager getInstance(){
        if (null == instance){
            synchronized (DataManager.class){
                if (null == instance){
                    instance = new DataManager();
                }
            }
        }
        return instance;
    }

    //load data from file system including movie, rating, link data and model data like embedding vectors.
    public void loadData(String movieDataPath, String linkDataPath, String ratingDataPath, String movieEmbPath, String userEmbPath, String movieRedisKey, String userRedisKey) throws Exception{
        loadMovieData(movieDataPath);
        loadLinkData(linkDataPath);
        loadRatingData(ratingDataPath);
        loadMovieEmb(movieEmbPath, movieRedisKey);
        if (Config.IS_LOAD_ITEM_FEATURE_FROM_REDIS){
            loadMovieFeatures("mf:");
        }

        loadUserEmb(userEmbPath, userRedisKey);
    }

    //load movie data from movies.csv
    private void loadMovieData(String movieDataPath) throws Exception{
        System.out.println("Loading movie data from " + movieDataPath + " ...");
        boolean skipFirstLine = true;
        try (Scanner scanner = new Scanner(new File(movieDataPath))) {
            while (scanner.hasNextLine()) {
                String movieRawData = scanner.nextLine();
                if (skipFirstLine){
                    skipFirstLine = false;
                    continue;
                }
                String[] movieData = movieRawData.split(",");
                if (movieData.length == 3){
                    Movie movie = new Movie();
                    movie.setMovieId(Integer.parseInt(movieData[0]));
                    int releaseYear = parseReleaseYear(movieData[1].trim());
                    if (releaseYear == -1){
                        movie.setTitle(movieData[1].trim());
                    }else{
                        movie.setReleaseYear(releaseYear);
                        movie.setTitle(movieData[1].trim().substring(0, movieData[1].trim().length()-6).trim());
                    }
                    String genres = movieData[2];
                    if (!genres.trim().isEmpty()){
                        String[] genreArray = genres.split("\\|");
                        for (String genre : genreArray){
                            movie.addGenre(genre);
                            addMovie2GenreIndex(genre, movie);
                        }
                    }
                    this.movieMap.put(movie.getMovieId(), movie);
                }
            }
        }
        System.out.println("Loading movie data completed. " + this.movieMap.size() + " movies in total.");
    }

    //load movie embedding
    private void loadMovieEmb(String movieEmbPath, String embKey) throws Exception{
        if (Config.EMB_DATA_SOURCE.equals(Config.DATA_SOURCE_FILE)) {
            System.out.println("Loading movie embedding from " + movieEmbPath + " ...");
            int validEmbCount = 0;
            try (Scanner scanner = new Scanner(new File(movieEmbPath))) {
                while (scanner.hasNextLine()) {
                    String movieRawEmbData = scanner.nextLine();
                    String[] movieEmbData = movieRawEmbData.split(":");
                    if (movieEmbData.length == 2) {
                        Movie m = getMovieById(Integer.parseInt(movieEmbData[0]));
                        if (null == m) {
                            continue;
                        }
                        m.setEmb(Utility.parseEmbStr(movieEmbData[1]));
                        validEmbCount++;
                    }
                }
            }
            System.out.println("Loading movie embedding completed. " + validEmbCount + " movie embeddings in total.");
        }else{
            System.out.println("Loading movie embedding from Redis ...");
            Set<String> movieEmbKeys = RedisClient.getInstance().keys(embKey + "*");
            int validEmbCount = 0;
            for (String movieEmbKey : movieEmbKeys){
                String movieId = movieEmbKey.split(":")[1];
                Movie m = getMovieById(Integer.parseInt(movieId));
                if (null == m) {
                    continue;
                }
                m.setEmb(Utility.parseEmbStr(RedisClient.getInstance().get(movieEmbKey)));
                validEmbCount++;
            }
            System.out.println("Loading movie embedding completed. " + validEmbCount + " movie embeddings in total.");
        }
    }

    //load movie features
    private void loadMovieFeatures(String movieFeaturesPrefix) throws Exception{
        System.out.println("Loading movie features from Redis ...");
        Set<String> movieFeaturesKeys = RedisClient.getInstance().keys(movieFeaturesPrefix + "*");
        int validFeaturesCount = 0;
        for (String movieFeaturesKey : movieFeaturesKeys){
            String movieId = movieFeaturesKey.split(":")[1];
            Movie m = getMovieById(Integer.parseInt(movieId));
            if (null == m) {
                continue;
            }
            m.setMovieFeatures(RedisClient.getInstance().hgetAll(movieFeaturesKey));
            validFeaturesCount++;
        }
        System.out.println("Loading movie features completed. " + validFeaturesCount + " movie features in total.");
    }

    //load user embedding
    private void loadUserEmb(String userEmbPath, String embKey) throws Exception{
        if (Config.EMB_DATA_SOURCE.equals(Config.DATA_SOURCE_FILE)) {
            System.out.println("Loading user embedding from " + userEmbPath + " ...");
            int validEmbCount = 0;
            try (Scanner scanner = new Scanner(new File(userEmbPath))) {
                while (scanner.hasNextLine()) {
                    String userRawEmbData = scanner.nextLine();
                    String[] userEmbData = userRawEmbData.split(":");
                    if (userEmbData.length == 2) {
                        // ========== Only modify this ID parsing logic (add compatibility) ==========
                        int userId;
                        String userIdStr = userEmbData[0];
                        if (userIdStr.startsWith("user_")) {
                            // Compatible with user_N format for large dataset
                            userId = Integer.parseInt(userIdStr.substring(5));
                        } else {
                            // Keep original logic for pure numeric format
                            userId = Integer.parseInt(userIdStr);
                        }
                        // ========== End of modification ==========

                        User u = getUserById(userId);
                        if (null == u) {
                            continue;
                        }
                        u.setEmb(Utility.parseEmbStr(userEmbData[1]));
                        validEmbCount++;
                    }
                }
            }
            System.out.println("Loading user embedding completed. " + validEmbCount + " user embeddings in total.");
        }
    }

    //parse release year
    private int parseReleaseYear(String rawTitle){
        if (null == rawTitle || rawTitle.trim().length() < 6){
            return -1;
        }else{
            String yearString = rawTitle.trim().substring(rawTitle.length()-5, rawTitle.length()-1);
            try{
                return Integer.parseInt(yearString);
            }catch (NumberFormatException exception){
                return -1;
            }
        }
    }

    //load links data from links.csv
    private void loadLinkData(String linkDataPath) throws Exception{
        System.out.println("Loading link data from " + linkDataPath + " ...");
        int count = 0;
        boolean skipFirstLine = true;
        try (Scanner scanner = new Scanner(new File(linkDataPath))) {
            while (scanner.hasNextLine()) {
                String linkRawData = scanner.nextLine();
                if (skipFirstLine){
                    skipFirstLine = false;
                    continue;
                }
                String[] linkData = linkRawData.split(",");
                if (linkData.length == 3){
                    int movieId = Integer.parseInt(linkData[0]);
                    Movie movie = this.movieMap.get(movieId);
                    if (null != movie){
                        count++;
                        movie.setImdbId(linkData[1].trim());
                        movie.setTmdbId(linkData[2].trim());
                    }
                }
            }
        }
        System.out.println("Loading link data completed. " + count + " links in total.");
    }

    //load ratings data from ratings.csv
    private void loadRatingData(String ratingDataPath) throws Exception{
        System.out.println("Loading rating data from " + ratingDataPath + " ...");
        boolean skipFirstLine = true;
        int count = 0;
        try (Scanner scanner = new Scanner(new File(ratingDataPath))) {
            while (scanner.hasNextLine()) {
                String ratingRawData = scanner.nextLine();
                if (skipFirstLine){
                    skipFirstLine = false;
                    continue;
                }
                String[] linkData = ratingRawData.split(",");
                if (linkData.length == 4){
                    count ++;
                    Rating rating = new Rating();
                    rating.setUserId(Integer.parseInt(linkData[0]));
                    rating.setMovieId(Integer.parseInt(linkData[1]));
                    rating.setScore(Float.parseFloat(linkData[2]));
                    rating.setTimestamp(Long.parseLong(linkData[3]));
                    Movie movie = this.movieMap.get(rating.getMovieId());
                    if (null != movie){
                        movie.addRating(rating);
                    }
                    if (!this.userMap.containsKey(rating.getUserId())){
                        User user = new User();
                        user.setUserId(rating.getUserId());
                        this.userMap.put(user.getUserId(), user);
                    }
                    this.userMap.get(rating.getUserId()).addRating(rating);
                }
            }
        }

        System.out.println("Loading rating data completed. " + count + " ratings in total.");
    }

    //add movie to genre reversed index
    private void addMovie2GenreIndex(String genre, Movie movie){
        if (!this.genreReverseIndexMap.containsKey(genre)){
            this.genreReverseIndexMap.put(genre, new ArrayList<>());
        }
        this.genreReverseIndexMap.get(genre).add(movie);
    }

    //get movies by genre, and order the movies by sortBy method
    public List<Movie> getMoviesByGenre(String genre, int size, String sortBy){
        if (null != genre){
            List<Movie> movies = new ArrayList<>(this.genreReverseIndexMap.get(genre));
            switch (sortBy){
                case "rating":movies.sort((m1, m2) -> Double.compare(m2.getAverageRating(), m1.getAverageRating()));break;
                case "releaseYear": movies.sort((m1, m2) -> Integer.compare(m2.getReleaseYear(), m1.getReleaseYear()));break;
                default:
            }

            if (movies.size() > size){
                return movies.subList(0, size);
            }
            return movies;
        }
        return null;
    }

    //get top N movies order by sortBy method
    public List<Movie> getMovies(int size, String sortBy){
        List<Movie> movies = new ArrayList<>(movieMap.values());
        switch (sortBy){
            case "rating":movies.sort((m1, m2) -> Double.compare(m2.getAverageRating(), m1.getAverageRating()));break;
            case "releaseYear": movies.sort((m1, m2) -> Integer.compare(m2.getReleaseYear(), m1.getReleaseYear()));break;
            default:
        }

        if (movies.size() > size){
            return movies.subList(0, size);
        }
        return movies;
    }

    //get movie object by movie id
    public Movie getMovieById(int movieId){
        return this.movieMap.get(movieId);
    }

    //get user object by user id
    public User getUserById(int userId){
        return this.userMap.get(userId);
    }

    // ========== 实验手册要求的重载方法（原有保留） ==========
    public void reloadEmbeddings(String modelDataPath, String movieEmbFile, String userEmbFile) throws Exception {
        String movieEmbPath = modelDataPath + movieEmbFile;
        String userEmbPath = modelDataPath + userEmbFile;

        System.out.println("Reloading embedding model:");
        System.out.println("Movie embedding: " + movieEmbPath);
        System.out.println("User embedding: " + userEmbPath);

        // Clear existing embedding data
        for (Movie movie : movieMap.values()) {
            movie.setEmb(null);
        }
        for (User user : userMap.values()) {
            user.setEmb(null);
        }

        // Reload embeddings (reuse existing loading methods, no new logic)
        loadMovieEmb(movieEmbPath, "i2vEmb");
        loadUserEmb(userEmbPath, "uEmb");

        System.out.println(" Embedding model reloaded successfully!");
    }

    // ========== 新增：NCF相关方法（仅新增，不改动原有逻辑） ==========
    /**
     * 加载NCF预测得分文件（仅NCF模型使用）
     * @param scoreFilePath NCF得分文件路径
     */
    private void loadNCFPredictScores(String scoreFilePath) throws Exception {
        // 清空原有得分（避免模型切换时数据残留）
        ncfPredictScores.clear();
        if (scoreFilePath == null || scoreFilePath.isEmpty()) {
            return; // 非NCF模型，直接返回
        }

        System.out.println("Loading NCF predict scores from " + scoreFilePath + " ...");
        int validScoreCount = 0;
        try (Scanner scanner = new Scanner(new File(scoreFilePath))) {
            while (scanner.hasNextLine()) {
                String line = scanner.nextLine().trim();
                if (line.isEmpty()) continue;

                String[] parts = line.split(":");
                if (parts.length == 2) {
                    String userItemKey = parts[0]; // 格式：userId_movieId
                    double score = Double.parseDouble(parts[1]);
                    ncfPredictScores.put(userItemKey, score);
                    validScoreCount++;
                }
            }
        }
        System.out.println("Loading NCF predict scores completed. " + validScoreCount + " scores in total.");
    }

    /**
     * 扩展重载方法：支持加载NCF得分（兼容原有重载逻辑）
     * @param modelDataPath 模型数据根路径
     * @param movieEmbFile 电影Emb文件名称
     * @param userEmbFile 用户Emb文件名称
     * @param ncfScoreFile NCF得分文件名称（非NCF模型传空）
     */
    public void reloadEmbeddings(String modelDataPath, String movieEmbFile, String userEmbFile, String ncfScoreFile) throws Exception {
        // 先执行原有重载逻辑（保证实验手册兼容性）
        reloadEmbeddings(modelDataPath, movieEmbFile, userEmbFile);

        // 再加载NCF得分（仅当文件路径非空时）
        if (ncfScoreFile != null && !ncfScoreFile.isEmpty()) {
            String scoreFilePath = modelDataPath + ncfScoreFile;
            loadNCFPredictScores(scoreFilePath);
        } else {
            // 非NCF模型，清空得分（避免数据残留）
            ncfPredictScores.clear();
        }
    }

    /**
     * 获取指定用户-电影的NCF预测得分（供推荐服务调用）
     * @param userId 用户ID
     * @param movieId 电影ID
     * @return 预测得分（无得分返回0.0）
     */
    public double getNCFPredictScore(int userId, int movieId) {
        String key = userId + "_" + movieId;
        return ncfPredictScores.getOrDefault(key, 0.0);
    }
}