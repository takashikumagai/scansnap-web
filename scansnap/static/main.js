
var url = 'ws://' + location.hostname + ':2479';
console.log('WebSocket URL:',url);

// Ref https://stackoverflow.com/questions/15900485/correct-way-to-convert-size-in-bytes-to-kb-mb-gb-in-javascript
function formatBytes(bytes,decimals) {
    if(bytes == 0) return '0 Bytes';
    var k = 1024,
        dm = decimals <= 0 ? 0 : decimals || 2,
        sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'],
        i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
 }

function getOutputFormatDesc(outputFormat) {
    switch(outputFormat) {
        case 'pdf': return 'PDF';
        case 'jpeg': return 'JPEG images (a .zip download)';
        case 'pdf_and_jpeg': return 'PDF file + JPEG images (a .zip download)';
        default: return 'Unknown format';
    }
 }

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
            case 'creating_zip':
                break;
            case 'zip_created':
                break;
            case 'download_ready':
                console.log('Showing the download button');
                document.querySelector('#download-form').style.visibility = "visible";
                console.log('msg.download_file_url:',msg.download_file_url)
                document.querySelector('#download-form').action = msg.download_file_url;
                const size = formatBytes(msg.download_file_size, 1);
                const outputFormat = getOutputFormatDesc(msg.output_format);
                document.querySelector('#download-file-desc').textContent = `${outputFormat}, ${size}`
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

function getSelectedRadioButtonValue(radioButtonName) {
    let radioButtons = document.querySelectorAll(`input[name="${radioButtonName}"]`);
    for(btn of radioButtons) {
        if(btn.checked) {
            return btn.value;
        }
    }
    return '';
}

function onFixedSizeClicked() {
    document.querySelector('#custom-width').disabled = true;
    document.querySelector('#custom-height').disabled = true;

    let size = getSelectedRadioButtonValue('paper_size');
    if( size == 'jp-postcard-2-fold'
     || size == 'jp-postcard-3-fold' ) {
         document.querySelector("#rotate-page-90-degrees").checked = true;
         onRotateOptionClicked();
    } else {
         document.querySelector("#rotate-page-90-degrees").checked = false;
         onRotateOptionClicked();
    }
}

function onCustomSizeClicked() {
    document.querySelector('#custom-width').disabled = false;
    document.querySelector('#custom-height').disabled = false;
}

function onRotateOptionClicked() {
    const borderOpacity
    = document.querySelector("#rotate-page-90-degrees").checked ? 0.9 : 0.0;
    console.log('opacity: ',borderOpacity);
    document.querySelector("#rotate-option-container").style.borderColor
    = `rgba(255, 20, 20, ${borderOpacity})`;
}

function updateBrightnessSlider(value) {
    document.querySelector('#brightness-value').innerHTML = value;
}

function resetBrightness() {
    // TODO: define the default brightness for each scanner model
    const defaultBrightness = 25;

    document.querySelector("#brightness-slider").value = defaultBrightness;
    document.querySelector("#brightness-value").innerHTML = defaultBrightness;
}

// Encodes the custom paper size in the form of a comma-separated string
// Example: 'custom,100,200'
function encodeCustomPaperSize() {
    return `custom,
    ${document.querySelector('#custom-width').value.trim()},
    ${document.querySelector('#custom-height').value.trim()}`;
}

function startScan() {
    console.log('Starting the scan');
    const paperSizeValue = getSelectedRadioButtonValue('paper_size');
    const paperSize = (paperSizeValue == 'custom-size') ?
    encodeCustomPaperSize() : paperSizeValue;
    let rotate_options = '';
    if(document.querySelector('#rotate-page-90-degrees').checked) {
        rotate_options += 'rotate_by_90_degrees';
    }
    if(document.querySelector('#rotate-even-numbered-pages-180-degrees').checked) {
        rotate_options += (0 < rotate_options.length ? ',' : '') + 'rotate_even_numbered_page_by_180_degrees';
    }
    let scanParams = {
        paper_size: paperSize,
        sides: getSelectedRadioButtonValue('sides'),
        color: getSelectedRadioButtonValue('color'),
        brightness: document.querySelector('#brightness-slider').value,
        resolution: getSelectedRadioButtonValue('resolution'),
        output_format: getSelectedRadioButtonValue('output_format'),
        page_rotate_options: rotate_options
    };
    (async () => {
        const rawResponse = await fetch('/scan', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(scanParams)
        });
        const content = await rawResponse.json();
        console.log(content);
    })();
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

let coll = document.getElementsByClassName("collapsible");
for(let i = 0; i < coll.length; i++) {
  coll[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.display === "block") {
      content.style.display = "none";
    } else {
      content.style.display = "block";
    }
  });
}

resetBrightness();