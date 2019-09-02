<!DOCTYPE html>
<html>
    <head>
        <title>Drive</title>
        <style>
            body{
                margin-left: 15%;
                margin-right: 15%;
                margin-top: 3%;
                font-family: sans-serif;
                font-size: 22px;
            }
            a {
                text-decoration: none;
            }
        </style>
    </head>
    <body>
    <script>
function myAjaxPost(url, dataObj, doneFunction) {
    var xhttp = new XMLHttpRequest();
    xhttp.open("POST", url, true);
    xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhttp.onreadystatechange = function() {
        if (this.readyState == XMLHttpRequest.DONE) { // ajax done == 4
            doneFunction(this);
        }
    };
    var sendString = "";
    for (var key in dataObj) {
        sendString += "&" + key + "=" + encodeURIComponent(dataObj[key]);
    }
    xhttp.send(sendString.slice(1));
}
function play_media(url){
    myAjaxPost("/ccast/play_media", {
        url: url
    }, function(){});
}
    </script>
{{!body_string}}
    </body>
</html>
