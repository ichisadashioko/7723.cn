var GLOBAL_IS_LOADING_DATA = false;
var GLOBAL_LOADED_GAME_COUNT = 0;
var GLOBAL_LOADING_DATA_XHR = null;
var GLOBAL_GAME_OBJ_LIST = [];

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

function append_game_html_node_list(htmlNodeList) {
    if (mainContainer == null) {
        console.error('mainContainer not found');
        return;
    }

    for (var i = 0; i < htmlNodeList.length; i++) {
        var htmlNode = htmlNodeList[i];
        mainContainer.appendChild(htmlNode);
    }
}

function fetch_game_data() {
    if (GLOBAL_IS_LOADING_DATA) {
        console.warn('already loading data');
        return;
    }

    GLOBAL_IS_LOADING_DATA = true;

    var xhr = new XMLHttpRequest();
    GLOBAL_LOADING_DATA_XHR = xhr;

    xhr.addEventListener('load', function () {
        GLOBAL_IS_LOADING_DATA = false;

        // to validate data and append the application state instead of replacing it
        var data = JSON.parse(xhr.responseText);
        if (data == null) {
            console.error('data is null');
            return;
        }

        console.log('data loaded');

        for (var i = 0; i < data.length; i++) {
            GLOBAL_GAME_OBJ_LIST.push(data[i]);
        }

        GLOBAL_LOADED_GAME_COUNT += data.length;

        setTimeout(function () {
            var gameNodeList = render_game_html_node_list(data);
            append_game_html_node_list(gameNodeList);
        });
    });

    xhr.addEventListener('error', function () {
        GLOBAL_IS_LOADING_DATA = false;
        console.error('error loading data');
        console.error('status code: ' + xhr.status);
        console.error(xhr.responseText);
    });

    xhr.open('POST', `/api/games?index=${GLOBAL_LOADED_GAME_COUNT}`);
    xhr.send();
}

var moreButton = document.getElementById('more');
if (moreButton != null) {
    moreButton.addEventListener('click', function () {
        fetch_game_data();
    });
}

if (mainContainer == null) {
    console.error('mainContainer not found');
} else {
    // fetch data
    fetch_game_data();
}
