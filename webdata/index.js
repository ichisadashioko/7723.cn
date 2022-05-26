var mainContainer = document.getElementById('main');
if (mainContainer == null) {
    console.error('mainContainer not found');
} else {
    // fetch data
    var xhr = new XMLHttpRequest();

    xhr.addEventListener('load', function () {
        var data = JSON.parse(xhr.responseText);
        window.GAME_ENTRIES_INFO_LIST = data;
        console.log('data loaded');
    });

    xhr.addEventListener('error', function () {
        console.error('error loading data');
        console.error('status code: ' + xhr.status);
        console.error(xhr.responseText);
    });

    xhr.open('POST', '/api/games');
    xhr.send();
}
