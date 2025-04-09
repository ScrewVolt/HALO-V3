export async function sendAudioToBackend(audioBlob) {
  const formData = new FormData();
  formData.append("file", audioBlob, "audio.webm");

  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/transcribe`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    console.log("📝 Transcription result:", data);
    return data.text;
  } catch (error) {
    console.error("❌ Transcription error:", error);
    return null;
  }
}
