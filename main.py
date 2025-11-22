import os
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, AudioFileClip

from elevenlabs import generate, save

# ================== CONFIG ==================
BACKGROUND_FOLDER = "backgrounds"   # folder with your 10 parchment images
# ===========================================

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

# 2. Generate calm voiceover
audio = generate(
    text=f"{verse}. {reference}",
    voice="Matthew",            # change to "Rachel" if you prefer female
    api_key=os.getenv("ELEVENLABS_API_KEY")
)
save(audio, "voice.mp3")

# 3. Pick random background from backgrounds/ folder
bg_files = [f for f in os.listdir(BACKGROUND_FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
bg_path = os.path.join(BACKGROUND_FOLDER, random.choice(bg_files))

background = ImageClip(bg_path).set_duration(20).resize(height=1920).margin(top=0, bottom=0, left=0, right=0, color=(0,0,0))

# 4. Create red-letter text clips
verse_clip = TextClip(
    verse,
    fontsize=80,
    color="#BE1E2D",                    # classic Bible red
    font="Cinzel-Regular",              # download free if needed, or use "Times-New-Roman"
    size=(900, None),
    method='caption',
    align='center'
).set_position('center').set_duration(20)

ref_clip = TextClip(
    f"— {reference}",
    fontsize=70,
    color="#D4AF37",                    # gold
    font="Playfair-Display-Regular"
).set_position(('center', 'bottom')).set_duration(20).margin(bottom=120, opacity=0)

# 5. Combine everything
video = CompositeVideoClip([background, verse_clip, ref_clip])
video = video.set_audio(AudioFileClip("voice.mp3"))
video.write_videofile("short.mp4", fps=30, codec="libx264", audio_codec="aac")

print("Daily Red Letter Short created → short.mp4")
