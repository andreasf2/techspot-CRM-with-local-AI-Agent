import speech_recognition as sr

def listen_greek():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Μπορείς να μιλήσεις...")
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio, language="el-GR")
        print("Είπες:", text)
        return text
    except:
        return ""
