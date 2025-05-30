// static/script.js

document.addEventListener('DOMContentLoaded', () => {
  const elements = initializeElements();
  let mediaRecorder = null;
  let audioChunks = [];

  setupEventListeners();

  function initializeElements() {
    return {
      recordButton: document.getElementById('recordButton'),
      stopButton: document.getElementById('stopButton'),
      recordingSpinner: document.getElementById('recordingSpinner'),
      playbackAudio: document.getElementById('playbackAudio'),
      responseSpinner: document.getElementById('responseSpinner'),
      responseSection: document.getElementById('responseSection'),
      responseAudio: document.getElementById('responseAudio'),
      downloadAudioLink: document.getElementById('downloadAudioLink'),
    };
  }

  function setupEventListeners() {
    elements.recordButton.addEventListener('click', startRecording);
    elements.stopButton.addEventListener('click', stopRecording);
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      initializeMediaRecorder(stream);
      mediaRecorder.start();

      toggleRecordingState(true);
      console.log('Recording started.');
    } catch (error) {
      handleError('Could not access microphone. Please ensure your browser has microphone permissions.', error);
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
      console.log('Recording stopped.');
    }
  }

  function initializeMediaRecorder(stream) {
    mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm; codecs=opus' });
    audioChunks = [];

    mediaRecorder.ondataavailable = collectAudioData;
    mediaRecorder.onstart = () => {
      toggleRecordingState(true);
      hideResponseSection();
    };
    mediaRecorder.onstop = processAudioCapture;
  }

  function collectAudioData(event) {
    if (event.data.size > 0) audioChunks.push(event.data);
  }

  function processAudioCapture() {
    toggleRecordingState(false);
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm; codecs=opus' });
    const audioUrl = URL.createObjectURL(audioBlob);

    elements.playbackAudio.src = audioUrl;
    elements.playbackAudio.load();

    displayProcessingSpinner(true);
    sendAudioToServer(audioBlob).finally(() => displayProcessingSpinner(false));
  }

  async function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');

    try {
      const response = await fetch('/api/record-transcribe', { method: 'POST', body: formData });
      await processServerResponse(response);
    } catch (error) {
      handleError('An error occurred during processing. Please try again.', error);
    }
  }

  async function processServerResponse(response) {
    const data = await response.json();
    if (response.ok) {
      updateResponseUI(data);
      console.log('Received response:', data);
    } else {
      handleError(`Error from backend: ${data.error}`);
    }
  }

  function updateResponseUI(data) {
    const { audioUrl } = data;

    // Append a timestamp to the audio URL to prevent caching
    const cacheBuster = `?t=${new Date().getTime()}`;
    const finalAudioUrl = `${audioUrl}${cacheBuster}`;

    elements.responseAudio.src = finalAudioUrl;
    elements.responseAudio.load();
    elements.downloadAudioLink.href = finalAudioUrl;
    elements.downloadAudioLink.download = 'response_audio.mp3';

    elements.responseSection.classList.remove('hidden');
    elements.responseAudio.play().catch(err => console.error('Error playing audio:', err));
  }

  function toggleRecordingState(isRecording) {
    elements.recordButton.disabled = isRecording;
    elements.stopButton.disabled = !isRecording;
    elements.recordingSpinner.classList.toggle('hidden', !isRecording);
    if (!isRecording) elements.responseSection.classList.add('hidden');
  }

  function displayProcessingSpinner(isVisible) {
    elements.responseSpinner.classList.toggle('hidden', !isVisible);
    elements.responseSection.classList.toggle('hidden', isVisible);
  }

  function hideResponseSection() {
    elements.responseSection.classList.add('hidden');
  }

  function handleError(message, error = null) {
    console.error(message, error);
    alert(message);
  }
});
