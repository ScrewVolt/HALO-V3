export async function sendAudioToBackend(audioUrl) {
  console.log("📤 Sending audio URL to Whisper:", audioUrl);
  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/transcribe`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        audio_url: audioUrl,  // 👈 Make sure this key matches the backend
      }),
    });

    const data = await response.json();
    console.log("📝 Transcription result:", data);
    return data.text;
  } catch (error) {
    console.error("❌ Transcription error:", error);
    return null;
  }
}
