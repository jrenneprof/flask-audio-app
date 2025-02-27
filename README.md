# flask-audio-app
COT 5930-009: Conversational AI Project 2

Flask Audio App with Sentiment Analysis

This application enhances the original Flask Audio App by integrating Google Cloud Natural Language API for sentiment analysis. Users can record and upload audio, which is transcribed into text using Google Speech-to-Text API. Additionally, users can input text to generate speech via Google Text-to-Speech API.

In this updated version, the transcribed text undergoes sentiment analysis to determine whether the content is positive, negative, or neutral. The results are saved alongside the corresponding audio and text files for traceability and displayed within the app for real-time feedback. The app is deployed on Google Cloud Run, ensuring scalability and accessibility.
