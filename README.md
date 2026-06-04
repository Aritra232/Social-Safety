# Child Safety Content Moderator

A FastAPI-based content moderation system that checks text, images, and videos for child safety compliance using Google's Gemini AI and backup toxicity detection.

---

## 📌 Features

- **Text Moderation**: Analyzes captions for inappropriate language, tone, and content using Gemini AI
- **Emoji Awareness**: Detects adult-meaning or suggestive emoji patterns that could imply mature content
- **Image Analysis**: Scans images for nudity, sexual content, violence, and unsafe material
- **Video Checking**: Extracts key frames from videos and performs safety analysis on each frame
- **PII Detection**: Identifies and blocks personal information (phone numbers, emails) in captions
- **Quota Management**: Automatically switches between Gemini models with higher free tier limits
- **Retry Logic**: Implements exponential backoff for rate-limited requests
- **Backup System**: Falls back to local toxicity detection when AI service is unavailable
- **Simple Response Format**: Returns only boolean safety status

---

## 🚀 How to Run the Project

### Prerequisites
- Python
- pip (Python package manager)
- Google Gemini API key

### Installation

1. **Clone/Setup Project**
   ```bash
   cd c:\Aritra\aycemax_check_adult
   ```

2. **Create Virtual Environment** (Optional but recommended)
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup Environment Variables**
   Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_google_gemini_api_key_here
   YOUTUBE_API_KEY=your_youtube_data_api_key_here
   ```

   Get your Gemini API key from: https://aistudio.google.com/
   Get your YouTube Data API key from: https://console.developers.google.com/

5. **Run the Server**
   ```bash
   uvicorn app:app --reload
   ```

   The server will start at `http://127.0.0.1:8000`

---

## 📋 API Endpoints

### POST `/check-content`

Submit content (image/video) with caption for moderation.

**Request:**
- `caption` (string, required): Text caption to check
- `image` (file, optional): Image file to check
- `video` (file, optional): Video file to check

**Response:**
```json
{
  "language_and_tone": true,
  "content_appropriateness": true,
  "photos": true,
  "personal_information": true,
  "kindness": true,
  "overall": true
}
```

**Example (using curl):**
```bash
curl -X POST http://127.0.0.1:8000/check-content \
  -F "caption=This is my post" \
  -F "image=@path/to/image.jpg"
```

### GET `/video-suggestions`

Request kid-safe English YouTube videos for a grade and topic. The response returns only video links plus a short topic summary and a 4-question quiz.

**Query parameters:**
- `grade` (integer, required): 3 through 8
- `topic` (string, required): subject/topic name, e.g. `Mathematics`, `Science`, `History`
- `limit` (integer, optional): number of videos to return, default 2, maximum 12

**Response:**
```json
{
  "grade": 3,
  "topic": "Mathematics",
  "count": 12,
  "videos": [
    {
      "url": "https://www.youtube.com/watch?v=...",
      "summary": "Topic: Mathematics. This video explains the main idea in three simple sentences, gives a real-life example, and shows the important parts of the topic.",
      "quiz": [
        {
          "question": "...",
          "options": ["...", "...", "...", "..."],
          "answer": "..."
        }
      ]
    }
  ]
}
```

**Example (using curl):**
```bash
curl "http://127.0.0.1:8000/video-suggestions?grade=3&topic=Mathematics"
```


---


## 🛡️ Safety Features

✅ No reason/explanation strings (only boolean returns)  
✅ Automatic retry with exponential backoff  
✅ Fallback to local toxicity detection  
✅ PII detection for sensitive data  
✅ Video frame sampling for efficient processing  
✅ Quota management across multiple models

---

## 📞 Support

For issues with:
- **API Keys**: Visit https://aistudio.google.com/
- **Rate Limits**: See https://ai.google.dev/gemini-api/docs/rate-limits
- **Gemini Docs**: https://ai.google.dev/

---

## 📄 License

This project is for educational and child safety purposes.
