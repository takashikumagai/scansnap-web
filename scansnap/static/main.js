
var url = 'ws://' + location.hostname + ':2479';
console.log('WebSocket URL:',url);

// Creating a websocket automatically attempts to open the connection
// to the server
webSocket = new WebSocket(url);

webSocket.onopen = function(event) {
    console.log('Connection established.');
}

webSocket.onmessage = function(event) {
    console.log('Message received:',event.data);

    let msg = JSON.parse(event.data);
    console.log('msg:', msg);

    if(msg.state) {
        console.log('state', msg.state);
        switch(msg.state) {
            case 'scan_complete':
                break;
            case 'converting':
                break;
            case 'conversion_complete':
                console.log('Showing the download button');
                document.querySelector('#download-form').style.visibility = "visible";
                console.log('msg.download_pdf_url:',msg.download_pdf_url)
                document.querySelector('#download-form').action = msg.download_pdf_url;
                document.querySelector('#download-button').textContent = `Download PDF (${msg.pdf_file_size} MB)`
                break;
            default:
                break;
        }

        document.querySelector('#status-message').textContent = msg.message;
    }
}

webSocket.onerror = function(event) {
    console.log('ws error:',event);
}

webSocket.onclose = function(event) {
    console.log('ws closed:',event);
}

fetch('/get-scanner-info')
    .then(response => response.json())
    .then(data => {
        console.log(data);
        if(data.scanner_found) {
            document.querySelector('#scan-btn-container').style.visibility = 'visible';
            document.querySelector('#scanner-name').textContent = data.scanner_name;
        } else {
            document.querySelector('#scan-btn-container').style.visibility = 'hidden';
            document.querySelector('#scanner-name').textContent = 'Scanner not found';
        }
    });
