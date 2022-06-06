function render_game_html_node(gameObj) {
    var htmlGameNode = document.createElement('div');
    htmlGameNode.className = 'game-node';

    var el = document.createElement('div');
    el.textContent = gameObj.name;
    el.className = 'game-node-name';
    htmlGameNode.appendChild(el);

    el = document.createElement('div');
    el.className = 'game-node-image-container';
    htmlGameNode.appendChild(el);
    if (gameObj.banner_image != null) {
        var img = document.createElement('img');
        var originalImageUrl = gameObj.banner_image.url;
        var quotedImageUrl = encodeURIComponent(originalImageUrl);
        var actualImageUrl = `/api/images/${quotedImageUrl}`;
        img.src = actualImageUrl;
        img.className = 'game-node-image';
        el.appendChild(img);
    }

    return htmlGameNode;
}

function render_game_html_node_list(gameObjList) {
    var htmlGameNodeList = [];
    for (var i = 0; i < gameObjList.length; i++) {
        var gameObj = gameObjList[i];
        var htmlGameNode = render_game_html_node(gameObj);
        htmlGameNodeList.push(htmlGameNode);
    }

    return htmlGameNodeList;
}

var mainContainer = document.getElementById('main');
if (mainContainer == null) {
    console.error('mainContainer not found');
} else {
    // fetch data
    var xhr = new XMLHttpRequest();

    xhr.addEventListener('load', function () {
        // to validate data and append the application state instead of replacing it
        var data = JSON.parse(xhr.responseText);
        window.GAME_ENTRIES_INFO_LIST = data;
        console.log('data loaded');

        setTimeout(function () {
            var gameNodeList = render_game_html_node_list(data);
            for (var i = 0; i < gameNodeList.length; i++) {
                mainContainer.appendChild(gameNodeList[i]);
            }
        });
    });

    xhr.addEventListener('error', function () {
        console.error('error loading data');
        console.error('status code: ' + xhr.status);
        console.error(xhr.responseText);
    });

    xhr.open('POST', '/api/games');
    xhr.send();
}
