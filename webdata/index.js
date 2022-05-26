function render_game_html_node(gameObj) {
    var htmlGameNode = document.createElement('div');
    htmlGameNode.className = 'game-node';

    var el = document.createElement('div');
    el.textContent = gameObj.name;
    htmlGameNode.appendChild(el);

    // TODO
}

function render_game_html_node_list(gameObjList) {
    var htmlGameNodeList = [];
    for (var i = 0; i < gameObjList.length; i++) {
        var gameObj = gameObjList[i];
        var htmlGameNode = render_game_html_node(gameObj);
        // TODO
    }
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

        // TODO
    });

    xhr.addEventListener('error', function () {
        console.error('error loading data');
        console.error('status code: ' + xhr.status);
        console.error(xhr.responseText);
    });

    xhr.open('POST', '/api/games');
    xhr.send();
}
