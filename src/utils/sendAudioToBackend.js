export async function sendAudioToBackend(audioBlob) {
  const formData = new FormData()
  formData.append("file", audioBlob, "audio.webm")

  console.log("🔊 Sending audio blob:", audioBlob)

  try {
    const response = await fetch("https://halo-whisper-backend.onrender.com/transcribe", {
      method: "POST",
      body: formData,
    })

    const data = await response.json()
    console.log("📝 Transcription result:", data)

    return data.text
  } catch (error) {
    console.error("❌ Transcription error:", error)
    return null
  }
}
