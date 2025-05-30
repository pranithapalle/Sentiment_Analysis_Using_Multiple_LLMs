# Sentiment_Analysis_Using_Multi_Model_LLMs

The project focuses on building an advanced audio analysis application utilizing Google Cloud's 
multimodal Large Language Model (LLM) API. This updated implementation replaces previously used 
discrete APIs (e.g., transcription and sentiment analysis) with a unified LLM API call, simplifying the 
workflow and improving integration efficiency. 

The application's core functionality revolves around the following features: 


1. Audio Recording and Upload: Users can easily record their voice using a simple web interface. 
Once the recording is complete, the user uploads the audio file to the system for processing. This 
step is crucial for getting the audio input into the system, where it will be analyzed and 
transformed into usable data.

2. Single API Call for Multimodal Analysis: After the audio is uploaded, it is sent to Google 
Cloud's Large Language Model (LLM) API in one go. This API does two things at once: it 
transcribes the audio into text (converting speech into written words) and performs a sentiment 
analysis to determine the emotional tone behind the speech. The power of using a single API call 
lies in its efficiency, simplifying the process and reducing the need for multiple systems to handle 
different tasks.

3. Audio Feedback: Once the audio has been transcribed and analyzed for sentiment, the system 
takes the results and converts them into speech. This is done using Google Cloud's Text-to
Speech (TTS) API. The synthesized audio response is then played back to the user, providing an 
interactive way to review the analysis results without needing to read text on a screen.
 
4. Downloadable Audio File: The results from the transcription and sentiment analysis are then 
converted into an audio file. Users can download this audio file, which contains the spoken 
feedback based on the analysis. This allows users to keep a copy of the audio response for future 
reference or share it as needed.
