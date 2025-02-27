document.addEventListener("DOMContentLoaded", function () {
  const recordButton = document.getElementById('record');
  const stopButton = document.getElementById('stop');
  const transcriptionDiv = document.getElementById('transcription');
  const sentimentDiv = document.getElementById('sentiment');
  const recordedFilesList = document.getElementById('recordedFiles');
  const ttsFilesList = document.getElementById('ttsFiles');
  let mediaRecorder;
  let audioChunks = [];

  recordButton.addEventListener('click', () => {
      navigator.mediaDevices.getUserMedia({ audio: true })
          .then(stream => {
              mediaRecorder = new MediaRecorder(stream);
              mediaRecorder.start();
              audioChunks = [];

              mediaRecorder.ondataavailable = event => {
                  audioChunks.push(event.data);
              };

              mediaRecorder.onstop = () => {
                  const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                  const formData = new FormData();
                  formData.append('audio_data', audioBlob, 'recorded_audio.wav');

                  fetch('/upload', {
                      method: 'POST',
                      body: formData
                  })
                  .then(response => response.json())
                  .then(data => {
                      if (data.transcript) {
                          transcriptionDiv.innerHTML = `<strong>Transcription:</strong> ${data.transcript}`;
                          sentimentDiv.innerHTML = `<strong>Sentiment:</strong> ${data.sentiment_label} (Score: ${data.sentiment_score}, Magnitude: ${data.sentiment_magnitude})`;
                      }

                      if (data.audio_url) {
                          const listItem = document.createElement('li');
                          listItem.innerHTML = `
                              <audio controls>
                                  <source src="${data.audio_url}" type="audio/wav">
                                  Your browser does not support the audio element.
                              </audio><br>
                              <a href="${data.audio_url}">Download ${data.audio_url.split('/').pop()}</a>
                          `;
                          recordedFilesList.appendChild(listItem);
                      }
                  })
                  .catch(error => {
                      console.error("Error uploading audio:", error);
                  });
              };
          })
          .catch(error => {
              console.error("Microphone access denied:", error);
          });

      recordButton.disabled = true;
      stopButton.disabled = false;
  });

  stopButton.addEventListener('click', () => {
      if (mediaRecorder) {
          mediaRecorder.stop();
      }
      recordButton.disabled = false;
      stopButton.disabled = true;
  });

  const textInput = document.getElementById('textInput');
  const textSubmit = document.getElementById('textSubmit');
  const ttsAudio = document.createElement("audio");
  document.body.appendChild(ttsAudio);

  textSubmit.addEventListener('click', () => {
      fetch('/upload_text', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({ text: textInput.value })
      })
      .then(response => response.json())
      .then(data => {
          if (data.tts_url) {
              ttsAudio.src = data.tts_url;
              ttsAudio.controls = true;
              ttsAudio.play();

              const listItem = document.createElement('li');
              listItem.innerHTML = `
                  <audio controls>
                      <source src="${data.tts_url}" type="audio/wav">
                      Your browser does not support the audio element.
                  </audio><br>
                  <a href="${data.tts_url}">Download ${data.tts_url.split('/').pop()}</a>
              `;
              ttsFilesList.appendChild(listItem);
          } else {
              alert("Failed to generate TTS audio.");
          }
      })
      .catch(error => {
          console.error("Error generating speech:", error);
          alert("Failed to generate speech.");
      });
  });
});


