// recsys.js - 汉化完整版（UTF-8）
// 保留原有逻辑，仅将界面文本/类别/提示汉化（电影标题不变）
// 依赖：jQuery 已在页面中引入

// ================= 全局类型映射表：英文 → 中文 =================
var genreMap = {
    "Action": "动作",
    "Adventure": "冒险",
    "Animation": "动画",
    "Children": "儿童",
    "Comedy": "喜剧",
    "Crime": "犯罪",
    "Documentary": "纪录片",
    "Drama": "剧情",
    "Fantasy": "奇幻",
    "Horror": "恐怖",
    "Musical": "音乐剧",
    "Mystery": "悬疑",
    "Romance": "爱情",
    "Sci-Fi": "科幻",
    "Thriller": "惊悚",
    "War": "战争",
    "Western": "西部",
    "Film-Noir": "黑色电影"
};

// ================= Helper: 将英文类型数组转为中文展示字符串 =================
function buildGenresHtml(genres, baseUrl) {
    var genresStr = "";
    $.each(genres, function(i, genre){
        var cn = genreMap[genre] || genre;
        genresStr += '<div class="genre"><a href="'+baseUrl+'collection.html?type=genre&value='+encodeURIComponent(genre)+'"><b>'+cn+'</b></a></div>';
    });
    return genresStr;
}

// ================= 添加单个电影卡片到行 =================
function appendMovie2Row(rowId, movieName, movieId, year, rating, rateNumber, genres, baseUrl) {

    var genresStr = buildGenresHtml(genres, baseUrl);

    var divstr = '<div class="movie-row-item" style="margin-right:5px">\
                    <movie-card-smart>\
                     <movie-card-md1>\
                      <div class="movie-card-md1">\
                       <div class="card">\
                        <link-or-emit>\
                         <a uisref="base.movie" href="'+baseUrl+'movie.html?movieId='+movieId+'">\
                         <span>\
                           <div class="poster">\
                            <img src="' + getPosterUrl(movieId) + '" onerror="handlePosterError(this, ' + movieId + ')" />\
                           </div>\
                           </span>\
                           </a>\
                        </link-or-emit>\
                        <div class="overlay">\
                         <div class="above-fold">\
                          <link-or-emit>\
                           <a uisref="base.movie" href="'+baseUrl+'movie.html?movieId='+movieId+'">\
                           <span><p class="title">' + movieName + '</p></span></a>\
                          </link-or-emit>\
                          <div class="rating-indicator">\
                           <ml4-rating-or-prediction>\
                            <div class="rating-or-prediction predicted">\
                             <svg class="star-icon" height="14px" version="1.1" viewbox="0 0 14 14" width="14px" xmlns="http://www.w3.org/2000/svg">\
                              <polygon fill-rule="evenodd" points="13.7714286 5.4939887 9.22142857 4.89188383 7.27142857 0.790044361 5.32142857 4.89188383 0.771428571 5.4939887 4.11428571 8.56096041 3.25071429 13.0202996 7.27142857 10.8282616 11.2921429 13.0202996 10.4285714 8.56096041" stroke="none"></polygon>\
                             </svg>\
                             <div class="rating-value">\
                              '+rating+'\
                             </div>\
                            </div>\
                           </ml4-rating-or-prediction>\
                          </div>\
                          <p class="year">'+year+' 年</p>\
                         </div>\
                         <div class="below-fold">\
                          <div class="genre-list">\
                           '+genresStr+'\
                          </div>\
                          <div class="ratings-display">\
                           <div class="rating-average">\
                            <span class="rating-large">'+rating+'</span>\
                            <span class="rating-total">/5 星</span>\
                            <p class="rating-caption"> '+rateNumber+' 人评分 </p>\
                           </div>\
                          </div>\
                         </div>\
                        </div>\
                       </div>\
                      </div>\
                     </movie-card-md1>\
                    </movie-card-smart>\
                   </div>';
    $('#'+rowId).append(divstr);
};

// ================= 行框架：带链接标题 =================
function addRowFrame(pageId, rowName, rowId, baseUrl) {
    var displayName = genreMap[rowName] || rowName;
    var divstr = '<div class="frontpage-section-top"> \
                <div class="explore-header frontpage-section-header">\
                 <a class="plainlink" title="查看完整列表" href="'+baseUrl+'collection.html?type=genre&value='+encodeURIComponent(rowName)+'">' + displayName + '</a> \
                </div>\
                <div class="movie-row">\
                 <div class="movie-row-bounds">\
                  <div class="movie-row-scrollable" id="' + rowId +'" style="margin-left: 0px;">\
                  </div>\
                 </div>\
                 <div class="clearfix"></div>\
                </div>\
               </div>';
    $(pageId).append(divstr);
};

// ================= 行框架：不带外部链接（备用） =================
function addRowFrameWithoutLink(pageId, titleText, rowId) {
    var divstr = '<div class="frontpage-section-top"> \
                <div class="explore-header frontpage-section-header">\
                 <span class="plainlink">' + titleText + '</span> \
                </div>\
                <div class="movie-row">\
                 <div class="movie-row-bounds">\
                  <div class="movie-row-scrollable" id="' + rowId +'" style="margin-left: 0px;">\
                  </div>\
                 </div>\
                 <div class="clearfix"></div>\
                </div>\
               </div>';
    $(pageId).append(divstr);
};

// ================= 添加按类型的推荐行 =================
function addGenreRow(pageId, rowName, rowId, size, baseUrl) {
    addRowFrame(pageId, rowName, rowId, baseUrl);
    $.getJSON(baseUrl + "getrecommendation?genre="+encodeURIComponent(rowName)+"&size="+size+"&sortby=rating", function(result){
        if(!result || !result.length){ return; }
        $.each(result, function(i, movie){
            appendMovie2Row(rowId, movie.title, movie.movieId, movie.releaseYear, movie.averageRating.toPrecision(2), movie.ratingNumber, movie.genres, baseUrl);
        });
    }).fail(function(){
        // 若请求失败，在该行显示错误提示
        $('#'+rowId).append('<div style="padding:12px;color:#a00">加载失败，请稍后重试</div>');
    });
};

// ================= 添加“相关电影” =================
function addRelatedMovies(pageId, containerId, movieId, baseUrl){
    addRowFrameWithoutLink(pageId, '相关电影', containerId);
    // replace the placeholder id usage: we created with id containerId
    $.getJSON(baseUrl + "getsimilarmovie?movieId="+encodeURIComponent(movieId)+"&size=16&model=emb", function(result){
        if(!result || !result.length){ return; }
        $.each(result, function(i, movie){
            appendMovie2Row(containerId, movie.title, movie.movieId, movie.releaseYear, movie.averageRating.toPrecision(2), movie.ratingNumber, movie.genres, baseUrl);
        });
    }).fail(function(){
        $('#'+containerId).append('<div style="padding:12px;color:#a00">加载失败，请稍后重试</div>');
    });
}

// ================= 添加“用户观看历史” =================
function addUserHistory(pageId, containerId, userId, baseUrl){
    addRowFrameWithoutLink(pageId, '用户观看历史', containerId);
    $.getJSON(baseUrl + "getuser?id="+encodeURIComponent(userId), function(userObject){
        if(!userObject || !userObject.ratings){ return; }
        $.each(userObject.ratings, function(i, rating){
            $.getJSON(baseUrl + "getmovie?id="+encodeURIComponent(rating.rating.movieId), function(movieObject){
                appendMovie2Row(containerId, movieObject.title, movieObject.movieId, movieObject.releaseYear, rating.rating.score, movieObject.ratingNumber, movieObject.genres, baseUrl);
            });
        });
    }).fail(function(){
        $('#'+containerId).append('<div style="padding:12px;color:#a00">无法加载用户信息</div>');
    });
}

// ================= 添加“为你推荐” =================
function addRecForYou(pageId, containerId, userId, model, baseUrl){
    addRowFrameWithoutLink(pageId, '为你推荐', containerId);
    $.getJSON(baseUrl + "getrecforyou?id="+encodeURIComponent(userId)+"&size=32&model=" + encodeURIComponent(model), function(result){
        if(!result || !result.length){ return; }
        $.each(result, function(i, movie){
            appendMovie2Row(containerId, movie.title, movie.movieId, movie.releaseYear, movie.averageRating.toPrecision(2), movie.ratingNumber, movie.genres, baseUrl);
        });
    }).fail(function(){
        $('#'+containerId).append('<div style="padding:12px;color:#a00">无法加载推荐结果</div>');
    });
}

// ================= 电影详情页：添加电影信息（汉化标签） =================
function addMovieDetails(containerId, movieId, baseUrl) {
    $.getJSON(baseUrl + "getmovie?id="+encodeURIComponent(movieId), function(movieObject){
        if(!movieObject){ $('#'+containerId).prepend('<div style="color:#a00">电影数据加载失败</div>'); return; }

        var genresHtml = "";
        $.each(movieObject.genres, function(i, genre){
            var cn = genreMap[genre] || genre;
            genresHtml += '<span><a href="'+baseUrl+'collection.html?type=genre&value='+encodeURIComponent(genre)+'"><b>'+cn+'</b></a>';
            if(i < movieObject.genres.length-1){ genresHtml += ", </span>"; } else { genresHtml += "</span>"; }
        });

        var ratingUsers = "";
        if(movieObject.topRatings && movieObject.topRatings.length){
            $.each(movieObject.topRatings, function(i, rating){
                ratingUsers += '<span><a href="'+baseUrl+'user.html?id='+encodeURIComponent(rating.rating.userId)+'"><b>用户'+rating.rating.userId+'</b></a>';
                if(i < movieObject.topRatings.length-1){ ratingUsers += ", </span>"; } else { ratingUsers += "</span>"; }
            });
        } else {
            ratingUsers = "<span>暂无数据</span>";
        }

        var movieDetails = '<div class="row movie-details-header movie-details-block">\
                                <div class="col-md-2 header-backdrop">\
                                    <img alt="电影海报" height="250" src="'+baseUrl+'posters/'+movieObject.movieId+'.jpg" onerror="this.onerror=null;this.src=\''+baseUrl+'images/poster-missing.png\';">\
                                </div>\
                                <div class="col-md-9"><h1 class="movie-title"> '+movieObject.title+' </h1>\
                                    <div class="row movie-highlights">\
                                        <div class="col-md-2">\
                                            <div class="heading-and-data">\
                                                <div class="movie-details-heading">上映年份</div>\
                                                <div> '+movieObject.releaseYear+' </div>\
                                            </div>\
                                            <div class="heading-and-data">\
                                                <div class="movie-details-heading">外部链接</div>\
                                                <a target="_blank" href="http://www.imdb.com/title/tt'+movieObject.imdbId+'">IMDb</a>,\
                                                <span><a target="_blank" href="http://www.themoviedb.org/movie/'+movieObject.tmdbId+'">TMDb</a></span>\
                                            </div>\
                                        </div>\
                                        <div class="col-md-3">\
                                            <div class="heading-and-data">\
                                                <div class="movie-details-heading">系统预测评分</div>\
                                                <div> 5.0 星</div>\
                                            </div>\
                                            <div class="heading-and-data">\
                                                <div class="movie-details-heading">平均评分（'+movieObject.ratingNumber+' 人）</div>\
                                                <div> '+movieObject.averageRating.toPrecision(2)+' 星</div>\
                                            </div>\
                                        </div>\
                                        <div class="col-md-6">\
                                            <div class="heading-and-data">\
                                                <div class="movie-details-heading">类型</div>\
                                                '+genresHtml+'\
                                            </div>\
                                            <div class="heading-and-data">\
                                                <div class="movie-details-heading">最喜欢此片的用户</div>\
                                                '+ratingUsers+'\
                                            </div>\
                                        </div>\
                                    </div>\
                                </div>\
                            </div>';
        $("#"+containerId).prepend(movieDetails);
    }).fail(function(){
        $('#'+containerId).prepend('<div style="color:#a00">加载电影详情失败</div>');
    });
};

// ================= 用户详情页：添加用户信息（汉化标签） =================
function addUserDetails(containerId, userId, baseUrl) {
    $.getJSON(baseUrl + "getuser?id="+encodeURIComponent(userId), function(userObject){
        if(!userObject){ $('#'+containerId).prepend('<div style="color:#a00">用户数据加载失败</div>'); return; }

        var favorite = userObject.favoriteGenre || "";
        var cnFavorite = genreMap[favorite] || favorite || "未知";

        var userDetails = '<div class="row movie-details-header movie-details-block">\
                                <div class="col-md-2 header-backdrop">\
                                    <img alt="用户头像" height="200" src="'+baseUrl+'images/avatar/'+(userObject.userId % 10)+'.png">\
                                </div>\
                                <div class="col-md-9"><h1 class="movie-title"> 用户'+userObject.userId+' </h1>\
                                    <div class="row movie-highlights">\
                                        <div class="col-md-2">\
                                            <div class="heading-and-data">\
                                                <div class="movie-details-heading">已看电影数</div>\
                                                <div> '+userObject.ratingCount+' </div>\
                                            </div>\
                                            <div class="heading-and-data">\
                                                <div class="movie-details-heading">平均评分</div>\
                                                <div> '+userObject.averageRating.toPrecision(2)+' 星</div>\
                                            </div>\
                                        </div>\
                                        <div class="col-md-3">\
                                            <div class="heading-and-data">\
                                                <div class="movie-details-heading">最高评分</div>\
                                                <div> '+userObject.highestRating+' 星</div>\
                                            </div>\
                                            <div class="heading-and-data">\
                                                <div class="movie-details-heading">最低评分</div>\
                                                <div> '+userObject.lowestRating+' 星</div>\
                                            </div>\
                                        </div>\
                                        <div class="col-md-6">\
                                            <div class="heading-and-data">\
                                                <div class="movie-details-heading">最喜爱类型</div>\
                                                <div> '+cnFavorite+' </div>\
                                            </div>\
                                        </div>\
                                    </div>\
                                </div>\
                            </div>';
        $("#"+containerId).prepend(userDetails);
    }).fail(function(){
        $('#'+containerId).prepend('<div style="color:#a00">加载用户信息失败</div>');
    });
};

// ================= 模型管理（汉化提示） =================
var ModelManager = {
    // 初始化
    init: function() {
        this.loadModelList();
    },

    // 加载模型列表
    loadModelList: function() {
        var self = this;
        $.ajax({
            url: '/getmodel?action=list',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                if (data && data.success) {
                    self.renderModelList(data.models, data.currentModel);
                } else {
                    console && console.warn('加载模型列表失败', data && data.message);
                    // 如果页面有元素显示模型状态，可进行显示
                    $('#modelSelect').empty().append($('<option>').text('加载失败'));
                    $('#modelStatus').text('加载模型失败').css('color','red');
                }
            },
            error: function() {
                $('#modelSelect').empty().append($('<option>').text('无法连接'));
                $('#modelStatus').text('无法连接到服务器').css('color','red');
            }
        });
    },

    // 渲染模型列表（假定页面存在 #modelSelect #modelStatus）
    renderModelList: function(models, currentModel) {
        var sel = $('#modelSelect');
        if(!sel || !sel.length) return;
        sel.empty();
        $.each(models || [], function(i, m){
            var name = m.displayName || m.version;
            if(m.version === 'STANDARD') name = '标准版本';
            if(m.version === 'LARGE') name = '大数据集版本';
            if(m.version === 'NCF') name = 'NCF 深度学习版本';
            var opt = $('<option>').val(m.version).text(name);
            if(m.isCurrent) opt.prop('selected', true);
            sel.append(opt);
        });
        if(currentModel && currentModel.displayName){
            $('#modelStatus').text('当前模型：' + (currentModel.displayName)).css('color','green');
        } else {
            $('#modelStatus').text('当前模型：' + (sel.find('option:selected').text()||'未设置')).css('color','green');
        }
    },

    // 切换模型（供页面按钮触发）
    switchModel: function(version) {
        if(!version) return;
        $('#modelStatus').text('正在切换模型...').css('color','blue');
        $.ajax({
            url: '/getmodel',
            type: 'POST',
            data: { action: 'switch', version: version },
            dataType: 'json',
            success: function(res){
                if(res && res.success){
                    $('#modelStatus').text('已切换到：' + (res.current || version)).css('color','green');
                    // 可选：局部重载推荐
                }else{
                    $('#modelStatus').text('切换失败：' + (res && res.message || '')).css('color','red');
                }
            },
            error: function(){
                $('#modelStatus').text('切换请求失败').css('color','red');
            }
        });
    }
};

// ================= 页面初始化（示例：加载首页若干类型推荐） =================
$(document).ready(function(){
    // 若页面中存在模型选择元素，则初始化 ModelManager
    if($('#modelSelect').length) {
        ModelManager.init();

        // 绑定切换按钮（若存在）
        $('#switchModelBtn').on('click', function(){
            var v = $('#modelSelect').val();
            if(!v){ $('#modelStatus').text('请选择模型'); return; }
            $(this).prop('disabled', true).text('切换中...');
            ModelManager.switchModel(v);
            var that = this;
            setTimeout(function(){ $(that).prop('disabled', false).text('切换模型'); }, 1500);
        });
    }

    // 首页常见类型（中文显示由 genreMap 控制）
    var baseUrl = window.location.protocol + '//' + window.location.host + '/';

    // 仅在首页（存在 #recPage）时添加默认行
    if($('#recPage').length) {
        addGenreRow('#recPage', 'Adventure', 'adventure-collection', 8, baseUrl);
        addGenreRow('#recPage', 'Drama', 'drama-collection', 8, baseUrl);
        addGenreRow('#recPage', 'Comedy', 'comedy-collection', 8, baseUrl);
        addGenreRow('#recPage', 'Thriller', 'thriller-collection', 8, baseUrl);
        addGenreRow('#recPage', 'Romance', 'romance-collection', 8, baseUrl);
        addGenreRow('#recPage', 'Action', 'action-collection', 8, baseUrl);
    }
});
