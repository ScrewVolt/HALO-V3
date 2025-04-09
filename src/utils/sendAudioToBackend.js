export async function sendAudioToBackend(audioUrl) {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/transcribe`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ audio_url: audioUrl }),
    });

    const data = await response.json();
    console.log("📝 Transcription result:", data);
    return data.text;
  } catch (error) {
    console.error("❌ Transcription error:", error);
    return null;
  }
}
