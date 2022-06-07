let GLOBAL_IS_LOADING_DATA = false;
let GLOBAL_LOADED_GAME_COUNT = 0;
let GLOBAL_LOADING_DATA_XHR = null;
let GLOBAL_GAME_OBJ_LIST = [];

function render_game_html_node(gameObj) {
    let anchor = document.createElement('a');
    anchor.href = `/gameinfo/${gameObj.index}`;

    let htmlGameNode = document.createElement('div');
    htmlGameNode.className = 'game-node';
    htmlGameNode.attributes['index'] = gameObj.index;

    anchor.appendChild(htmlGameNode);

    let el = document.createElement('div');
    el.textContent = gameObj.name;
    el.className = 'game-node-name';
    htmlGameNode.appendChild(el);

    el = document.createElement('div');
    el.className = 'game-node-image-container';
    htmlGameNode.appendChild(el);
    if (gameObj.banner_image != null) {
        let img = document.createElement('img');
        let originalImageUrl = gameObj.banner_image.url;
        let quotedImageUrl = encodeURIComponent(originalImageUrl);
        let actualImageUrl = `/api/images/${quotedImageUrl}`;
        img.src = actualImageUrl;
        img.className = 'game-node-image';
        el.appendChild(img);
    }

    // return htmlGameNode;
    return anchor;
}

function render_game_html_node_list(gameObjList) {
    let htmlGameNodeList = [];
    for (let i = 0; i < gameObjList.length; i++) {
        let gameObj = gameObjList[i];
        let htmlGameNode = render_game_html_node(gameObj);
        htmlGameNodeList.push(htmlGameNode);
    }

    return htmlGameNodeList;
}

let mainContainer = document.getElementById('main');

function append_game_html_node_list(htmlNodeList) {
    if (mainContainer == null) {
        console.error('mainContainer not found');
        return;
    }

    for (let i = 0; i < htmlNodeList.length; i++) {
        let htmlNode = htmlNodeList[i];
        mainContainer.appendChild(htmlNode);
    }
}

function fetch_game_data() {
    if (GLOBAL_IS_LOADING_DATA) {
        console.warn('already loading data');
        return;
    }

    GLOBAL_IS_LOADING_DATA = true;

    let xhr = new XMLHttpRequest();
    GLOBAL_LOADING_DATA_XHR = xhr;

    xhr.addEventListener('load', function () {
        GLOBAL_IS_LOADING_DATA = false;

        // to validate data and append the application state instead of replacing it
        let data = JSON.parse(xhr.responseText);
        if (data == null) {
            console.error('data is null');
            return;
        }

        console.log('data loaded');

        for (let i = 0; i < data.length; i++) {
            GLOBAL_GAME_OBJ_LIST.push(data[i]);
        }

        GLOBAL_LOADED_GAME_COUNT += data.length;

        setTimeout(function () {
            let gameNodeList = render_game_html_node_list(data);
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

let moreButton = document.getElementById('more');
if (moreButton != null) {
    moreButton.addEventListener('click', function () {
        fetch_game_data();
    });
}

if (mainContainer == null) {
    console.error('mainContainer not found');
} else {
    // parse search query into dictionary
    let searchQuery = window.location.search;
    let searchQueryDict = {};
    if (searchQuery != null && searchQuery.length > 1) {
        let searchQueryList = searchQuery.substring(1).split('&');
        for (let i = 0; i < searchQueryList.length; i++) {
            let searchQueryItem = searchQueryList[i];
            let searchQueryItemList = searchQueryItem.split('=');
            if (searchQueryItemList.length == 2) {
                let key = searchQueryItemList[0];
                let value = searchQueryItemList[1];
                searchQueryDict[key] = value;
            }
        }
    }

    if (searchQueryDict['index'] != null) {
        GLOBAL_LOADED_GAME_COUNT = parseInt(searchQueryDict['index']);
        let count = null;

        if (searchQueryDict['count'] != null) {
            count = parseInt(searchQueryDict['count']);
        }

        GLOBAL_IS_LOADING_DATA = true;

        let xhr = new XMLHttpRequest();
        GLOBAL_LOADING_DATA_XHR = xhr;

        xhr.addEventListener('load', function () {
            GLOBAL_IS_LOADING_DATA = false;

            // to validate data and append the application state instead of replacing it
            let data = JSON.parse(xhr.responseText);
            if (data == null) {
                console.error('data is null');
                return;
            }

            console.log('data loaded');

            for (let i = 0; i < data.length; i++) {
                GLOBAL_GAME_OBJ_LIST.push(data[i]);
            }

            GLOBAL_LOADED_GAME_COUNT += data.length;

            setTimeout(function () {
                let gameNodeList = render_game_html_node_list(data);
                append_game_html_node_list(gameNodeList);
            });
        });

        xhr.addEventListener('error', function () {
            GLOBAL_IS_LOADING_DATA = false;
            console.error('error loading data');
            console.error('status code: ' + xhr.status);
            console.error(xhr.responseText);
        });

        let url = `/api/games?index=${GLOBAL_LOADED_GAME_COUNT}`;
        if (count != null) {
            url += `&count=${count}`;
        }

        xhr.open('POST', url);
        xhr.send();
    } else {
        // fetch data
        fetch_game_data();
    }
}
