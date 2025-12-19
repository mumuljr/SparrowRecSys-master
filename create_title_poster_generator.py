import csv
import json
import os
def create_title_based_posters():
    """
    创建基于电影标题的海报映射
    """
    print("创建基于电影标题的海报映射...")
    # 读取电影数据
    movies = {}
    with open('src/main/resources/webroot/sampledata/movies.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            movie_id = int(row['movieId'])
            title = row['title'].strip()
            genres = row['genres'].strip()
            # 清理标题，移除年份
            clean_title = title
            if '(' in title and ')' in title:
                clean_title = title[:title.rfind('(')].strip()
            movies[movie_id] = {
                'title': clean_title,
                'full_title': title,
                'genres': genres
            }
    print(f"读取了 {len(movies)} 部电影的信息")
    # 生成JavaScript海报生成器
    js_content = """// 基于电影标题的动态海报生成器
// 电影信息映射
var movieInfo = """ + json.dumps(movies, indent=2, ensure_ascii=False) + """;
// 类型颜色主题
var genreColors = {
    'Action': '#e74c3c',      // 动作 - 红色
    'Adventure': '#f39c12',   // 冒险 - 橙色
    'Animation': '#9b59b6',   // 动画 - 紫色
    'Children': '#1abc9c',    // 儿童 - 青色
    'Comedy': '#f1c40f',      // 喜剧 - 黄色
    'Crime': '#34495e',       // 犯罪 - 深灰
    'Documentary': '#95a5a6', // 纪录片 - 银色
    'Drama': '#2c3e50',       // 剧情 - 深蓝
    'Fantasy': '#8e44ad',     // 奇幻 - 深紫
    'Horror': '#c0392b',      // 恐怖 - 暗红
    'Musical': '#e67e22',     // 音乐剧 - 橙红
    'Mystery': '#16a085',     // 悬疑 - 蓝绿
    'Romance': '#e91e63',     // 爱情 - 粉色
    'Sci-Fi': '#3498db',      // 科幻 - 蓝色
    'Thriller': '#27ae60',    // 惊悚 - 绿色
    'War': '#7f8c8d',         // 战争 - 灰色
    'Western': '#d35400'      // 西部 - 棕色
};
// 获取类型颜色
function getGenreColor(genres) {
    if (!genres || genres === '(no genres listed)') {
        return '#34495e';
    }
    var genreList = genres.split('|');
    var genre = genreList[0];
    return genreColors[genre] || '#34495e';
}
// 获取电影海报URL
function getPosterUrl(movieId) {
    // 1. 优先使用本地海报 (ID ≤ 1000)
    if (movieId <= 1000) {
        return './posters/' + movieId + '.jpg';
    }
    // 2. 生成动态海报
    return generateMoviePoster(movieId);
}
// 动态生成电影海报
function generateMoviePoster(movieId) {
    var movie = movieInfo[movieId];
    if (!movie) {
        return './images/default-poster.svg';
    }
    var title = movie.title || 'Unknown Movie';
    var genres = movie.genres || '';
    var color = getGenreColor(genres);
    // 限制标题长度并分行
    var displayTitle = title.length > 25 ? title.substring(0, 22) + '...' : title;
    var lines = [];
    if (displayTitle.length > 15) {
        var words = displayTitle.split(' ');
        var currentLine = '';
        for (var i = 0; i < words.length; i++) {
            if (currentLine.length + words[i].length + 1 <= 15) {
                currentLine += (currentLine ? ' ' : '') + words[i];
            } else {
                if (currentLine) lines.push(currentLine);
                currentLine = words[i];
            }
        }
        if (currentLine) lines.push(currentLine);
    } else {
        lines.push(displayTitle);
    }
    // 确保最多3行
    if (lines.length > 3) {
        lines = lines.slice(0, 2);
        lines.push('...');
    }
    // 创建SVG海报
    var svg = '<svg width="300" height="450" xmlns="http://www.w3.org/2000/svg">' +
              '<defs>' +
              '<linearGradient id="grad" x1="0%" y1="0%" x2="0%" y2="100%">' +
              '<stop offset="0%" style="stop-color:' + color + ';stop-opacity:1" />' +
              '<stop offset="100%" style="stop-color:#2c3e50;stop-opacity:1" />' +
              '</linearGradient>' +
              '</defs>' +
              '<rect width="300" height="450" fill="url(#grad)"/>' +
              '<rect x="20" y="20" width="260" height="410" fill="none" stroke="white" stroke-width="2" opacity="0.3"/>';
    // 添加标题文本
    var startY = 180;
    for (var i = 0; i < lines.length; i++) {
        svg += '<text x="150" y="' + (startY + i * 25) + '" font-family="Arial, sans-serif" font-size="18" ' +
               'font-weight="bold" fill="white" text-anchor="middle">' + 
               lines[i] + '</text>';
    }
    // 添加ID和类型信息
    svg += '<text x="150" y="' + (startY + lines.length * 25 + 20) + '" font-family="Arial, sans-serif" ' +
           'font-size="14" fill="#bdc3c7" text-anchor="middle">ID: ' + movieId + '</text>';
    var genre = genres.split('|')[0] || 'Movie';
    svg += '<text x="150" y="' + (startY + lines.length * 25 + 40) + '" font-family="Arial, sans-serif" ' +
           'font-size="12" fill="#ecf0f1" text-anchor="middle">' + genre + '</text>';
    // 添加播放按钮图标
    svg += '<circle cx="150" cy="350" r="25" fill="white" opacity="0.2"/>' +
           '<polygon points="140,340 140,360 165,350" fill="white"/>';
    svg += '</svg>';
    // 返回Base64编码的SVG
    return 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svg)));
}
// 错误处理函数
function handlePosterError(imgElement, movieId) {
    imgElement.src = './images/default-poster.svg';
}
// 获取备用海报URL
function getBackupPosterUrl(movieId) {
    return generateMoviePoster(movieId);
}
"""
    # 保存JavaScript文件
    output_file = 'src/main/resources/webroot/js/poster-links.js'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print(f"动态海报生成器已保存到: {output_file}")
    print(f"包含 {len(movies)} 部电影的信息")
def main():
    """主函数"""
    print("=== 基于电影标题的动态海报生成器 ===")
    if not os.path.exists('src/main/resources/webroot/sampledata/movies.csv'):
        print("错误: 找不到movies.csv文件")
        return
    try:
        create_title_based_posters()
        print("\\n=== 动态海报生成器创建完成 ===")
        print("特性:")
        print("- ✅ 基于电影标题生成海报")
        print("- ✅ 按类型分配颜色主题")
        print("- ✅ 智能文本分行显示")
        print("- ✅ 包含电影ID和类型信息")
        print("- ✅ 本地海报优先 (ID ≤ 1000)")
        print("- ✅ SVG矢量图形高清显示")
    except Exception as e:
        print(f"创建时出错: {e}")
        import traceback
        traceback.print_exc()
if __name__ == "__main__":
    main()