    (function() {
  // The width and height of the captured photo. We will set the
  // width to the value defined here, but the height will be
  // calculated based on the aspect ratio of the input stream.

  var csrftoken = $('meta[name=csrf-token]').attr('content');

   $.ajaxSetup({
       beforeSend: function(xhr, settings) {
           if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
               xhr.setRequestHeader("X-CSRFToken", csrftoken);
           }
       }
   });

  var width = 1024;    // We will scale the photo width to this (note that only 160px steps are valid for yolov4-CSP - 640, 480, 320, ...)
  var widthDifference = 512;
  var widthDifferenceHalf = widthDifference/2;
  var scaledHeight;
  var startTime;
  var image;
  var colorConfig = {'0': 'green', '1': 'red', '2': 'orange'};
  var nameConfing = {'0': 'Masked face', '1': 'Unmasked face', '2': 'Incorrect mask'};
  var lineWidth = 4;
  var textPaddingVertical = 4;
  var detectionResult = null;
  var maxAverageWindowSize = 20;
  var speedResults = [];
  var averageSpeed = 0;

  // |streaming| indicates whether or not we're currently streaming
  // video from the camera. Obviously, we start at false.

  var streaming = false;

  // The various HTML elements we need to configure or control. These
  // will be set by the startup() function.

  io.on('update-picture', (socket) => {
    validate(socket);
    console.log(`Execution time: ${Date.now() - startTime} ms`);
    takepicture();
  });

  var video = null;
  var canvas = null;
  var secondCanvas = null;
  var photo = null;
  var startbutton = null;
  let initalized = false;

  function showViewLiveResultButton() {
    if (window.self !== window.top) {
      // Ensure that if our document is in a frame, we get the user
      // to first open it in its own tab or window. Otherwise, it
      // won't be able to request permission for camera access.
      document.querySelector('.contentarea').remove();
      const button = document.createElement('button');
      button.textContent = 'View live result of the example code above';
      document.body.append(button);
      button.addEventListener('click', () => window.open(location.href));
      return true;
    }
    return false;
  }

  function startup() {
    if (showViewLiveResultButton()) { return; }
    video = document.getElementById('video');
    canvas = document.getElementById('canvas');
    secondCanvas = document.getElementById('secondCanvas');
    photo = document.getElementById('photo');
    startbutton = document.getElementById('startbutton');

    navigator.mediaDevices.getUserMedia({video: true, audio: false})
    .then(function(stream) {
      video.srcObject = stream;
      video.play();
    })
    .catch(function(err) {
      console.log('An error occurred: ' + err);
    });

    video.addEventListener('canplay', function(ev){
      if (!streaming) {
        height = video.videoHeight / (video.videoWidth/width);
        scaledHeight = video.videoHeight / (video.videoWidth/(width - widthDifference));

        // Firefox currently has a bug where the height can't be read from
        // the video, so we will make assumptions if this happens.

        if (isNaN(height)) {
          height = width / (4/3);
        }

        if (isNaN(scaledHeight)) {
          scaledHeight = (width - widthDifference) / (4/3);
        }

        $.ajax({method: 'POST', url: 'main/config', contentType: 'application/json',
            data: JSON.stringify({'height': scaledHeight, 'width': width - widthDifference}),
            success: function (response) {
                $('#start-message').hide();
                $('#startbutton').removeClass('hidden');
            },
                failure: function (response) {
                alert("failure");
            }
        });

        video.setAttribute('width', width);
        video.setAttribute('height', height);
        canvas.setAttribute('width', width);
        canvas.setAttribute('height', height);
        streaming = true;
      }
    }, false);

    startbutton.addEventListener('click', function(ev){
      takepicture();
      $('#startbutton').hide();
      ev.preventDefault();
    }, false);
    clearphoto();

    $('#streamNav').on('click', function(){
        if(!$(this).hasClass('active')){
            $(this).toggleClass('active');
            $('#logNav').toggleClass('active');

            $('.contentDiv').toggleClass('hidden');
        }
    });

    $(document).ready(function(){
        $('#logNav').on('click', function(){
            $.ajax({method: 'POST', url: 'main/table', contentType: 'application/json'})
                .done(function(msg){
                    $('.table tbody').empty();
                    var time, fileName, content;
                    for(i = 0; i < Object.keys(msg).length; i++){
                        time = msg[i][0];
                        fileName = msg[i][1];
                        content = $('<tr>');
                        content.append($('<td>').attr('scope', 'row').text(i));
                        content.append($('<td>').text(time));
                        content.append($('<td>').append($('<a>').attr('href', '/main/log/' + fileName).attr('target', '_blank').addClass('link-info').text(fileName)));
                        $('.table tbody').append(content);
                    }
                });
            if(!$(this).hasClass('active')){
                $(this).toggleClass('active');
                $('#streamNav').toggleClass('active');

                $('.contentDiv').toggleClass('hidden');
            }
        });
    });
  }

  // Fill the photo with an indication that none has been
  // captured.

  function clearphoto() {
    var context = canvas.getContext('2d');
    context.fillStyle = '#AAA';
    context.fillRect(0, 0, canvas.width, canvas.height);

    var data = canvas.toDataURL('image/jpeg');
    photo.setAttribute('src', data);
  }

  // Capture a photo by fetching the current contents of the video
  // and drawing it into a canvas, then converting that to a JPG
  // format data URL. By drawing it on an offscreen canvas and then
  // drawing that to the screen, we can change its size and/or apply
  // other changes before drawing it.

  function makeBlob(dataURL){
    var BASE64_MARKER = ';base64,';
    if (dataURL.indexOf(BASE64_MARKER) == -1) {
      var parts = dataURL.split(',');
      var contentType = parts[0].split(':')[1];
      var raw = decodeURIComponent(parts[1]);
      return new Blob([raw], { type: contentType });
    }
      var parts = dataURL.split(BASE64_MARKER);
      var contentType = parts[0].split(':')[1];
      var raw = window.atob(parts[1]);
      var rawLength = raw.length;

      var uInt8Array = new Uint8Array(rawLength);

      for (var i = 0; i < rawLength; ++i) {
        uInt8Array[i] = raw.charCodeAt(i);
      }

      return new Blob([uInt8Array], { type: contentType });
  }

  function validate(response){
    var speed = Date.now() - startTime;
    addNewSpeedResult(speed);
    averageSpeed = countAverageSpeed(speedResults);
    console.log(`Average speed: ${averageSpeed} ms`);
    detectionResult = $.parseJSON(response);
    if($('#result').hasClass('hidden')){
       $('#result').removeClass('hidden');
    }
  }


  function takepicture() {
    var context = canvas.getContext('2d');
    var secondContext = secondCanvas.getContext('2d');
    if (width && height) {
      canvas.width = width;
      canvas.height = height;
      secondCanvas.width = width - widthDifference;
      secondCanvas.height = scaledHeight;

      if($('#canvas-container').hasClass('hidden')){
        $('#canvas-container').removeClass('hidden');
      }

      context.drawImage(video, 0, 0, width, height);
      drawDetectionResult(detectionResult);
      secondContext.drawImage(canvas, 0, 0, width - widthDifference, scaledHeight);

      secondCanvas.toBlob((blob) => {
        startTime = Date.now();
        io.emit('frame', {blob});
      });

    } else {
      clearphoto();
    }
  }

  function drawDetectionResult(detectionDataArray){
    if(detectionDataArray != null && detectionDataArray.length > 0){
        var context = canvas.getContext('2d');
        context.font = '20px Arial';
        detectionDataArray.forEach(detectionData => {
            context.beginPath();
            detectionData = $.parseJSON(detectionData);
            var positionData = detectionData['position'];
            var classIndex = detectionData['class'];
            context.lineWidth = lineWidth;
            context.strokeStyle = colorConfig[classIndex];
            context.fillStyle = colorConfig[classIndex];

            var origWidth = (Number(positionData['width']) / (width - widthDifference)) * width;
            var origHeight = (Number(positionData['height']) / scaledHeight) * height;
            var origX = (Number(positionData['x']) / (width - widthDifference)) * width;
            var origY = (Number(positionData['y']) / scaledHeight) * height;

            context.rect(origX, origY, origWidth, origHeight);

            var name = nameConfing[classIndex] + ': ' + parseFloat(detectionData['confidence']).toFixed(2);
            context.fillText(name, origX, origY - textPaddingVertical);
            context.stroke();
        });
    }
  }

  function scalePositionToOriginalWidth(position){
    return (Number(position) / (width - widthDifference)) * width;
  }

  function scalePositionToOriginalHeight(position){
    return (Number(position) / scaledHeight) * height;
  }

  function countAverageSpeed(){
    return speedResults.reduce((partialSum, speed) => partialSum + speed, 0) / speedResults.length;
  }

  function addNewSpeedResult(speedResult){
    if(speedResults.length > maxAverageWindowSize){
        speedResults.shift();
    }
    speedResults.push(speedResult);
  }

  // Set up our event listener to run the startup process
  // once loading is complete.
  window.addEventListener('load', startup, false);
})();