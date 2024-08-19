<!DOCTYPE html>
<html>

<head>
    <meta charset="UTF-8" />
    <title>File Explorer</title>

    <meta name="viewport"
        content="width=device-width, initial-scale=1, shrink-to-fit=no, maximum-scale=1, user-scalable=no">
    <style>
html {
    height: 100%;
}
body {
    margin: 0;
    height: 100%;

    display: flex;
    flex-direction: column;

    font-family: sans-serif;
}
#path, #query, #content > div {
    margin: 0.5em 1.2em;
    display: flex;
}
#query, #content > div {
    flex-wrap: wrap;
}
#content > div {
    border: 1px solid black;
    border-radius: 0.5em;
}
#path > *, #content > div > * {
    margin: 0;
    padding: 1em;
}
#query > * {
    margin: 0;
    padding: 1em 0.5em;
}
#path a, #content a {
    text-decoration: none;
}
#content > div > *:first-child {
    flex: 1;
    overflow-wrap: anywhere;
}
#content > div > pre {
    font-family: Consolas, Menlo, Monaco, Lucida Console, Liberation Mono, DejaVu Sans Mono, Bitstream Vera Sans Mono, Courier New, monospace, serif;
}
@media (max-width: 768px) {
    #content > div > *:first-child {
        flex: unset;
        width: 100%;
    }
    #content > div > pre:nth-child(1) {
        order: 3;
    }
    #content > div > pre:nth-child(2) {
        order: 2;
    }
    #content > div > pre:nth-child(3) {
        order: 1;
    }
}
@media (prefers-color-scheme: dark) {
    body, #query input, #path a, #content a {
        background-color: rgb(30, 30, 30);
        color: rgb(200, 200, 200);
    }
    #content > div {
        border: 1px solid rgb(200, 200, 200);
    }
}
    </style>
</head>

<body>
    <div id="path">
        <h3>
            % for i, (url, part) in enumerate(path_parts):
            {{path_sep if i > 1 else ""}}
            <a href="{{url}}">{{part}}</a>
            % end
        </h3>
    </div>
    <div id="query">
        <label title="open file by url">
            file url:
            <input type="text" name="file_url" value="{{'' if file_url is None else file_url}}"
                placeholder="File link prefix">
        </label>
        <label title="show hidden folders & files">
            <input type="checkbox" name="show_hidden" {{"checked" if show_hidden else ""}}>
            show hidden
        </label>

        <label title="filter files by name">
            filter name:
            <input type="text" name="filter_name"
                value="{{'' if filter_name is None else filter_name}}"
                placeholder="Enter filename to filter">
        </label>
        <label title="filter filename case sensitive">
            <input type="checkbox" name="case_sensitive"
                {{"checked" if case_sensitive else ""}}>
            case sensitive
        </label>

        <label title="filter files by mime types">
            filter type:
            <input type="text" name="filter_type"
                value="{{'' if filter_type is None else ', '.join(filter_type)}}"
                placeholder="video, audio, image">
        </label>
        <label title="filter files recursively">
            <input type="checkbox" name="recursive_filter"
                {{"checked" if recursive_filter else ""}}>
            recursive filter
        </label>
    </div>
    <div id="content">
        % for folder in folders:
        <div>
            <a href="{{folder['url']}}">/{{folder["name"]}}</a>
            <pre>{{folder["mtime"]}}</pre>
        </div>
        % end
        % for file in files:
        <div>
            <a href="{{file['url']}}">{{file["name"]}}</a>
            <pre title="{{file['mime_type'] or ''}}">{{file["main_type"] or ''}}</pre>
            <pre>{{file["size"]}}</pre>
            <pre>{{file["mtime"]}}</pre>
        </div>
        % end
    </div>

    <script>
const checkboxInputs = document.querySelectorAll('#query input[type="checkbox"]');
const textInputs = document.querySelectorAll('#query input[type="text"]');

for (let i=0; i<checkboxInputs.length; ++i) {
    checkboxInputs[i].addEventListener("change", event => {
        const url = new URL(location.href);
        const name = event.currentTarget.getAttribute("name");
        if (url.searchParams.has(name)) {
            url.searchParams.delete(name);
        }
        else {
            url.searchParams.set(name, "");
        }
        location.href = url;
    });
}

for (let i=0; i<textInputs.length; ++i) {
    textInputs[i].addEventListener("keydown", event => {
        if (event.key !== "Enter") {
            return;
        }
        const url = new URL(location.href);
        const name = event.currentTarget.getAttribute("name");
        const value = event.currentTarget.value;
        if (value.length === 0) {
            url.searchParams.delete(name);
        }
        else {
            url.searchParams.set(name, value);
        }
        location.href = url;
    });
}
    </script>
</body>

</html>
