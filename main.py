import os
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from moviepy.editor import TextClip, CompositeVideoClip, ColorClip, AudioFileClip
from elevenlabs import generate, save

# 1. Get today's verse from Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Red Letter Verses").sheet1

# Find next unposted verse
for row in range(2, 367):  # rows 2–366
    if sheet.cell(row, 3).value == "":  # column C empty = not posted
        verse = sheet.cell(row, 1).value
        reference = sheet.cell(row, 2).value
        sheet.update(f"C{row}", "POSTED " + os.popen("date").read().strip())
        break

# 2. Generate voiceover
audio = generate(
    text=f"{verse}. {reference}",
    voice="Matthew",  # or "Rachel"
    api_key=os.getenv("ELEVENLABS_API_KEY")
)
save(audio, "voice.mp3")

# 3. Create video (red text on parchment)
background = ColorClip(size=(1080,1920), color=(30,20,10)).set_duration(20)  # dark parchment
# Or use a real image: ImageClip("background.jpg")

verse_clip = TextClip(verse, fontsize=80, color="#BE1E2D", font="Cinzel", 
                      size=(900, None), method='caption', align='center')
verse_clip = verse_clip.set_position('center').set_duration(20)

ref_clip = TextClip(f"— {reference}", fontsize=70, color="#D4AF37", font="Playfair-Display")
ref_clip = ref_clip.set_position(('center','bottom')).set_duration(20).margin(bottom=100)

video = CompositeVideoClip([background, verse_clip, ref_clip])
video = video.set_audio(AudioFileClip("voice.mp3"))
video.write_videofile("short.mp4", fps=24)
# === AUTO UPLOAD SECTION (uncomment when ready) ===

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import tiktoken  # pip install tiktoken python-telegram-bot etc. if needed

# YouTube upload
youtube = build('youtube', 'v3', developerKey=os.getenv("YOUTUBE_API_KEY"))  # or use OAuth
request_body = {
    'snippet': {
        'title': f"{reference} – Red Letter Words of Jesus",
        'description': f'"{verse}"\n\nDaily red-letter devotionals from The Red Letter Christian 📖🔴\n#RedLetterChristian #JesusWords',
        'tags': ['Jesus', 'Bible', 'Red Letter', 'Christian', 'Devotional'],
        'categoryId': '22'  # People & Blogs
    },
    'status': {'privacyStatus': 'public'}
}
media = MediaFileUpload("short.mp4", resumable=True)
response = youtube.videos().insert(part='snippet,status', body=request_body, media_body=media).execute()
print("Uploaded to YouTube:", response['id'])

# TikTok & Instagram via manual or third-party (or use Buffer/Publer API here)
print("Short ready — upload short.mp4 manually to TikTok/Instagram or connect Buffer")

print("Daily Red Letter Short created! short.mp4 is ready.")
