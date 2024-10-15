$(document).ready(function () {
    loadUserData();

    $('#save-api-key-btn').click(function (e) {
        e.preventDefault();

        testOpenAIKey().then(result => console.log(result));

        saveUserData();
    });

    $('#novel-gen-tab').click(function (e) {
        e.preventDefault();
        $('#novel-gen').show();
        $('#api-key').hide();
        $(this).addClass('active');
    });

    $('#api-key-btn').click(function (e) {
        e.preventDefault();
        $('#novel-gen').hide();
        $('#api-key').show();
        $('#novel-gen-tab').removeClass('active');
    });

    $('#novel-gen').hide();
    $('#api-key').show();

    $('#addInputBtn').click(function () {
        addInputField();
        updateLevels();
    });

    $('#novel-gen-form').on('submit', function (e) {
        e.preventDefault();

        // Clear previous error messages
        $('.error').text('');

        // Validation
        let isValid = true;

        if ($('#novel-gen-title').val().trim() === '') {
            $('#novel-gen-title-Error').text('Please enter a title.');
            isValid = false;
        }

        if (!isValid) {
            return; // Stop the function if validation fails
        }

        prefix = 'novel-gen'

        // Show the loading bar
        $('#' + prefix + '-loading-bar-container').show();
        $('#' + prefix + '-loading-bar').css('width', '0%');
        $('#' + prefix + '-loading-percent').text('0%'); // Reset the text

        let formData = gatherFormData();
        formData['title'] = $('#novel-gen-title').val().trim();
        formData["api_key"] = $("#api-key-input").val();

        $.ajax({
            type: "POST",
            url: "/novel-gen",
            contentType: "application/json",
            data: JSON.stringify(formData),
            xhr: function () {
                var xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener("progress", function (evt) {
                    if (evt.lengthComputable) {
                        var percentComplete = evt.loaded / evt.total;
                        // Update loading bar width
                        $('#' + prefix + '-loading-bar').css('width', percentComplete * 100 + '%');
                    }
                }, false);
                return xhr;
            },
            success: function (response) {
                console.log("Data submitted successfully:", response);
            },
            error: function (xhr, status, error) {
                console.error("Error in data submission:", xhr.responseText);
            },
            complete: function () {
                // Hide the loading bar when the request is complete
                updateLoadingBar(formData.title, prefix);
            }
        });
    });

    // Event listener for when the selection changes
    $('#novel-gen-prompt-type').change(function() {
        // Get the selected value
        var selectedOption = $(this).val();
        
        // Hide both tabs initially
        $('#novel-gen-outline-tab').hide();
        $('#novel-gen-summary-tab').hide();

        // Show the relevant tab based on the selected option
        if (selectedOption === 'Outline') {
            $('#novel-gen-outline-tab').show();
        } else if (selectedOption === 'Summary') {
            $('#novel-gen-summary-tab').show();
        }
    });

    // Trigger the change event on page load to ensure the correct tab is shown
    $('#novel-gen-prompt-type').trigger('change');
});

function addInputField() {
    let newInput = createDepthControlInput();
    $('#inputContainer').append(newInput);
}

function createDepthControlInput() {
    let inputGroup = $('<div>', {
        'class': 'input-group mb-2',
        'data-depth': '1',
        css: { 'padding-left': '20px' }
    });

    let levelIndicator = $('<div>', {
        'class': 'level-indicator',
        css: { 'margin-right': '10px' }
    });

    let indentBtn = $('<button>', {
        type: 'button',
        'class': 'btn btn-outline-secondary',
        text: '>',
        click: function () {
            adjustDepth(inputGroup, true);
        }
    });

    let outdentBtn = $('<button>', {
        type: 'button',
        'class': 'btn btn-outline-secondary',
        text: '<',
        click: function () {
            adjustDepth(inputGroup, false);
        }
    });

    let deleteBtn = $('<button>', {
        type: 'button',
        'class': 'btn btn-outline-danger',
        text: 'X',
        click: function () { deleteInputField(inputGroup); } // Corrected event handler
    });

    let input = $('<input>', {
        type: 'text',
        'class': 'form-control',
        placeholder: 'Enter detail'
    });

    inputGroup.append(levelIndicator, outdentBtn, indentBtn, input, deleteBtn);

    return inputGroup;
}

function adjustDepth(element, isIndent) {
    let currentDepth = parseInt(element.attr('data-depth'));
    currentDepth += isIndent ? 1 : -1;
    currentDepth = Math.max(1, currentDepth); // Ensure depth is not negative
    element.attr('data-depth', currentDepth.toString());

    // Adjust padding based on depth
    let padding = (20 * currentDepth);
    element.css('padding-left', `${padding}px`);

    updateLevels();
}

function updateLevels() {
    let levelNumbers = [0]; // Initialize level numbers

    $('#inputContainer').children('.input-group').each(function () {
        let depth = parseInt($(this).attr('data-depth'));

        while (levelNumbers.length - 1 > depth) {
            levelNumbers.pop(); // Remove deeper levels
        }
        if (levelNumbers.length - 1 < depth) {
            levelNumbers.push(1); // Start a new sub-level
        } else {
            levelNumbers[depth]++; // Increment the current level
        }

        let levelString = levelNumbers.slice(1).join('.');
        $(this).find('.level-indicator').text(levelString);
    });
}

function deleteInputField(element) {
    element.remove();
    updateLevels();
}

function gatherFormData() {
    let selectedPromptType = $('#novel-gen-prompt-type').val();
    let formData = {};

    if (selectedPromptType === 'Outline') {
        let inputData = [];
        $('#inputContainer').find('.input-group').each(function () {
            let level = $(this).find('.level-indicator').text();
            let value = $(this).find('input[type="text"]').val();
            inputData.push({ value: value, level: level });
        });
        formData['outline'] = inputData;
    } else if (selectedPromptType === 'Summary') {
        formData['summary'] = $('#summaryTextarea').val().trim();
        formData['version'] = $('#novel-gen-version').val().trim();
    }

    return formData;
}

function setLocalStorageItem(value) {
    localStorage.setItem('key54-32579032', value);
}

function getLocalStorageItem() {
    return localStorage.getItem('key54-32579032');
}

function saveUserData() {
    var userInput = $("#api-key-input").val();
    setLocalStorageItem(userInput);
}

function loadUserData() {
    var userData = getLocalStorageItem();

    if (userData) {
        $("#api-key-input").val(userData);
    }
}

async function testOpenAIKey() {
    var apiKey = $("#api-key-input").val();

    const url = 'https://api.openai.com/v1/chat/completions'; // Example endpoint

    const headers = {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
    };

    const body = JSON.stringify({
        model: "gpt-4o-mini",
        messages: [
            {
                role: "system",
                content: "You are a helpful assistant."
            },
            {
                role: "user",
                content: "Hello!"
            }
        ]
    });

    try {
        const response = await fetch(url, { method: 'POST', headers: headers, body: body });
        const data = await response.json();

        if (response.ok) {
            return { valid: true, message: 'API key is valid.', data: data };
        } else {
            return { valid: false, message: 'API key is not valid.', error: data };
        }
    } catch (error) {
        return { valid: false, message: 'Failed to test API key.', error: error };
    }
}

// Function to periodically fetch progress and update the loading bar
function updateLoadingBar(title, prefix) {
    $.get('/progress', function (data) {
        if (data.fail) {
            $('#' + prefix + '-loading-bar-container').hide();
            $('#novel-gen-error').text('Error occurred on the server. Unable to create novel.' + data.fail_message);
            return -1
        }
        if (data.current && data.total) {
            var progress = (data.current / data.total) * 100;
            $('#' + prefix + '-loading-bar').css('width', progress + '%');
            $('#' + prefix + '-loading-percent').text(Math.round(progress) + '%'); // Update the text
        }

        if (data.complete) {
            deliverPDF(data.text, title);
            $('#' + prefix + '-loading-bar-container').hide();
        }
        else {
            setTimeout(() => updateLoadingBar(title, prefix), 1000); // Update every second
        }
    });
}

// JavaScript Part
function deliverPDF(text, title) {
    // Prepare the data to be sent in the request
    const data = JSON.stringify({text: text, title: title});

    // Use the fetch API to send the POST request
    fetch('/create-pdf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: data
    })
    .then(response => {
        // Check if the response is ok (status in the range 200-299)
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        // Retrieve the filename from the Content-Disposition header
        // This is optional, but useful if you want to use the original filename
        const filename = response.headers.get('Content-Disposition').split('filename=')[1].replaceAll('"', '');
        return response.blob().then(blob => ({blob, filename}));
    })
    .then(({ blob, filename }) => {
        // Create a URL for the blob object
        const url = window.URL.createObjectURL(blob);
        // Create an anchor (<a>) element with the URL as the href
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || 'download.pdf'; // Use the filename from the header or a default
        document.body.appendChild(a); // Append the anchor to the body
        a.click(); // Simulate a click on the anchor to trigger the download
        window.URL.revokeObjectURL(url); // Clean up by revoking the blob URL
        a.remove(); // Remove the anchor from the body
    })
    .catch(error => {
        console.error('Error creating PDF:', error);
        // Handle any errors that occurred during the fetch
    });
}